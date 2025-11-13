# app/services/portfolio_streaming.py
from __future__ import annotations

import asyncio
import contextlib
import time
from datetime import UTC, datetime
from typing import Any

from app.core.config.time_tuning import BACKOFFS, QUEUE_LIMITS, TIMEOUTS
from app.core.logging import get_logger
from app.core.websocket import ConnectionManager
from app.trading.signals import get_portfolio_summary, get_positions


logger = get_logger("ziggy.portfolio_streaming")


class PortfolioStreamer:
    """Real-time portfolio value, P&L, and position streaming service"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.update_interval = 5.0  # target producer interval (seconds)
        self.is_running = False
        # Dedicated tasks
        self._producer_task: asyncio.Task | None = None
        self._consumer_task: asyncio.Task | None = None
        # Decoupling queue (coalescing): producer snapshots go here, consumer broadcasts
        self.portfolio_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=QUEUE_LIMITS["portfolio_snapshots"]
        )

        # Portfolio cache for change detection
        self.last_portfolio_data: dict[str, Any] | None = None
        self.last_positions_data: list[dict[str, Any]] | None = None

        # Performance tracking
        self.update_count = 0
        self.error_count = 0
        self.last_update_time = 0.0
        # Health/backoff state
        self._error_streak = 0
        self._last_state: str = "INIT"
        self._last_state_log_ts: float = 0.0
        # Metrics
        self.broadcasts_attempted: int = 0
        self.broadcasts_failed: int = 0

    async def start_streaming(self):
        """Start portfolio data streaming"""
        if self.is_running:
            logger.warning("Portfolio streaming already running")
            return

        self.is_running = True
        # Start consumer first so broadcasts are handled
        self._consumer_task = asyncio.create_task(self._consume_loop())
        self._producer_task = asyncio.create_task(self._producer_loop())
        logger.info(
            "Portfolio streaming started",
            extra={"update_interval_s": self.update_interval},
        )

    async def stop_streaming(self):
        """Stop portfolio data streaming"""
        if not self.is_running:
            return

        self.is_running = False
        from contextlib import suppress

        # Cancel producer
        if self._producer_task:
            self._producer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._producer_task
        # Cancel consumer
        if self._consumer_task:
            self._consumer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._consumer_task

        logger.info(
            "Portfolio streaming stopped",
            extra={"total_updates": self.update_count, "total_errors": self.error_count},
        )

    async def _producer_loop(self):
        """Producer: build snapshots, coalesce into the queue, keep heavy work off the loop."""
        logger.info("Starting portfolio producer loop")
        while self.is_running:
            t0 = time.time()
            try:
                # Build snapshot (fetch + enrich)
                portfolio_data = await self._get_portfolio_data()
                positions_data = await self._get_positions_data()

                if await self._has_portfolio_changed(portfolio_data, positions_data):
                    snapshot = {
                        "type": "portfolio_update",
                        "portfolio": portfolio_data,
                        "positions": positions_data,
                        "timestamp": time.time(),
                        "update_count": self.update_count,
                    }
                    # Coalesce: if full, drop oldest then put
                    try:
                        self.portfolio_queue.put_nowait(snapshot)
                    except asyncio.QueueFull:
                        try:
                            _ = self.portfolio_queue.get_nowait()  # drop oldest
                            self.portfolio_queue.task_done()
                        except Exception:
                            pass
                        finally:
                            with contextlib.suppress(Exception):
                                self.portfolio_queue.put_nowait(snapshot)
                    # Expose queue length metric via connection manager
                    with contextlib.suppress(Exception):
                        self.connection_manager.set_metric(
                            "portfolio", "portfolio_queue_len", float(self.portfolio_queue.qsize())
                        )

                    # Update last cached
                    self.last_portfolio_data = portfolio_data
                    self.last_positions_data = positions_data

                # Success path bookkeeping
                self.update_count += 1
                self.last_update_time = time.time()
                if self._error_streak > 0:
                    self._error_streak = 0
                    if self._last_state != "UP" or (time.time() - self._last_state_log_ts) > 10.0:
                        logger.info("Portfolio streamer state: UP")
                        self._last_state = "UP"
                        self._last_state_log_ts = time.time()

                # pacing
                producer_ms = (time.time() - t0) * 1000.0
                if producer_ms > self.update_interval * 1000.0:
                    logger.warning(
                        "Portfolio producer slow",
                        extra={
                            "producer_ms": round(producer_ms, 1),
                            "target_interval_s": self.update_interval,
                        },
                    )
                await asyncio.sleep(max(0.0, self.update_interval - (time.time() - t0)))

            except TimeoutError:
                self.error_count += 1
                self._error_streak = min(
                    self._error_streak + 1, BACKOFFS["portfolio_max_streak"] * 2
                )
                backoff = min(
                    BACKOFFS["portfolio_max_delay"],
                    BACKOFFS["portfolio_base"]
                    ** min(BACKOFFS["portfolio_max_streak"], self._error_streak),
                )
                now = time.time()
                if self._last_state != "DOWN" or (now - self._last_state_log_ts) > 10.0:
                    logger.warning(
                        "Portfolio streamer state: DOWN (timeout)",
                        extra={"error_count": self.error_count, "backoff_s": backoff},
                    )
                    self._last_state = "DOWN"
                    self._last_state_log_ts = now
                await asyncio.sleep(backoff)
            except Exception as e:
                self.error_count += 1
                self._error_streak = min(
                    self._error_streak + 1, BACKOFFS["portfolio_max_streak"] * 2
                )
                backoff = min(
                    BACKOFFS["portfolio_max_delay"],
                    BACKOFFS["portfolio_base"]
                    ** min(BACKOFFS["portfolio_max_streak"], self._error_streak),
                )
                now = time.time()
                if self._last_state != "DOWN" or (now - self._last_state_log_ts) > 10.0:
                    logger.error(
                        "Portfolio streamer state: DOWN (error)",
                        extra={
                            "error": repr(e),
                            "error_count": self.error_count,
                            "backoff_s": backoff,
                        },
                    )
                    self._last_state = "DOWN"
                    self._last_state_log_ts = now
                await asyncio.sleep(backoff)

    async def _consume_loop(self):
        """Consumer: broadcast snapshots from the queue to clients."""
        logger.info("Starting portfolio consumer loop")
        while self.is_running:
            try:
                snapshot = await self.portfolio_queue.get()
                t0 = time.time()
                self.broadcasts_attempted += 1
                try:
                    # Truncate payload in logs for visibility only
                    # Broadcasting via connection manager which fans out safely
                    await self.connection_manager.broadcast_to_type(snapshot, "portfolio")
                except Exception as e:
                    self.broadcasts_failed += 1
                    # Count failures with channel and ids recorded by connection manager
                    logger.warning(
                        "Failed to broadcast portfolio snapshot",
                        extra={"channel": "portfolio", "error": repr(e)},
                    )
                finally:
                    self.portfolio_queue.task_done()
                    # Expose queue length metric after drain
                    with contextlib.suppress(Exception):
                        self.connection_manager.set_metric(
                            "portfolio", "portfolio_queue_len", float(self.portfolio_queue.qsize())
                        )
                    # Warn if broadcast slow
                    b_ms = (time.time() - t0) * 1000.0
                    if b_ms > 2000.0:
                        logger.warning(
                            "Portfolio broadcast slow", extra={"broadcast_ms": round(b_ms, 1)}
                        )
            except asyncio.CancelledError:
                # Task cancelled during shutdown; exit loop gracefully
                break
            except Exception as e:
                # Catch any unexpected error during consumption to keep loop alive
                self.broadcasts_failed += 1
                logger.error("Error in portfolio consumer loop", extra={"error": repr(e)})
                await asyncio.sleep(0.5)

    async def _get_portfolio_data(self) -> dict[str, Any]:
        """Fetch current portfolio summary data"""
        try:
            # Get portfolio summary from trading system (with aggressive timeout protection)
            portfolio_summary = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, get_portfolio_summary),
                timeout=TIMEOUTS["async_fast"],
            )

            # Enhance with real-time calculated metrics
            current_time = datetime.now(UTC)

            # Calculate additional real-time metrics
            portfolio_data = {
                "total_value": portfolio_summary.get("total_value", 0.0),
                "cash_balance": portfolio_summary.get("cash_balance", 0.0),
                "daily_pnl": portfolio_summary.get("daily_pnl", 0.0),
                "daily_pnl_percent": portfolio_summary.get("daily_pnl_percent", 0.0),
                "market_value": portfolio_summary.get("market_value", 0.0),
                "cost_basis": portfolio_summary.get("cost_basis", 0.0),
                "unrealized_pnl": portfolio_summary.get("unrealized_pnl", 0.0),
                "realized_pnl": portfolio_summary.get("realized_pnl", 0.0),
                "buying_power": portfolio_summary.get("buying_power", 0.0),
                "margin_used": portfolio_summary.get("margin_used", 0.0),
                "day_trades_count": portfolio_summary.get("day_trades_count", 0),
                "timestamp": current_time.isoformat(),
                "last_updated": time.time(),
            }

            return portfolio_data

        except Exception as e:
            logger.error(f"Error fetching portfolio data: {e}")
            # Return default/safe values on error
            return {
                "total_value": 0.0,
                "cash_balance": 0.0,
                "daily_pnl": 0.0,
                "daily_pnl_percent": 0.0,
                "market_value": 0.0,
                "cost_basis": 0.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "buying_power": 0.0,
                "margin_used": 0.0,
                "day_trades_count": 0,
                "timestamp": datetime.now(UTC).isoformat(),
                "last_updated": time.time(),
                "error": str(e),
            }

    async def _get_positions_data(self) -> list[dict[str, Any]]:
        """Fetch current positions data"""
        try:
            # Get positions from trading system (with aggressive timeout protection)
            positions = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, get_positions),
                timeout=TIMEOUTS["async_fast"],
            )

            # Enhance positions with real-time metrics
            enhanced_positions = []
            for position in positions:
                enhanced_position = {
                    "symbol": position.get("symbol", ""),
                    "quantity": position.get("quantity", 0),
                    "avg_price": position.get("avg_price", 0.0),
                    "current_price": position.get("current_price", 0.0),
                    "market_value": position.get("market_value", 0.0),
                    "cost_basis": position.get("cost_basis", 0.0),
                    "unrealized_pnl": position.get("unrealized_pnl", 0.0),
                    "unrealized_pnl_percent": position.get("unrealized_pnl_percent", 0.0),
                    "day_pnl": position.get("day_pnl", 0.0),
                    "day_pnl_percent": position.get("day_pnl_percent", 0.0),
                    "side": position.get("side", "long"),  # long/short
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                enhanced_positions.append(enhanced_position)

            return enhanced_positions

        except Exception as e:
            logger.error(f"Error fetching positions data: {e}")
            return []

    async def _has_portfolio_changed(
        self, current_portfolio: dict[str, Any], current_positions: list[dict[str, Any]]
    ) -> bool:
        """Check if portfolio data has meaningfully changed.

        Improvements:
        - Order-independent comparison of positions (keyed by symbol)
        - Small absolute thresholds to filter noise (prices/values)
        - Detect add/remove/quantity/price/value changes
        """
        if not self.last_portfolio_data or not self.last_positions_data:
            return True

        # Thresholds to reduce noise from tiny fluctuations
        portfolio_threshold = 0.01  # $0.01 change threshold for totals
        price_threshold = 0.01  # $0.01 price change
        value_threshold = 0.01  # $0.01 market value change

        # Portfolio-level deltas
        totals_changed = (
            abs(
                current_portfolio.get("total_value", 0.0)
                - self.last_portfolio_data.get("total_value", 0.0)
            )
            > portfolio_threshold
        ) or (
            abs(
                current_portfolio.get("daily_pnl", 0.0)
                - self.last_portfolio_data.get("daily_pnl", 0.0)
            )
            > portfolio_threshold
        )

        # Map positions by symbol for order-independent comparison
        def to_map(positions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
            out: dict[str, dict[str, Any]] = {}
            for p in positions:
                sym = (p.get("symbol") or "").upper()
                if sym:
                    out[sym] = p
            return out

        cur_map = to_map(current_positions)
        last_map = to_map(self.last_positions_data)

        # Detect add/remove quickly via symbol set difference
        if set(cur_map.keys()) != set(last_map.keys()):
            return True

        # Compare shared symbols for meaningful changes
        for sym in cur_map:
            c = cur_map[sym]
            last = last_map.get(sym, {})

            # Quantity change (position size adjusted or closed/opened in same tick)
            if c.get("quantity", 0) != last.get("quantity", 0):
                return True

            # Price or market value change with noise thresholds
            if (
                abs(float(c.get("current_price", 0.0)) - float(last.get("current_price", 0.0)))
                > price_threshold
            ):
                return True
            if (
                abs(float(c.get("market_value", 0.0)) - float(last.get("market_value", 0.0)))
                > value_threshold
            ):
                return True

        return totals_changed

    # _broadcast_portfolio_update removed; handled by _consume_loop

    async def handle_client_message(self, websocket, message: dict[str, Any]):
        """Handle incoming client messages for portfolio streaming"""
        action = message.get("action")

        if action == "force_update":
            # Force immediate portfolio update
            try:
                portfolio_data = await self._get_portfolio_data()
                positions_data = await self._get_positions_data()

                response = {
                    "type": "portfolio_snapshot",
                    "portfolio": portfolio_data,
                    "positions": positions_data,
                    "timestamp": time.time(),
                }

                await self.connection_manager.send_json_personal(response, websocket)
                logger.info("Force portfolio update sent")

            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": f"Failed to get portfolio snapshot: {e!s}",
                    "timestamp": time.time(),
                }
                await self.connection_manager.send_json_personal(error_response, websocket)

        elif action == "get_performance_stats":
            # Send streaming performance statistics
            stats = {
                "type": "portfolio_streaming_stats",
                "stats": {
                    "update_count": self.update_count,
                    "error_count": self.error_count,
                    "last_update_time": self.last_update_time,
                    "is_running": self.is_running,
                    "update_interval": self.update_interval,
                },
                "timestamp": time.time(),
            }

            await self.connection_manager.send_json_personal(stats, websocket)

        else:
            logger.warning(f"Unknown portfolio action: {action}")


# Global portfolio streamer instance
portfolio_streamer: PortfolioStreamer | None = None


def get_portfolio_streamer(connection_manager: ConnectionManager) -> PortfolioStreamer:
    """Get or create global portfolio streamer instance"""
    global portfolio_streamer
    if portfolio_streamer is None:
        portfolio_streamer = PortfolioStreamer(connection_manager)
    return portfolio_streamer


async def start_portfolio_streaming():
    """Start portfolio streaming (call during app startup)"""
    from app.core.websocket import connection_manager
    streamer = get_portfolio_streamer(connection_manager)
    await streamer.start_streaming()


async def stop_portfolio_streaming():
    """Stop portfolio streaming (call during app shutdown)"""
    global portfolio_streamer
    if portfolio_streamer:
        await portfolio_streamer.stop_streaming()
