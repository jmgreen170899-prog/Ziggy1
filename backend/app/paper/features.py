"""
Feature engineering pipeline for ZiggyAI paper trading lab.

This module provides rolling indicators, market state classification,
and regime detection for feeding into trading theories.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.core.logging import get_logger
from app.paper.theories import MarketFeatures


logger = get_logger("ziggy.features")


@dataclass
class PriceData:
    """Single price observation."""

    timestamp: datetime
    symbol: str
    open_price: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class TechnicalIndicators:
    """Technical indicator values."""

    sma_5: float = 0.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
    atr: float = 0.0
    stochastic_k: float = 50.0
    stochastic_d: float = 50.0


class RollingWindow:
    """Efficient rolling window for price data."""

    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self.data: list[PriceData] = []
        self.symbol_data: dict[str, list[PriceData]] = {}

    def add(self, price_data: PriceData) -> None:
        """Add new price data point."""
        # Add to global data
        self.data.append(price_data)
        if len(self.data) > self.max_size:
            self.data.pop(0)

        # Add to symbol-specific data
        if price_data.symbol not in self.symbol_data:
            self.symbol_data[price_data.symbol] = []

        symbol_list = self.symbol_data[price_data.symbol]
        symbol_list.append(price_data)
        if len(symbol_list) > self.max_size:
            symbol_list.pop(0)

    def get_symbol_data(
        self, symbol: str, lookback: int | None = None
    ) -> list[PriceData]:
        """Get recent data for a symbol."""
        if symbol not in self.symbol_data:
            return []

        data = self.symbol_data[symbol]
        if lookback is None:
            return data
        return data[-lookback:] if lookback <= len(data) else data

    def get_latest(self, symbol: str) -> PriceData | None:
        """Get latest price for symbol."""
        data = self.get_symbol_data(symbol, 1)
        return data[0] if data else None


class FeatureComputer:
    """Computes technical indicators and market features."""

    def __init__(self, window_size: int = 200):
        self.window = RollingWindow(window_size)
        self.ema_cache: dict[tuple[str, int], float] = {}

    def add_price_data(self, price_data: PriceData) -> None:
        """Add new price data to the window."""
        self.window.add(price_data)

    def compute_features(self, symbol: str) -> MarketFeatures | None:
        """
        Compute comprehensive market features for a symbol.

        Args:
            symbol: Symbol to compute features for

        Returns:
            MarketFeatures object or None if insufficient data
        """
        data = self.window.get_symbol_data(symbol)
        if not data:
            return None

        latest = data[-1]

        # Compute technical indicators
        indicators = self._compute_technical_indicators(symbol, data)

        # Compute regime classifications
        vol_regime = self._classify_volatility_regime(data)
        trend_regime = self._classify_trend_regime(data, indicators)

        # Compute market microstructure (simplified)
        bid_ask_spread = self._estimate_bid_ask_spread(latest)
        order_flow_imbalance = self._estimate_order_flow_imbalance(data)

        # News/sentiment (placeholder - would integrate with news service)
        news_sentiment = 0.0
        news_urgency = 0.0

        # Cross-asset correlations (simplified)
        spy_correlation = self._compute_spy_correlation(symbol, data)
        sector_momentum = self._compute_sector_momentum(symbol, data)

        return MarketFeatures(
            symbol=symbol,
            timestamp=latest.timestamp,
            price=latest.close,
            open_price=latest.open_price,
            high=latest.high,
            low=latest.low,
            volume=latest.volume,
            sma_5=indicators.sma_5,
            sma_20=indicators.sma_20,
            sma_50=indicators.sma_50,
            rsi=indicators.rsi,
            bollinger_upper=indicators.bollinger_upper,
            bollinger_lower=indicators.bollinger_lower,
            atr=indicators.atr,
            vol_regime=vol_regime,
            trend_regime=trend_regime,
            bid_ask_spread=bid_ask_spread,
            order_flow_imbalance=order_flow_imbalance,
            news_sentiment=news_sentiment,
            news_urgency=news_urgency,
            spy_correlation=spy_correlation,
            sector_momentum=sector_momentum,
        )

    def _compute_technical_indicators(
        self, symbol: str, data: list[PriceData]
    ) -> TechnicalIndicators:
        """Compute technical indicators."""
        if not data:
            return TechnicalIndicators()

        closes = [d.close for d in data]

        indicators = TechnicalIndicators()

        # Simple Moving Averages
        if len(closes) >= 5:
            indicators.sma_5 = sum(closes[-5:]) / 5
        if len(closes) >= 20:
            indicators.sma_20 = sum(closes[-20:]) / 20
        if len(closes) >= 50:
            indicators.sma_50 = sum(closes[-50:]) / 50

        # Exponential Moving Averages
        indicators.ema_12 = self._compute_ema(symbol, closes, 12)
        indicators.ema_26 = self._compute_ema(symbol, closes, 26)

        # MACD
        if indicators.ema_12 > 0 and indicators.ema_26 > 0:
            indicators.macd = indicators.ema_12 - indicators.ema_26

        # RSI
        if len(closes) >= 15:
            indicators.rsi = self._compute_rsi(closes[-15:])

        # Bollinger Bands
        if len(closes) >= 20:
            indicators.bollinger_middle = indicators.sma_20
            std_dev = self._compute_std_dev(closes[-20:])
            indicators.bollinger_upper = indicators.bollinger_middle + (2 * std_dev)
            indicators.bollinger_lower = indicators.bollinger_middle - (2 * std_dev)

        # Average True Range (ATR)
        if len(data) >= 15:
            indicators.atr = self._compute_atr(data[-15:])

        # Stochastic
        if len(data) >= 14:
            indicators.stochastic_k, indicators.stochastic_d = self._compute_stochastic(
                data[-14:]
            )

        return indicators

    def _compute_ema(self, symbol: str, closes: list[float], period: int) -> float:
        """Compute Exponential Moving Average."""
        if len(closes) < period:
            return 0.0

        cache_key = (symbol, period)
        alpha = 2.0 / (period + 1)

        if cache_key in self.ema_cache:
            # Update from cached value
            prev_ema = self.ema_cache[cache_key]
            current_ema = alpha * closes[-1] + (1 - alpha) * prev_ema
        else:
            # Initialize with SMA
            sma = sum(closes[:period]) / period
            current_ema = sma
            # Calculate EMA from SMA
            for i in range(period, len(closes)):
                current_ema = alpha * closes[i] + (1 - alpha) * current_ema

        self.ema_cache[cache_key] = current_ema
        return current_ema

    def _compute_rsi(self, closes: list[float]) -> float:
        """Compute Relative Strength Index."""
        if len(closes) < 2:
            return 50.0

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if not gains:
            return 50.0

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _compute_std_dev(self, values: list[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _compute_atr(self, data: list[PriceData]) -> float:
        """Compute Average True Range."""
        if len(data) < 2:
            return 0.0

        true_ranges = []
        for i in range(1, len(data)):
            high_low = data[i].high - data[i].low
            high_close = abs(data[i].high - data[i - 1].close)
            low_close = abs(data[i].low - data[i - 1].close)
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)

        return sum(true_ranges) / len(true_ranges)

    def _compute_stochastic(self, data: list[PriceData]) -> tuple[float, float]:
        """Compute Stochastic oscillator."""
        if len(data) < 14:
            return 50.0, 50.0

        recent_data = data[-14:]
        highest_high = max(d.high for d in recent_data)
        lowest_low = min(d.low for d in recent_data)
        current_close = data[-1].close

        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = (
                (current_close - lowest_low) / (highest_high - lowest_low)
            ) * 100

        # Simplified %D (usually 3-period SMA of %K)
        d_percent = k_percent  # Would normally be smoothed

        return k_percent, d_percent

    def _classify_volatility_regime(self, data: list[PriceData]) -> str:
        """Classify current volatility regime."""
        if len(data) < 20:
            return "normal"

        # Calculate recent volatility
        recent_returns = []
        for i in range(1, min(21, len(data))):
            ret = (data[-i].close - data[-i - 1].close) / data[-i - 1].close
            recent_returns.append(ret)

        if not recent_returns:
            return "normal"

        volatility = self._compute_std_dev(recent_returns) * math.sqrt(
            252
        )  # Annualized

        # Simple thresholds (would be more sophisticated in practice)
        if volatility > 0.3:  # 30% annualized
            return "high"
        elif volatility < 0.15:  # 15% annualized
            return "low"
        else:
            return "normal"

    def _classify_trend_regime(
        self, data: list[PriceData], indicators: TechnicalIndicators
    ) -> str:
        """Classify current trend regime."""
        if len(data) < 20:
            return "sideways"

        current_price = data[-1].close

        # Use SMA slopes for trend detection
        if indicators.sma_5 > indicators.sma_20 > indicators.sma_50:
            if current_price > indicators.sma_5:
                return "up"
        elif indicators.sma_5 < indicators.sma_20 < indicators.sma_50:
            if current_price < indicators.sma_5:
                return "down"

        return "sideways"

    def _estimate_bid_ask_spread(self, price_data: PriceData) -> float:
        """Estimate bid-ask spread (simplified)."""
        # Simple estimation based on high-low range
        if price_data.high == price_data.low:
            return 0.01  # Minimum spread

        range_pct = (price_data.high - price_data.low) / price_data.close
        return min(0.05, range_pct * 0.3)  # Cap at 5%

    def _estimate_order_flow_imbalance(self, data: list[PriceData]) -> float:
        """Estimate order flow imbalance (simplified)."""
        if len(data) < 2:
            return 0.0

        # Use volume and price change as proxy
        latest = data[-1]
        prev = data[-2]

        price_change = latest.close - prev.close
        volume_ratio = latest.volume / max(1, prev.volume)

        # Positive imbalance = buying pressure
        if price_change > 0:
            return min(1.0, volume_ratio - 1.0)
        elif price_change < 0:
            return max(-1.0, -(volume_ratio - 1.0))
        else:
            return 0.0

    def _compute_spy_correlation(self, symbol: str, data: list[PriceData]) -> float:
        """Compute correlation with SPY (simplified)."""
        if symbol == "SPY" or symbol.startswith("^"):
            return 1.0

        # Simplified: assume moderate correlation for stocks
        if len(data) >= 20:
            return 0.7  # Default stock correlation with market
        return 0.0

    def _compute_sector_momentum(self, symbol: str, data: list[PriceData]) -> float:
        """Compute sector momentum (simplified)."""
        if len(data) < 5:
            return 0.0

        # Simple momentum based on recent price action
        recent_change = (data[-1].close - data[-5].close) / data[-5].close
        return max(-1.0, min(1.0, recent_change * 10))  # Scale to [-1, 1]


# Global feature computer instance
feature_computer = FeatureComputer()


async def compute_features_async(symbol: str) -> MarketFeatures | None:
    """
    Async-safe wrapper for feature computation.

    Offloads blocking computation to executor to prevent event loop blocking.

    Args:
        symbol: Symbol to compute features for

    Returns:
        MarketFeatures object or None if insufficient data
    """
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, feature_computer.compute_features, symbol)
