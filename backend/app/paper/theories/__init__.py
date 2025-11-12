"""
Trading theories registry for ZiggyAI paper trading lab.

This module provides a plug-in interface for trading strategies/hypotheses
and includes starter implementations for common patterns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.paper.engine import Signal


@dataclass
class MarketFeatures:
    """Market feature set for theory evaluation."""

    symbol: str
    timestamp: datetime

    # Price features
    price: float
    open_price: float
    high: float
    low: float
    volume: int

    # Technical indicators
    sma_5: float = 0.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    rsi: float = 50.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    atr: float = 0.0

    # Volatility and regime
    vol_regime: str = "normal"  # low, normal, high
    trend_regime: str = "sideways"  # up, down, sideways

    # Market microstructure
    bid_ask_spread: float = 0.0
    order_flow_imbalance: float = 0.0

    # News/sentiment
    news_sentiment: float = 0.0  # -1 to 1
    news_urgency: float = 0.0  # 0 to 1

    # Cross-asset signals
    spy_correlation: float = 0.0
    sector_momentum: float = 0.0


class Theory(ABC):
    """
    Abstract base class for trading theories.

    Each theory implements:
    1. Signal generation based on market features
    2. Risk model for position sizing
    3. Theory-specific metadata and description
    """

    def __init__(self, theory_id: str):
        self.theory_id = theory_id
        self.enabled = True
        self.last_signal_time: datetime | None = None
        self.signal_count = 0

    @abstractmethod
    def describe(self) -> dict[str, Any]:
        """Return theory description and parameters."""
        pass

    @abstractmethod
    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        """
        Generate trading signals based on market features.

        Args:
            features: Current market features

        Returns:
            List of trading signals (can be empty)
        """
        pass

    @abstractmethod
    def risk_model(self, features: MarketFeatures) -> float:
        """
        Calculate position size multiplier based on features.

        Args:
            features: Current market features

        Returns:
            Position size multiplier (0.0 to 1.0)
        """
        pass

    def update_state(self, signal: Signal, outcome: dict[str, Any] | None = None) -> None:
        """
        Update theory state based on signal outcome.

        Args:
            signal: Signal that was generated
            outcome: Optional outcome data (PnL, etc.)
        """
        self.signal_count += 1
        self.last_signal_time = signal.timestamp


class MeanReversionTheory(Theory):
    """
    Mean reversion theory based on RSI and Bollinger Bands.

    Generates signals when price is oversold/overbought relative to recent range.
    """

    def __init__(
        self,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        bb_threshold: float = 0.02,
        min_volume_ratio: float = 1.2,
    ):
        super().__init__("mean_revert")
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_threshold = bb_threshold
        self.min_volume_ratio = min_volume_ratio

    def describe(self) -> dict[str, Any]:
        return {
            "name": "Mean Reversion",
            "description": "RSI and Bollinger Band mean reversion strategy",
            "parameters": {
                "rsi_oversold": self.rsi_oversold,
                "rsi_overbought": self.rsi_overbought,
                "bb_threshold": self.bb_threshold,
                "min_volume_ratio": self.min_volume_ratio,
            },
            "horizons": [5, 15, 30],
            "typical_hold_time_mins": 15,
        }

    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        signals = []

        # Check for oversold condition (BUY signal)
        if features.rsi <= self.rsi_oversold and features.price <= features.bollinger_lower * (
            1 + self.bb_threshold
        ):
            confidence = min(1.0, (self.rsi_oversold - features.rsi) / 10.0)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="BUY",
                confidence=confidence,
                horizon_mins=15,
                features={
                    "rsi": features.rsi,
                    "price_vs_bb_lower": features.price / features.bollinger_lower,
                    "volume_ratio": 1.0,  # TODO: Calculate from data
                    "signal_type": "oversold",
                },
            )
            signals.append(signal)

        # Check for overbought condition (SELL signal)
        elif features.rsi >= self.rsi_overbought and features.price >= features.bollinger_upper * (
            1 - self.bb_threshold
        ):
            confidence = min(1.0, (features.rsi - self.rsi_overbought) / 10.0)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="SELL",
                confidence=confidence,
                horizon_mins=15,
                features={
                    "rsi": features.rsi,
                    "price_vs_bb_upper": features.price / features.bollinger_upper,
                    "volume_ratio": 1.0,
                    "signal_type": "overbought",
                },
            )
            signals.append(signal)

        return signals

    def risk_model(self, features: MarketFeatures) -> float:
        """Position size based on volatility and regime."""
        base_size = 1.0

        # Reduce size in high volatility
        if features.vol_regime == "high":
            base_size *= 0.5
        elif features.vol_regime == "low":
            base_size *= 1.2

        # Reduce size during strong trends (counter-trend is risky)
        if features.trend_regime in ["up", "down"]:
            base_size *= 0.7

        return min(1.0, base_size)


class BreakoutTheory(Theory):
    """
    Breakout theory based on price levels and volume confirmation.

    Generates signals when price breaks through significant levels with volume.
    """

    def __init__(
        self,
        breakout_threshold: float = 0.02,
        volume_multiplier: float = 1.5,
        atr_multiplier: float = 2.0,
    ):
        super().__init__("breakout")
        self.breakout_threshold = breakout_threshold
        self.volume_multiplier = volume_multiplier
        self.atr_multiplier = atr_multiplier

    def describe(self) -> dict[str, Any]:
        return {
            "name": "Breakout",
            "description": "Price and volume breakout strategy",
            "parameters": {
                "breakout_threshold": self.breakout_threshold,
                "volume_multiplier": self.volume_multiplier,
                "atr_multiplier": self.atr_multiplier,
            },
            "horizons": [5, 15, 60],
            "typical_hold_time_mins": 30,
        }

    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        signals = []

        # Simple breakout detection (would be more sophisticated in practice)
        sma_20 = features.sma_20
        if sma_20 <= 0:
            return signals

        # Upside breakout
        if (
            features.price > sma_20 * (1 + self.breakout_threshold) and features.volume > 0
        ):  # Volume check placeholder
            confidence = min(1.0, (features.price - sma_20) / sma_20 / self.breakout_threshold)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="BUY",
                confidence=confidence,
                horizon_mins=30,
                features={
                    "breakout_level": sma_20,
                    "breakout_magnitude": (features.price - sma_20) / sma_20,
                    "volume": features.volume,
                    "signal_type": "upside_breakout",
                },
            )
            signals.append(signal)

        # Downside breakout
        elif features.price < sma_20 * (1 - self.breakout_threshold) and features.volume > 0:
            confidence = min(1.0, (sma_20 - features.price) / sma_20 / self.breakout_threshold)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="SELL",
                confidence=confidence,
                horizon_mins=30,
                features={
                    "breakout_level": sma_20,
                    "breakout_magnitude": (sma_20 - features.price) / sma_20,
                    "volume": features.volume,
                    "signal_type": "downside_breakout",
                },
            )
            signals.append(signal)

        return signals

    def risk_model(self, features: MarketFeatures) -> float:
        """Position size based on ATR and trend strength."""
        base_size = 1.0

        # Increase size in trending markets
        if features.trend_regime in ["up", "down"]:
            base_size *= 1.3

        # Adjust for volatility
        if features.atr > 0:
            # Higher ATR = lower position size
            atr_factor = min(2.0, features.atr / (features.price * 0.02))
            base_size /= atr_factor

        return min(1.0, base_size)


class NewsShockGuardTheory(Theory):
    """
    News shock guard theory - protective selling during negative news events.

    Generates defensive signals when negative news sentiment spikes.
    """

    def __init__(
        self,
        sentiment_threshold: float = -0.5,
        urgency_threshold: float = 0.7,
        volatility_amplifier: float = 1.5,
    ):
        super().__init__("news_shock_guard")
        self.sentiment_threshold = sentiment_threshold
        self.urgency_threshold = urgency_threshold
        self.volatility_amplifier = volatility_amplifier

    def describe(self) -> dict[str, Any]:
        return {
            "name": "News Shock Guard",
            "description": "Defensive strategy for negative news events",
            "parameters": {
                "sentiment_threshold": self.sentiment_threshold,
                "urgency_threshold": self.urgency_threshold,
                "volatility_amplifier": self.volatility_amplifier,
            },
            "horizons": [5, 10],
            "typical_hold_time_mins": 10,
        }

    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        signals = []

        # Defensive SELL signal on negative news
        if (
            features.news_sentiment <= self.sentiment_threshold
            and features.news_urgency >= self.urgency_threshold
        ):
            confidence = min(1.0, abs(features.news_sentiment) * features.news_urgency)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="SELL",
                confidence=confidence,
                horizon_mins=5,
                features={
                    "news_sentiment": features.news_sentiment,
                    "news_urgency": features.news_urgency,
                    "vol_regime": features.vol_regime,
                    "signal_type": "defensive_sell",
                },
            )
            signals.append(signal)

        return signals

    def risk_model(self, features: MarketFeatures) -> float:
        """Aggressive sizing during news events."""
        base_size = 1.0

        # Increase size for more urgent/negative news
        if features.news_urgency > self.urgency_threshold:
            base_size *= 1 + features.news_urgency

        # Increase size in high volatility (defensive trades benefit from vol)
        if features.vol_regime == "high":
            base_size *= self.volatility_amplifier

        return min(1.0, base_size)


class VolatilityRegimeTheory(Theory):
    """
    Volatility regime theory - trades based on volatility transitions.

    Generates signals when volatility regime changes.
    """

    def __init__(self, vol_breakout_threshold: float = 0.25, mean_revert_factor: float = 0.8):
        super().__init__("vol_regime")
        self.vol_breakout_threshold = vol_breakout_threshold
        self.mean_revert_factor = mean_revert_factor

    def describe(self) -> dict[str, Any]:
        return {
            "name": "Volatility Regime",
            "description": "Volatility regime transition strategy",
            "parameters": {
                "vol_breakout_threshold": self.vol_breakout_threshold,
                "mean_revert_factor": self.mean_revert_factor,
            },
            "horizons": [15, 60],
            "typical_hold_time_mins": 45,
        }

    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        signals = []

        # Long volatility trades when entering high vol regime
        if features.vol_regime == "high" and features.atr > 0:
            # Simplified: buy when volatility is increasing
            confidence = 0.7  # Fixed confidence for regime trades

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="BUY",  # Could be more sophisticated (straddles, etc.)
                confidence=confidence,
                horizon_mins=60,
                features={
                    "vol_regime": features.vol_regime,
                    "atr": features.atr,
                    "signal_type": "long_volatility",
                },
            )
            signals.append(signal)

        # Short volatility trades when entering low vol regime
        elif features.vol_regime == "low":
            confidence = 0.6

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="SELL",
                confidence=confidence,
                horizon_mins=60,
                features={
                    "vol_regime": features.vol_regime,
                    "atr": features.atr,
                    "signal_type": "short_volatility",
                },
            )
            signals.append(signal)

        return signals

    def risk_model(self, features: MarketFeatures) -> float:
        """Position size based on volatility regime stability."""
        base_size = 0.8  # Conservative for regime trades

        # Increase size when regime is clear
        if features.vol_regime in ["high", "low"]:
            base_size *= 1.2

        return min(1.0, base_size)


class IntradayMomentumTheory(Theory):
    """
    Intraday momentum theory - short-term price momentum trades.

    Generates signals based on short-term price momentum and volume.
    """

    def __init__(
        self,
        momentum_threshold: float = 0.01,
        lookback_minutes: int = 5,
        volume_confirmation: bool = True,
    ):
        super().__init__("intraday_momentum")
        self.momentum_threshold = momentum_threshold
        self.lookback_minutes = lookback_minutes
        self.volume_confirmation = volume_confirmation

    def describe(self) -> dict[str, Any]:
        return {
            "name": "Intraday Momentum",
            "description": "Short-term momentum strategy",
            "parameters": {
                "momentum_threshold": self.momentum_threshold,
                "lookback_minutes": self.lookback_minutes,
                "volume_confirmation": self.volume_confirmation,
            },
            "horizons": [5, 15],
            "typical_hold_time_mins": 8,
        }

    def generate_signals(self, features: MarketFeatures) -> list[Signal]:
        signals = []

        # Calculate momentum (simplified - would use proper price history)
        momentum = (features.price - features.sma_5) / features.sma_5 if features.sma_5 > 0 else 0

        # Upward momentum
        if momentum > self.momentum_threshold:
            confidence = min(1.0, momentum / self.momentum_threshold)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="BUY",
                confidence=confidence,
                horizon_mins=5,
                features={
                    "momentum": momentum,
                    "price": features.price,
                    "sma_5": features.sma_5,
                    "signal_type": "momentum_up",
                },
            )
            signals.append(signal)

        # Downward momentum
        elif momentum < -self.momentum_threshold:
            confidence = min(1.0, abs(momentum) / self.momentum_threshold)

            signal = Signal(
                theory_id=self.theory_id,
                symbol=features.symbol,
                side="SELL",
                confidence=confidence,
                horizon_mins=5,
                features={
                    "momentum": momentum,
                    "price": features.price,
                    "sma_5": features.sma_5,
                    "signal_type": "momentum_down",
                },
            )
            signals.append(signal)

        return signals

    def risk_model(self, features: MarketFeatures) -> float:
        """Position size based on momentum strength and trend alignment."""
        base_size = 1.0

        # Increase size when momentum aligns with trend
        momentum = (features.price - features.sma_5) / features.sma_5 if features.sma_5 > 0 else 0

        if (momentum > 0 and features.trend_regime == "up") or (
            momentum < 0 and features.trend_regime == "down"
        ):
            base_size *= 1.3

        # Reduce size in choppy/sideways markets
        if features.trend_regime == "sideways":
            base_size *= 0.7

        return min(1.0, base_size)


class TheoryRegistry:
    """Registry for managing trading theories."""

    def __init__(self):
        self.theories: dict[str, Theory] = {}
        self._register_default_theories()

    def _register_default_theories(self) -> None:
        """Register default theories."""
        self.register(MeanReversionTheory())
        self.register(BreakoutTheory())
        self.register(NewsShockGuardTheory())
        self.register(VolatilityRegimeTheory())
        self.register(IntradayMomentumTheory())

    def register(self, theory: Theory) -> None:
        """Register a theory."""
        self.theories[theory.theory_id] = theory

    def get(self, theory_id: str) -> Theory | None:
        """Get a theory by ID."""
        return self.theories.get(theory_id)

    def get_enabled(self) -> list[Theory]:
        """Get all enabled theories."""
        return [theory for theory in self.theories.values() if theory.enabled]

    def list_ids(self) -> list[str]:
        """Get list of theory IDs."""
        return list(self.theories.keys())

    def describe_all(self) -> dict[str, dict[str, Any]]:
        """Get descriptions of all theories."""
        return {theory_id: theory.describe() for theory_id, theory in self.theories.items()}

    def enable(self, theory_id: str) -> bool:
        """Enable a theory."""
        if theory_id in self.theories:
            self.theories[theory_id].enabled = True
            return True
        return False

    def disable(self, theory_id: str) -> bool:
        """Disable a theory."""
        if theory_id in self.theories:
            self.theories[theory_id].enabled = False
            return True
        return False


# Global registry instance
theory_registry = TheoryRegistry()
