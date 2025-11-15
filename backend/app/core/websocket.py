# app/core/websocket.py
from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from app.core.config import get_settings
from app.core.config.time_tuning import QUEUE_LIMITS, TIMEOUTS
from app.core.logging import get_logger


logger = get_logger("ziggy.websocket")
settings = get_settings()


def _now() -> float:
    return time.time()


def _is_prod_trading_enabled() -> bool:
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or "development").strip().lower()
    trading = (os.getenv("TRADING_ENABLED") or "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return env == "production" and trading


class ConnectionManager:
    """
    Manage WebSocket connections and resilient broadcasting.

    - Per-channel asyncio.Queue(maxsize=100) with dedicated consumer tasks
    - Per-channel asyncio.Lock for mutation of connection sets
    - Snapshot iteration over connection sets to avoid "set changed size during iteration"
    - Heartbeats every 25s; send ping with 2.5s timeout; prune on failures
    - Send operations wrapped with asyncio.wait_for(..., timeout=2.5)
    - Basic metrics counters (by channel): attempts, failures, pruned, queue_len, dropped, latency_ms
    """

    def __init__(self):
        # Active connections per channel
        self.connections: dict[str, set[WebSocket]] = {}
        # Metadata per websocket
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}
        # Per-channel lock for connection set mutations
        self._locks: dict[str, asyncio.Lock] = {}
        # Per-channel broadcast queues and consumer tasks
        self._queues: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._consumers: dict[str, asyncio.Task] = {}
        # Heartbeat task
        self._heartbeat_task: asyncio.Task | None = None
        # Background tasks to keep references
        self._bg_tasks: set[asyncio.Task] = set()
        # Metrics storage
        self._metrics: dict[str, dict[str, float]] = {}

    # ------------- internal helpers -------------
    def _get_lock(self, channel: str) -> asyncio.Lock:
        lk = self._locks.get(channel)
        if lk is None:
            lk = asyncio.Lock()
            self._locks[channel] = lk
        return lk

    def _get_queue(self, channel: str) -> asyncio.Queue[dict[str, Any]]:
        q = self._queues.get(channel)
        if q is None:
            maxsize = QUEUE_LIMITS["websocket_default"]
            q = asyncio.Queue(maxsize=maxsize)
            self._queues[channel] = q
            # Start consumer for this channel
            self._consumers[channel] = asyncio.create_task(
                self._consume_channel(channel)
            )
        return q

    def _bump_metric(self, channel: str, key: str, delta: float = 1.0):
        ch = self._metrics.setdefault(channel, {})
        ch[key] = ch.get(key, 0.0) + delta

    def _set_metric(self, channel: str, key: str, value: float):
        ch = self._metrics.setdefault(channel, {})
        ch[key] = value

    # Expose a safe public metric setter for producers
    def set_metric(self, channel: str, key: str, value: float) -> None:
        """Set a numeric metric for a channel (used by producers to report queue sizes, etc.)."""
        self._set_metric(channel, key, value)

    def get_queue_utilization(self, channel: str) -> tuple[int, int, float]:
        """Return (size, capacity, ratio) for the channel's broadcast queue.

        Safe to call from producers to implement upstream backpressure.
        """
        q = self._get_queue(channel)
        size = q.qsize()
        cap = q.maxsize or 0
        ratio: float = (size / cap) if cap else 0.0
        return size, cap, ratio

    # ------------- public API -------------
    async def connect(
        self,
        websocket: WebSocket,
        connection_type: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Accept a new WebSocket connection and register under channel."""
        await websocket.accept()

        # Ensure structures exist
        lock = self._get_lock(connection_type)
        self._get_queue(connection_type)  # ensure consumer started

        async with lock:
            conns = self.connections.setdefault(connection_type, set())
            conns.add(websocket)
            self.connection_metadata[websocket] = {
                "type": connection_type,
                "connected_at": datetime.utcnow(),
                "metadata": metadata or {},
                "id": id(websocket),
                "last_seen": _now(),
            }

        logger.info(
            "WebSocket connected",
            extra={
                "connection_type": connection_type,
                "total_connections": len(self.connections.get(connection_type, set())),
            },
        )

        # Start heartbeat task lazily
        if not self._heartbeat_task or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """Gracefully stop heartbeat and per-channel consumers.

        Safe to call multiple times; cancels and awaits tasks best-effort.
        """
        # Cancel heartbeat
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        # Cancel consumer tasks
        for _ch, task in list(self._consumers.items()):
            if task and not task.done():
                task.cancel()
        # Await their completion
        for _ch, task in list(self._consumers.items()):
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
        # No need to clear queues; they'll be GC'd with manager lifecycle

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection (idempotent)."""
        info = self.connection_metadata.pop(websocket, None)
        if info:
            ch = info.get("type", "")
            lock = self._get_lock(ch)

            async def _do():
                async with lock:
                    conns = self.connections.get(ch)
                    if conns is not None:
                        conns.discard(websocket)
                        if not conns:
                            # Keep queue/consumer to avoid churn; they are cheap
                            self.connections.pop(ch, None)

            # fire-and-forget but keep reference to avoid GC
            task = asyncio.create_task(_do())
            self._bg_tasks.add(task)
            task.add_done_callback(self._bg_tasks.discard)

            try:
                duration = (
                    datetime.utcnow() - info.get("connected_at", datetime.utcnow())
                ).total_seconds()
            except Exception:
                duration = 0.0
            logger.info(
                "WebSocket disconnected",
                extra={"connection_type": ch, "duration_seconds": duration},
            )

    async def _send_json_safe(
        self, ws: WebSocket, payload: dict[str, Any], timeout: float | None = None
    ):
        """Send JSON with timeout; raises on failure."""
        if timeout is None:
            timeout = TIMEOUTS["websocket_send"]
        await asyncio.wait_for(ws.send_json(payload), timeout=timeout)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection with timeout and pruning on failure."""
        try:
            await asyncio.wait_for(
                websocket.send_text(message), timeout=TIMEOUTS["websocket_send"]
            )
        except Exception as e:
            logger.warning(
                "Failed to send personal message",
                extra={"error": repr(e), "ws_id": id(websocket)},
            )
            self.disconnect(websocket)

    async def send_json_personal(self, data: dict[str, Any], websocket: WebSocket):
        """Send JSON to specific connection with timeout and pruning on failure."""
        try:
            await self._send_json_safe(websocket, data)
        except Exception as e:
            logger.warning(
                "Failed to send JSON personal message",
                extra={"error": repr(e), "ws_id": id(websocket)},
            )
            self.disconnect(websocket)

    async def _enqueue_broadcast(self, channel: str, message: dict[str, Any]):
        q = self._get_queue(channel)
        # Approximate queue length metric
        self._set_metric(channel, "queue_len", float(q.qsize()))
        timeout_ms = int(getattr(settings, "WS_ENQUEUE_TIMEOUT_MS", 50) or 50)
        timeout_s = max(0.0, timeout_ms / 1000.0)
        try:
            await asyncio.wait_for(q.put(message), timeout=timeout_s)
        except (TimeoutError, asyncio.QueueFull):
            # Drop policy: drop newest (this) and record
            self._bump_metric(channel, "queue_dropped", 1.0)
            dropped = self._metrics.get(channel, {}).get("queue_dropped", 0.0)
            if dropped and int(dropped) % 100 == 0:
                logger.warning(
                    "Broadcast queue drops",
                    extra={"channel": channel, "dropped_total": int(dropped)},
                )

    async def broadcast_to_type(self, message: dict[str, Any], connection_type: str):
        """Enqueue message for broadcast to a channel; non-blocking."""
        await self._enqueue_broadcast(connection_type, message)

    async def _consume_channel(self, channel: str):
        """Dedicated consumer loop per channel that drains the queue and broadcasts safely."""
        lock = self._get_lock(channel)
        while True:
            try:
                payload = await self._queues[channel].get()
                t0 = _now()
                conns = list(self.connections.get(channel, set()))  # snapshot
                before = len(conns)
                # update a metric for current subscribers
                self._set_metric(channel, "subscribers", float(before))
                self._bump_metric(channel, "broadcasts_attempted", 1.0)

                # Send concurrently with timeouts
                tasks = [self._send_json_safe(ws, payload) for ws in conns]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Prune failed
                failed: list[WebSocket] = []
                for ws, res in zip(conns, results, strict=True):
                    if isinstance(res, Exception):
                        failed.append(ws)

                if failed:
                    self._bump_metric(channel, "broadcasts_failed", float(len(failed)))
                    async with lock:
                        for ws in failed:
                            try:
                                self.connections.get(channel, set()).discard(ws)
                                self.connection_metadata.pop(ws, None)
                            except Exception:
                                pass
                    after = len(self.connections.get(channel, set()))
                    logger.warning(
                        "Broadcast send failures",
                        extra={
                            "channel": channel,
                            "failed": len(failed),
                            "count_before": before,
                            "count_after": after,
                            "ws_ids": [id(x) for x in failed],
                        },
                    )

                # latency metric
                latency_ms = (_now() - t0) * 1000.0
                self._set_metric(channel, "broadcast_latency_ms", latency_ms)

                # Mark task done and update queue metric
                self._queues[channel].task_done()
                self._set_metric(
                    channel, "queue_len", float(self._queues[channel].qsize())
                )

            except asyncio.CancelledError:
                logger.info("Broadcast consumer cancelled", extra={"channel": channel})
                break
            except Exception as e:
                logger.error(
                    "Broadcast consumer error",
                    extra={"channel": channel, "error": repr(e)},
                )
                await asyncio.sleep(0.25)

    async def _heartbeat_loop(self):
        """Send heartbeat pings every 25s and prune sockets on errors/timeouts."""
        interval = 25.0
        while True:
            try:
                await asyncio.sleep(interval)
                # Iterate all channels and their sockets (snapshots)
                for channel, conns in list(self.connections.items()):
                    snapshot = list(conns)
                    if not snapshot:
                        continue
                    before = len(snapshot)
                    tasks = []
                    ping_payload = {"type": "ping", "ts": _now()}
                    for ws in snapshot:
                        tasks.append(self._send_json_safe(ws, ping_payload))

                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    failed = [
                        ws
                        for ws, res in zip(snapshot, results, strict=True)
                        if isinstance(res, Exception)
                    ]
                    if failed:
                        async with self._get_lock(channel):
                            for ws in failed:
                                conns.discard(ws)
                                self.connection_metadata.pop(ws, None)
                        after = len(self.connections.get(channel, set()))
                        logger.warning(
                            "Heartbeat pruned sockets",
                            extra={
                                "channel": channel,
                                "failed": len(failed),
                                "count_before": before,
                                "count_after": after,
                                "ws_ids": [id(x) for x in failed],
                            },
                        )
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error("Heartbeat loop error", extra={"error": repr(e)})
                # Don't spin if persistent error
                await asyncio.sleep(1.0)

    # ---------- Convenience broadcast helpers (unchanged public API) ----------
    async def broadcast_market_data(self, symbol: str, data: dict[str, Any]):
        """Broadcast market data to relevant connections."""
        message = {
            "type": "market_data",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow().timestamp(),
        }
        await self.broadcast_to_type(message, "market_data")
        await self.broadcast_to_type(message, f"market_data:{symbol}")
        # Update alert monitor (best-effort)
        try:
            from app.services.alert_monitoring import alert_monitor

            alert_monitor.update_market_data(symbol, data)
        except Exception as e:
            # In production with trading enabled elevate, else debug
            if _is_prod_trading_enabled():
                logger.warning(
                    "Alert monitor update failed",
                    extra={"symbol": symbol, "error": repr(e)},
                )
            else:
                logger.debug(
                    "Alert monitor update failed",
                    extra={"symbol": symbol, "error": repr(e)},
                )

    async def broadcast_trading_signal(self, signal: dict[str, Any]):
        """Broadcast trading signal to subscribers."""
        message = {
            "type": "trading_signal",
            "signal": signal,
            "timestamp": datetime.utcnow().timestamp(),
        }
        await self.broadcast_to_type(message, "trading_signals")

    async def broadcast_news(self, news_item: dict[str, Any]):
        """Broadcast news to subscribers."""
        message = {
            "type": "news",
            "news": news_item,
            "timestamp": datetime.utcnow().timestamp(),
        }
        await self.broadcast_to_type(message, "news_feed")

    def get_connection_stats(self) -> dict[str, Any]:
        """Return current connection and queue stats per channel."""
        stats: dict[str, Any] = {
            "total_connections": sum(len(c) for c in self.connections.values()),
            "per_channel": {},
        }
        now = datetime.utcnow()
        for ch, conns in self.connections.items():
            q = self._queues.get(ch)
            stats["per_channel"][ch] = {
                "connections": len(conns),
                "queue_len": int(q.qsize()) if q else 0,
                **self._metrics.get(ch, {}),
            }

        # basic uptime aggregates
        uptime: dict[str, dict[str, float]] = {}
        for _ws, info in self.connection_metadata.items():
            ch = info.get("type", "?")
            dur = (now - info.get("connected_at", now)).total_seconds()
            agg = uptime.setdefault(ch, {"count": 0.0, "total": 0.0})
            agg["count"] += 1.0
            agg["total"] += dur
        for ch, agg in uptime.items():
            if agg["count"]:
                stats["per_channel"].setdefault(ch, {})["avg_uptime_s"] = (
                    agg["total"] / agg["count"]
                )

        return stats


# Global connection manager
connection_manager = ConnectionManager()


class MarketDataStreamer:
    """Stream real-time market data"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.streaming_symbols: set[str] = set()
        self.stream_task: asyncio.Task | None = None
        # Small TTL cache to avoid hammering providers
        self._quote_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._quote_ttl: float = 10.0  # seconds

    async def start_streaming(self, symbols: list[str]):
        """Start streaming market data for given symbols"""
        self.streaming_symbols.update(symbols)

        if not self.stream_task or self.stream_task.done():
            self.stream_task = asyncio.create_task(self._stream_loop())

    async def stop_streaming(self, symbols: list[str] | None = None):
        """Stop streaming for specific symbols or all"""
        if symbols:
            self.streaming_symbols.difference_update(symbols)
        else:
            self.streaming_symbols.clear()

        if not self.streaming_symbols and self.stream_task:
            self.stream_task.cancel()

    async def _stream_loop(self):
        """Main streaming loop (best-effort, resilient)."""
        try:
            while self.streaming_symbols:
                for symbol in list(self.streaming_symbols):
                    try:
                        # Get latest market data (mock for now)
                        market_data = await self._get_market_data(symbol)
                        if market_data:
                            # Simple upstream backpressure: skip broadcast when queue is high
                            try:
                                stats = self.connection_manager.get_connection_stats()
                                ch_stats = stats.get("per_channel", {}).get(
                                    "market_data", {}
                                )
                                qlen = int(ch_stats.get("queue_len", 0))
                                maxsize = QUEUE_LIMITS["websocket_default"]
                                if maxsize > 0 and qlen / maxsize >= 0.8:
                                    # coalesce this tick; try next iteration
                                    continue
                            except Exception:
                                pass
                            # BRAIN ENHANCEMENT: Route data through Ziggy's brain
                            enhanced_data = await self._enhance_market_data_with_brain(
                                symbol, market_data
                            )

                            # UPDATE ALERT MONITORING: Feed market data to alert system
                            try:
                                from app.services.alert_monitoring import alert_monitor

                                alert_monitor.update_market_data(symbol, enhanced_data)
                            except Exception as alert_error:
                                logger.warning(
                                    f"Failed to update alert monitoring for {symbol}: {alert_error}"
                                )

                            # Broadcast to WebSocket clients
                            await self.connection_manager.broadcast_market_data(
                                symbol, enhanced_data
                            )
                    except Exception as e:
                        logger.error(f"Error streaming {symbol}: {e}")

                await asyncio.sleep(1)  # Stream every second

        except asyncio.CancelledError:
            logger.info("Market data streaming stopped")
        except Exception as e:
            logger.error(f"Market data streaming error: {e}")

    async def _enhance_market_data_with_brain(
        self, symbol: str, market_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhance real-time market data with Ziggy's brain intelligence"""
        try:
            # Import brain enhancement system
            from app.services.market_brain.simple_data_hub import (
                DataSource,
                enhance_market_data,
            )

            # Prepare data for brain enhancement
            symbol_data = {symbol: market_data}

            # Route through Ziggy's brain for enhancement
            enhanced = enhance_market_data(
                symbol_data, DataSource.OVERVIEW, symbols=[symbol]
            )

            # Extract enhanced data for the symbol
            if isinstance(enhanced, dict):
                # If brain returns enhanced structure, merge with original
                brain_enhanced_data = market_data.copy()
                brain_enhanced_data.update(
                    {
                        "brain_enhanced": True,
                        "brain_metadata": enhanced.get("brain_metadata", {}),
                        "market_regime": enhanced.get("market_regime", {}),
                        "enhanced_timestamp": market_data["timestamp"],
                    }
                )

                # Add brain-computed features if available
                symbols_data = enhanced.get("symbols", {})
                if symbol in symbols_data:
                    symbol_enhanced = symbols_data[symbol]
                    brain_enhanced_data.update(
                        {
                            "brain_features": symbol_enhanced.get("features", {}),
                            "regime_context": symbol_enhanced.get("regime_context", {}),
                            "confidence_score": symbol_enhanced.get(
                                "confidence_score", 0.5
                            ),
                        }
                    )

                logger.debug(f"Enhanced {symbol} data with brain intelligence")
                return brain_enhanced_data
            else:
                # Fallback: add basic brain metadata
                market_data["brain_enhanced"] = True
                market_data["brain_status"] = "basic_enhancement"
                return market_data

        except Exception as e:
            logger.warning(
                f"Brain enhancement failed for {symbol}: {e}, using raw data"
            )
            # Fallback: return original data with brain attempt marker
            market_data["brain_enhanced"] = False
            market_data["brain_error"] = str(e)
            return market_data

    async def _get_market_data(self, symbol: str) -> dict[str, Any] | None:
        """Get latest market data for symbol using real providers"""
        try:
            # Import providers and get current data
            import time
            from datetime import datetime

            from app.services.provider_factory import get_price_provider

            # Serve from small TTL cache if fresh
            ttl = self._quote_ttl
            cached = self._quote_cache.get(symbol)
            now_ts = time.time()
            if cached and cached[0] > now_ts:
                return cached[1]

            provider = get_price_provider()
            if not provider:
                logger.warning(f"No provider available for {symbol}")
                return None

            # Preferred path: provider_factory fetch_ohlc with short timeout; derive last/prev close
            try:

                async def _fetch_last_two() -> tuple[float | None, float | None]:
                    data = await provider.fetch_ohlc(
                        [symbol], period_days=3, adjusted=True
                    )
                    # Some providers may return (data_dict, source_map)
                    if isinstance(data, tuple) and len(data) >= 1:
                        data = data[0]
                    df = data.get(symbol)
                    if df is None or getattr(df, "empty", True):
                        return None, None
                    tail = df.tail(2)
                    if tail.shape[0] == 0:
                        return None, None
                    if tail.shape[0] == 1:
                        last = (
                            float(tail.iloc[-1]["Close"])
                            if tail.iloc[-1]["Close"] is not None
                            else None
                        )
                        return last, None
                    prev = (
                        float(tail.iloc[0]["Close"])
                        if tail.iloc[0]["Close"] is not None
                        else None
                    )
                    last = (
                        float(tail.iloc[-1]["Close"])
                        if tail.iloc[-1]["Close"] is not None
                        else None
                    )
                    return last, prev

                last, prev = await asyncio.wait_for(
                    _fetch_last_two(), timeout=TIMEOUTS["websocket_queue_get"]
                )
                if last is not None:
                    change = (last - prev) if prev is not None else 0.0
                    change_pct = ((change / prev) * 100.0) if prev else 0.0
                    market_data = {
                        "symbol": symbol,
                        "price": round(float(last), 2),
                        "change": round(float(change), 2),
                        "change_percent": round(float(change_pct), 2),
                        "volume": 0,  # volume not available from daily snapshot here
                        "timestamp": now_ts,
                        "market_time": datetime.now(UTC).isoformat(),
                        "provider": "provider_chain",
                    }
                    self._quote_cache[symbol] = (now_ts + ttl, market_data)
                    return market_data
            except Exception as e:
                logger.debug(f"Provider-chain quote path failed for {symbol}: {e}")

            # Secondary: try provider.today_open_prices as minimal fallback
            try:
                opens = provider.today_open_prices([symbol])
                val = opens.get(symbol)
                if val is not None:
                    market_data = {
                        "symbol": symbol,
                        "price": float(val),
                        "change": 0.0,
                        "change_percent": 0.0,
                        "volume": 0,
                        "timestamp": now_ts,
                        "market_time": datetime.now(UTC).isoformat(),
                        "provider": "open_fallback",
                    }
                    self._quote_cache[symbol] = (now_ts + ttl, market_data)
                    return market_data
            except Exception:
                pass

            # Last resort: yfinance direct (guarded, with minimal fields)
            try:
                import yfinance as yf

                ticker = yf.Ticker(symbol)
                info = ticker.info
                current_price = info.get("currentPrice") or info.get(
                    "regularMarketPrice"
                )
                if not current_price:
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                if not current_price:
                    return None
                previous_close = info.get("previousClose") or info.get(
                    "regularMarketPreviousClose"
                )
                change = (current_price - previous_close) if previous_close else 0.0
                change_percent = (
                    ((change / previous_close) * 100) if previous_close else 0.0
                )
                volume = info.get("regularMarketVolume") or info.get("volume", 0)
                market_data = {
                    "symbol": symbol,
                    "price": round(float(current_price), 2),
                    "change": round(float(change), 2),
                    "change_percent": round(float(change_percent), 2),
                    "volume": int(volume) if volume else 0,
                    "timestamp": now_ts,
                    "market_time": datetime.now(UTC).isoformat(),
                    "provider": "yfinance",
                }
                self._quote_cache[symbol] = (now_ts + ttl, market_data)
                return market_data
            except Exception as e:
                logger.warning(f"yfinance error for {symbol}: {e}")
                return None

        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None


# Global market data streamer
market_streamer = MarketDataStreamer(connection_manager)
