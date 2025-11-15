# app/services/chart_streaming.py
from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass
from typing import Any

import yfinance as yf

from app.core.config.time_tuning import TIMEOUTS
from app.core.logging import get_logger
from app.core.websocket import ConnectionManager


logger = get_logger("ziggy.chart_streaming")


@dataclass
class Candlestick:
    """Single candlestick data point"""

    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str
    timeframe: str


@dataclass
class TechnicalIndicator:
    """Technical indicator data"""

    name: str
    value: float
    timestamp: float
    symbol: str
    timeframe: str


class ChartStreamer:
    """Real-time chart data and candlestick streaming service"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

        # Supported timeframes and their update intervals
        self.timeframes = {
            "1m": 60,  # 1 minute bars, update every 60 seconds
            "5m": 300,  # 5 minute bars, update every 5 minutes
            "15m": 900,  # 15 minute bars, update every 15 minutes
            "1h": 3600,  # 1 hour bars, update every hour
            "1d": 86400,  # Daily bars, update once per day
        }

        # Active subscriptions: symbol -> set of timeframes
        self.active_subscriptions: dict[str, set[str]] = {}

        # Cache for chart data to avoid redundant API calls
        self.chart_cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = 30  # 30 seconds cache TTL for most timeframes

        # Streaming control
        self.is_running = False
        self.streaming_tasks: dict[str, asyncio.Task] = {}

        # Performance tracking
        self.update_count = 0
        self.error_count = 0
        self.last_update_time = 0.0

    async def start_streaming(
        self, symbols: list[str], timeframes: list[str] | None = None
    ):
        """Start chart data streaming for specified symbols and timeframes"""
        if timeframes is None:
            timeframes = ["1m", "5m", "1h"]  # Default timeframes

        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in self.active_subscriptions:
                self.active_subscriptions[symbol] = set()

            for timeframe in timeframes:
                if timeframe in self.timeframes:
                    self.active_subscriptions[symbol].add(timeframe)

                    # Start individual streaming task for this symbol-timeframe combo
                    task_key = f"{symbol}_{timeframe}"
                    if task_key not in self.streaming_tasks:
                        self.streaming_tasks[task_key] = asyncio.create_task(
                            self._stream_chart_data(symbol, timeframe)
                        )

        self.is_running = True
        logger.info(
            "Chart streaming started",
            extra={
                "symbols": symbols,
                "timeframes": timeframes,
                "active_subscriptions": len(self.active_subscriptions),
            },
        )

    async def stop_streaming(
        self, symbols: list[str] | None = None, timeframes: list[str] | None = None
    ):
        """Stop chart data streaming for specified symbols/timeframes or all"""
        if symbols is None:
            # Stop all streaming
            for task in self.streaming_tasks.values():
                task.cancel()
            self.streaming_tasks.clear()
            self.active_subscriptions.clear()
            self.is_running = False
            logger.info("All chart streaming stopped")
            return

        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in self.active_subscriptions:
                if timeframes is None:
                    # Remove all timeframes for this symbol
                    timeframes_to_remove = list(self.active_subscriptions[symbol])
                else:
                    timeframes_to_remove = timeframes

                for timeframe in timeframes_to_remove:
                    if timeframe in self.active_subscriptions[symbol]:
                        self.active_subscriptions[symbol].discard(timeframe)

                        # Cancel the streaming task
                        task_key = f"{symbol}_{timeframe}"
                        if task_key in self.streaming_tasks:
                            self.streaming_tasks[task_key].cancel()
                            del self.streaming_tasks[task_key]

                # Remove symbol if no timeframes left
                if not self.active_subscriptions[symbol]:
                    del self.active_subscriptions[symbol]

        # Check if all streaming stopped
        if not self.active_subscriptions:
            self.is_running = False

        logger.info(
            "Chart streaming stopped",
            extra={"symbols": symbols, "timeframes": timeframes},
        )

    async def _stream_chart_data(self, symbol: str, timeframe: str):
        """Stream chart data for a specific symbol and timeframe"""
        update_interval = self.timeframes[timeframe]

        # For minute charts, update more frequently
        if timeframe == "1m":
            update_interval = 30  # Update every 30 seconds for 1-minute charts
        elif timeframe == "5m":
            update_interval = 60  # Update every minute for 5-minute charts

        logger.info(
            f"Starting chart streaming for {symbol} {timeframe}",
            extra={
                "symbol": symbol,
                "timeframe": timeframe,
                "update_interval": update_interval,
            },
        )

        while self.is_running and symbol in self.active_subscriptions:
            if timeframe not in self.active_subscriptions.get(symbol, set()):
                break

            start_time = time.time()

            try:
                # Upstream backpressure: if charts queue is near capacity, skip this tick
                try:
                    size, cap, ratio = self.connection_manager.get_queue_utilization(
                        "charts"
                    )
                    if cap and ratio >= 0.8:
                        logger.debug(
                            "Skipping chart update due to high queue utilization",
                            extra={
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "queue_size": size,
                                "queue_capacity": cap,
                                "utilization": round(ratio, 3),
                            },
                        )
                        # brief pause to allow consumer to catch up
                        await asyncio.sleep(min(2.0, update_interval / 2))
                        continue
                except Exception:
                    # Do not let metrics/backpressure checks break streaming
                    pass

                # Fetch chart data
                chart_data = await self._fetch_chart_data(symbol, timeframe)

                if chart_data:
                    # Broadcast chart update
                    await self._broadcast_chart_update(symbol, timeframe, chart_data)
                    self.update_count += 1
                    self.last_update_time = time.time()

                # Calculate processing time and adjust sleep
                processing_time = time.time() - start_time
                sleep_time = max(0, update_interval - processing_time)

                if processing_time > update_interval:
                    logger.warning(
                        "Chart data processing slow",
                        extra={
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "processing_time": processing_time,
                            "target_interval": update_interval,
                        },
                    )

                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.error_count += 1
                logger.error(
                    "Chart streaming error",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "error": str(e),
                        "error_count": self.error_count,
                    },
                )
                await asyncio.sleep(60)  # Longer pause on error

    async def _fetch_chart_data(
        self, symbol: str, timeframe: str
    ) -> dict[str, Any] | None:
        """Fetch chart data from yfinance"""
        cache_key = f"{symbol}_{timeframe}"
        current_time = time.time()

        # Check cache first
        if cache_key in self.chart_cache:
            cached_data = self.chart_cache[cache_key]
            if current_time - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]

        try:
            # Map our timeframes to yfinance intervals
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "1h": "1h",
                "1d": "1d",
            }

            # Determine period based on timeframe
            period_map = {
                "1m": "1d",  # 1 day of 1-minute data
                "5m": "5d",  # 5 days of 5-minute data
                "15m": "1mo",  # 1 month of 15-minute data
                "1h": "3mo",  # 3 months of hourly data
                "1d": "1y",  # 1 year of daily data
            }

            interval = interval_map.get(timeframe, "1h")
            period = period_map.get(timeframe, "1mo")

            # Fetch data from yfinance with timeout
            try:
                ticker = yf.Ticker(symbol)
                # Use asyncio timeout to prevent hanging
                hist = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: ticker.history(
                            period=period,
                            interval=interval,
                            auto_adjust=True,
                            prepost=True,
                        ),
                    ),
                    timeout=TIMEOUTS["provider_market_data"],
                )

                if hist.empty:
                    logger.warning(f"No chart data available for {symbol} {timeframe}")
                    return None

            except TimeoutError:
                logger.error(f"Timeout fetching chart data for {symbol} {timeframe}")
                return None
            except Exception as fetch_error:
                logger.error(
                    f"Failed to fetch data from yfinance for {symbol}: {fetch_error}"
                )
                return None

            # Convert to our candlestick format
            candlesticks = []
            for timestamp, row in hist.iterrows():
                # Handle different timestamp types safely
                try:
                    if hasattr(timestamp, "timestamp"):
                        ts_value = timestamp.timestamp()  # type: ignore
                    else:
                        ts_value = float(str(timestamp))
                except (ValueError, TypeError, AttributeError):
                    ts_value = time.time()

                candlestick = Candlestick(
                    timestamp=ts_value,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                    symbol=symbol,
                    timeframe=timeframe,
                )
                candlesticks.append(asdict(candlestick))

            # Calculate basic technical indicators
            indicators = await self._calculate_indicators(
                candlesticks, symbol, timeframe
            )

            chart_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "candlesticks": candlesticks[-100:],  # Last 100 bars
                "indicators": indicators,
                "last_updated": current_time,
            }

            # Update cache
            self.chart_cache[cache_key] = {
                "data": chart_data,
                "timestamp": current_time,
            }

            return chart_data

        except Exception as e:
            logger.error(f"Error fetching chart data for {symbol} {timeframe}: {e}")
            return None

    async def _calculate_indicators(
        self, candlesticks: list[dict[str, Any]], symbol: str, timeframe: str
    ) -> list[dict[str, Any]]:
        """Calculate basic technical indicators"""
        if len(candlesticks) < 20:
            return []

        indicators = []
        current_time = time.time()

        try:
            # Extract close prices
            closes = [candle["close"] for candle in candlesticks]

            # Simple Moving Averages
            if len(closes) >= 20:
                sma_20 = sum(closes[-20:]) / 20
                indicators.append(
                    {
                        "name": "SMA_20",
                        "value": sma_20,
                        "timestamp": current_time,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )

            if len(closes) >= 50:
                sma_50 = sum(closes[-50:]) / 50
                indicators.append(
                    {
                        "name": "SMA_50",
                        "value": sma_50,
                        "timestamp": current_time,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )

            # RSI (Relative Strength Index)
            if len(closes) >= 14:
                rsi = self._calculate_rsi(closes, 14)
                indicators.append(
                    {
                        "name": "RSI_14",
                        "value": rsi,
                        "timestamp": current_time,
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )

            # MACD (Moving Average Convergence Divergence)
            if len(closes) >= 26:
                macd_line, signal_line = self._calculate_macd(closes)
                indicators.extend(
                    [
                        {
                            "name": "MACD",
                            "value": macd_line,
                            "timestamp": current_time,
                            "symbol": symbol,
                            "timeframe": timeframe,
                        },
                        {
                            "name": "MACD_Signal",
                            "value": signal_line,
                            "timestamp": current_time,
                            "symbol": symbol,
                            "timeframe": timeframe,
                        },
                    ]
                )

        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")

        return indicators

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(
        self,
        prices: list[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[float, float]:
        """Calculate MACD and Signal line"""
        if len(prices) < slow_period:
            return 0.0, 0.0

        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)

        macd_line = ema_fast - ema_slow

        # For signal line, we'd need historical MACD values
        # For simplicity, using a simple approximation
        signal_line = macd_line * 0.9  # Simplified signal line

        return macd_line, signal_line

    def _calculate_ema(self, prices: list[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Initial SMA

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    async def _broadcast_chart_update(
        self, symbol: str, timeframe: str, chart_data: dict[str, Any]
    ):
        """Broadcast chart update to connected clients"""
        message = {
            "type": "chart_update",
            "symbol": symbol,
            "timeframe": timeframe,
            "data": chart_data,
            "timestamp": time.time(),
            "update_count": self.update_count,
        }

        await self.connection_manager.broadcast_to_type(message, "charts")

        logger.debug(
            "Chart update broadcasted",
            extra={
                "symbol": symbol,
                "timeframe": timeframe,
                "candlesticks_count": len(chart_data.get("candlesticks", [])),
                "indicators_count": len(chart_data.get("indicators", [])),
                "update_count": self.update_count,
            },
        )

    async def handle_client_message(self, websocket, message: dict[str, Any]):
        """Handle incoming client messages for chart streaming"""
        action = message.get("action")
        symbol = message.get("symbol", "").upper()
        timeframes = message.get("timeframes", ["1m"])

        if action == "subscribe":
            if symbol:
                await self.start_streaming([symbol], timeframes)
                response = {
                    "type": "subscription_ack",
                    "symbol": symbol,
                    "timeframes": timeframes,
                    "timestamp": time.time(),
                }
                await self.connection_manager.send_json_personal(response, websocket)

        elif action == "unsubscribe":
            if symbol:
                await self.stop_streaming([symbol], timeframes)
                response = {
                    "type": "unsubscription_ack",
                    "symbol": symbol,
                    "timeframes": timeframes,
                    "timestamp": time.time(),
                }
                await self.connection_manager.send_json_personal(response, websocket)

        elif action == "get_snapshot":
            if symbol:
                try:
                    chart_data = await self._fetch_chart_data(symbol, timeframes[0])
                    response = {
                        "type": "chart_snapshot",
                        "symbol": symbol,
                        "timeframe": timeframes[0],
                        "data": chart_data,
                        "timestamp": time.time(),
                    }
                    await self.connection_manager.send_json_personal(
                        response, websocket
                    )
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "message": f"Failed to get chart snapshot: {e!s}",
                        "timestamp": time.time(),
                    }
                    await self.connection_manager.send_json_personal(
                        error_response, websocket
                    )

        elif action == "get_stats":
            stats = {
                "type": "chart_streaming_stats",
                "stats": {
                    "update_count": self.update_count,
                    "error_count": self.error_count,
                    "last_update_time": self.last_update_time,
                    "is_running": self.is_running,
                    "active_subscriptions": dict(self.active_subscriptions),
                    "supported_timeframes": list(self.timeframes.keys()),
                },
                "timestamp": time.time(),
            }
            await self.connection_manager.send_json_personal(stats, websocket)

        else:
            logger.warning(f"Unknown chart action: {action}")


# Global chart streamer instance
chart_streamer: ChartStreamer | None = None


def get_chart_streamer(connection_manager: ConnectionManager) -> ChartStreamer:
    """Get or create global chart streamer instance"""
    global chart_streamer
    if chart_streamer is None:
        chart_streamer = ChartStreamer(connection_manager)
    return chart_streamer
