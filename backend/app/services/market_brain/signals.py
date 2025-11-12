"""
Trading Signal Generation Module

Pure functions that read features + regime → emit signal objects.

Signal strategies implemented:
1. MeanReversion: Long when oversold, short when overbought
2. Momentum: Long on breakouts with trend confirmation
3. RegimeFilter: Filters signals based on market regime

All signals include confidence scores and detailed reasoning.
Enhanced with decision context for improved decision-making.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .features import get_ticker_features
from .regime import RegimeResult, RegimeState, get_regime_state


logger = logging.getLogger(__name__)


class SignalDirection(Enum):
    """Signal direction types."""

    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class SignalType(Enum):
    """Signal generation strategy types."""

    MEAN_REVERSION = "MeanReversion"
    MOMENTUM = "Momentum"
    REGIME_FILTER = "RegimeFilter"
    COMBINED = "Combined"


@dataclass
class Signal:
    """
    Trading signal object with confidence and reasoning.

    Attributes:
        ticker: Stock symbol
        direction: LONG/SHORT/FLAT
        confidence: 0-1 probability of success (calibrated)
        signal_type: Strategy that generated signal
        reason: Human-readable explanation
        entry_price: Suggested entry price
        stop_loss: Suggested stop loss level
        take_profit: Suggested take profit level
        time_horizon: Expected holding period
        regime_context: Market regime when generated
        features_snapshot: Key features used in decision
        raw_confidence: Original confidence before calibration
        confidence_adjustment: Amount of calibration adjustment
        decision_quality: Quality indicators from historical performance
        similar_outcomes: Summary of similar past decisions
    """

    ticker: str
    direction: SignalDirection
    confidence: float
    signal_type: SignalType
    reason: str

    # Price levels
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None

    # Context
    timestamp: datetime | None = None
    time_horizon: str | None = None  # "1D", "3D", "1W", etc.
    regime_context: str | None = None
    features_snapshot: dict[str, Any] | None = None

    # Metadata
    expected_return: float | None = None  # Expected % return
    risk_reward_ratio: float | None = None

    # Enhanced decision context (new fields)
    raw_confidence: float | None = None  # Original confidence before calibration
    confidence_adjustment: float | None = None  # How much calibration changed it
    decision_quality: dict[str, Any] = field(default_factory=dict)  # Quality metrics
    similar_outcomes: dict[str, Any] = field(default_factory=dict)  # Similar past decisions
    lessons_learned: list[str] = field(default_factory=list)  # Key insights

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else None
        return {
            "ticker": self.ticker,
            "direction": self.direction.value,
            "confidence": self.confidence,
            "signal_type": self.signal_type.value,
            "reason": self.reason,
            "price_levels": {
                "entry": self.entry_price,
                "stop_loss": self.stop_loss,
                "take_profit": self.take_profit,
            },
            "context": {
                "timestamp": ts,
                "time_horizon": self.time_horizon,
                "regime_context": self.regime_context,
                "expected_return": self.expected_return,
                "risk_reward_ratio": self.risk_reward_ratio,
            },
            "features_snapshot": self.features_snapshot,
            "decision_context": {
                "raw_confidence": self.raw_confidence,
                "confidence_adjustment": self.confidence_adjustment,
                "decision_quality": self.decision_quality,
                "similar_outcomes": self.similar_outcomes,
                "lessons_learned": self.lessons_learned,
            },
        }


class SignalGenerator:
    """
    Generates trading signals using rule-based strategies.

    Combines multiple signal types with regime filtering for robust
    signal generation with explainable logic.
    """

    def __init__(self):
        # Signal generation parameters
        self.params = {
            # Mean reversion thresholds
            "mr_rsi_oversold": 30,
            "mr_rsi_overbought": 70,
            "mr_z_score_long": -1.5,
            "mr_z_score_short": 1.5,
            # Momentum thresholds
            "mom_breakout_periods": 20,
            "mom_volume_multiplier": 1.5,
            "mom_trend_strength": 0.5,
            # Risk management
            "stop_loss_atr_multiple": 2.0,
            "take_profit_atr_multiple": 3.0,
            "max_holding_days": 5,
        }

        # Historical win rates for calibration (simplified)
        self.win_rates = {
            SignalType.MEAN_REVERSION: {
                RegimeState.CHOP: 0.65,
                RegimeState.RISK_ON: 0.60,
                RegimeState.RISK_OFF: 0.55,
                RegimeState.PANIC: 0.45,
            },
            SignalType.MOMENTUM: {
                RegimeState.RISK_ON: 0.70,
                RegimeState.CHOP: 0.55,
                RegimeState.RISK_OFF: 0.45,
                RegimeState.PANIC: 0.30,
            },
        }

    def generate_signal(self, ticker: str, regime: RegimeResult | None = None) -> dict:
        """
        Generate trading signal for a ticker.

        Args:
            ticker: Stock symbol
            regime: Current market regime (fetched if not provided)

        Returns:
            dict: {"ticker": ..., "signal": Signal or None, "reason": ...}
            If features are missing/invalid, returns {"ticker": ..., "signal": None, "reason": "insufficient_features"}
        """
        try:
            # Get features and regime
            features = get_ticker_features(ticker)
            # Defensive: handle None, status dict, or missing keys
            if (
                features is None
                or (isinstance(features, dict) and features.get("status") == "insufficient_data")
                or not isinstance(features, dict)
            ):
                logger.warning(f"[SIGNALS] Skipping {ticker}: insufficient/invalid features")
                return {"ticker": ticker, "signal": None, "reason": "insufficient_features"}

            # List required features for signal generation
            required_keys = [
                "rsi_14",
                "z_score_20",
                "close",
                "atr_14",
                "sma_20",
                "sma_50",
                "slope_20d",
                "new_high_20d",
            ]
            missing = [k for k in required_keys if k not in features or features[k] is None]
            if missing:
                logger.warning(f"[SIGNALS] Skipping {ticker}: missing features {missing}")
                return {"ticker": ticker, "signal": None, "reason": f"missing_features: {missing}"}

            if regime is None:
                regime = get_regime_state()

            # Generate signals from different strategies
            signals: list[Signal] = []

            # Mean reversion signal
            mr_signal = self._generate_mean_reversion_signal_dict(features, regime)
            if mr_signal:
                signals.append(mr_signal)

            # Momentum signal
            mom_signal = self._generate_momentum_signal_dict(features, regime)
            if mom_signal:
                signals.append(mom_signal)

            # Combine signals if multiple exist
            if len(signals) == 0:
                return {"ticker": ticker, "signal": None, "reason": "no_trade_edge"}
            elif len(signals) == 1:
                final_signal = signals[0]
            else:
                final_signal = self._combine_signals_dict(signals, features, regime)

            # Enrich signal with decision context (confidence calibration + historical insights)
            final_signal = self._enrich_signal_with_context(final_signal, features)

            return {"ticker": ticker, "signal": final_signal, "reason": "ok"}

        except Exception as e:
            logger.error(f"Error generating signal for {ticker}: {e}")
            return {"ticker": ticker, "signal": None, "reason": f"error: {e!s}"}

    def _generate_mean_reversion_signal_dict(
        self, features: dict[str, Any], regime: RegimeResult
    ) -> Signal | None:
        """Generate mean reversion signal."""

        # Check if regime supports mean reversion
        if regime.regime == RegimeState.PANIC:
            return None  # No mean reversion in panic

        signal_direction = SignalDirection.FLAT
        confidence = 0.0
        reasons = []

        # Long signal conditions
        if (
            features["rsi_14"] < self.params["mr_rsi_oversold"]
            and features["z_score_20"] < self.params["mr_z_score_long"]
        ):
            signal_direction = SignalDirection.LONG
            reasons.append(
                f"RSI {features['rsi_14']:.1f} oversold (< {self.params['mr_rsi_oversold']})"
            )
            reasons.append(
                f"Z-score {features['z_score_20']:.2f} below {self.params['mr_z_score_long']}"
            )

            # Confidence based on regime
            base_confidence = self.win_rates[SignalType.MEAN_REVERSION].get(regime.regime, 0.5)

            # Adjust based on signal strength
            rsi_strength = (self.params["mr_rsi_oversold"] - features["rsi_14"]) / self.params[
                "mr_rsi_oversold"
            ]
            z_strength = abs(features["z_score_20"]) / 2.0  # Normalize to 0-1

            confidence = base_confidence * (0.5 + 0.25 * rsi_strength + 0.25 * z_strength)
            confidence = min(confidence, 0.95)  # Cap at 95%

        # Short signal conditions (only in risk-on or chop)
        elif (
            regime.regime in [RegimeState.RISK_ON, RegimeState.CHOP]
            and features["rsi_14"] > self.params["mr_rsi_overbought"]
            and features["z_score_20"] > self.params["mr_z_score_short"]
        ):
            signal_direction = SignalDirection.SHORT
            reasons.append(
                f"RSI {features['rsi_14']:.1f} overbought (> {self.params['mr_rsi_overbought']})"
            )
            reasons.append(
                f"Z-score {features['z_score_20']:.2f} above {self.params['mr_z_score_short']}"
            )

            base_confidence = self.win_rates[SignalType.MEAN_REVERSION].get(regime.regime, 0.5)
            confidence = base_confidence * 0.8  # Lower confidence for shorts

        if signal_direction == SignalDirection.FLAT:
            return None

        # Calculate price levels
        entry_price = features["close"]
        stop_loss, take_profit = self._calculate_price_levels(
            entry_price, features["atr_14"], signal_direction
        )

        return Signal(
            ticker=features["ticker"],
            direction=signal_direction,
            confidence=confidence,
            signal_type=SignalType.MEAN_REVERSION,
            reason=f"Mean reversion: {'; '.join(reasons)}",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            time_horizon="3D",
            regime_context=regime.regime.value,
            features_snapshot={
                "rsi_14": features["rsi_14"],
                "z_score_20": features["z_score_20"],
                "close": features["close"],
                "atr_14": features["atr_14"],
            },
        )

    def _generate_momentum_signal_dict(
        self, features: dict[str, Any], regime: RegimeResult
    ) -> Signal | None:
        """Generate momentum signal."""

        # Momentum works best in risk-on regime
        if regime.regime not in [RegimeState.RISK_ON, RegimeState.CHOP]:
            return None

        signal_direction = SignalDirection.FLAT
        confidence = 0.0
        reasons = []

        # Long momentum conditions
        if (
            features["new_high_20d"]
            and features["close"] > features["sma_20"]
            and features["sma_20"] > features["sma_50"]
            and features["slope_20d"] > self.params["mom_trend_strength"]
        ):
            signal_direction = SignalDirection.LONG
            reasons.append(f"New 20-day high at {features['close']:.2f}")
            reasons.append(f"Price above 20D SMA ({features['sma_20']:.2f})")
            reasons.append(f"20D SMA above 50D SMA ({features['sma_50']:.2f})")
            reasons.append(f"Strong uptrend: {features['slope_20d']:.2f}% slope")

            # Higher confidence in risk-on regime
            base_confidence = self.win_rates[SignalType.MOMENTUM].get(regime.regime, 0.5)

            # Adjust for trend strength
            trend_strength = min(features["slope_20d"] / 2.0, 1.0)  # Normalize
            confidence = base_confidence * (0.7 + 0.3 * trend_strength)

        # No short momentum signals in this simple version

        if signal_direction == SignalDirection.FLAT:
            return None

        # Calculate price levels
        entry_price = features["close"]
        stop_loss, take_profit = self._calculate_price_levels(
            entry_price, features["atr_14"], signal_direction
        )

        return Signal(
            ticker=features["ticker"],
            direction=signal_direction,
            confidence=confidence,
            signal_type=SignalType.MOMENTUM,
            reason=f"Momentum breakout: {'; '.join(reasons)}",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            time_horizon="5D",
            regime_context=regime.regime.value,
            features_snapshot={
                "close": features["close"],
                "sma_20": features["sma_20"],
                "sma_50": features["sma_50"],
                "slope_20d": features["slope_20d"],
                "new_high_20d": features["new_high_20d"],
                "atr_14": features["atr_14"],
            },
        )

    def _combine_signals_dict(
        self, signals: list[Signal], features: dict[str, Any], regime: RegimeResult
    ) -> Signal:
        """Combine multiple signals into one."""

        # Simple combination: take highest confidence signal
        best_signal = max(signals, key=lambda s: s.confidence)

        # Boost confidence if multiple signals agree
        same_direction = [s for s in signals if s.direction == best_signal.direction]
        if len(same_direction) > 1:
            confidence_boost = 0.1 * (len(same_direction) - 1)
            best_signal.confidence = min(best_signal.confidence + confidence_boost, 0.95)

            # Update reason to reflect combination
            signal_types = [s.signal_type.value for s in same_direction]
            best_signal.reason = (
                f"Combined signal ({', '.join(signal_types)}): {best_signal.reason}"
            )
            best_signal.signal_type = SignalType.COMBINED

        return best_signal

    def _calculate_price_levels(
        self, entry_price: float, atr: float, direction: SignalDirection
    ) -> tuple[float, float]:
        """Calculate stop loss and take profit levels."""

        if direction == SignalDirection.LONG:
            stop_loss = entry_price - (atr * self.params["stop_loss_atr_multiple"])
            take_profit = entry_price + (atr * self.params["take_profit_atr_multiple"])
        else:  # SHORT
            stop_loss = entry_price + (atr * self.params["stop_loss_atr_multiple"])
            take_profit = entry_price - (atr * self.params["take_profit_atr_multiple"])

        return stop_loss, take_profit

    def _enrich_signal_with_context(self, signal: Signal, features: dict[str, Any]) -> Signal:
        """
        Enrich signal with decision context for improved decision-making.

        This applies confidence calibration based on historical performance
        and adds context from similar past decisions.
        """
        try:
            # Lazy import to avoid circular dependencies
            from ..decision_context import enrich_decision

            # Store raw confidence before calibration
            signal.raw_confidence = signal.confidence

            # Get enriched decision context
            context = enrich_decision(
                ticker=signal.ticker,
                signal_type=signal.signal_type.value,
                regime=signal.regime_context or "Unknown",
                raw_confidence=signal.confidence,
                features=features,
            )

            # Update signal with calibrated confidence
            signal.confidence = context.calibrated_confidence
            signal.confidence_adjustment = context.confidence_adjustment

            # Add decision quality indicators
            signal.decision_quality = {
                "expected_accuracy": context.expected_accuracy,
                "reliability_score": context.reliability_score,
                "historical_win_rate": (
                    context.historical_performance.win_rate
                    if context.historical_performance
                    else None
                ),
                "historical_sample_size": (
                    context.historical_performance.total_signals
                    if context.historical_performance
                    else 0
                ),
            }

            # Add similar outcomes summary
            signal.similar_outcomes = context.similar_decisions_summary

            # Add lessons learned
            signal.lessons_learned = context.lessons_learned

            # Update reason to include calibration info
            if signal.confidence_adjustment and abs(signal.confidence_adjustment) > 0.05:
                adjustment_str = (
                    f"increased by {signal.confidence_adjustment:.1%}"
                    if signal.confidence_adjustment > 0
                    else f"decreased by {abs(signal.confidence_adjustment):.1%}"
                )
                signal.reason += f" | Confidence {adjustment_str} based on historical performance"

            return signal

        except Exception as e:
            # If enrichment fails, return signal as-is
            logger.warning(f"Failed to enrich signal with context: {e}")
            return signal

    def generate_signals_bulk(self, tickers: list[str]) -> dict[str, dict]:
        """Generate signals for multiple tickers."""
        regime = get_regime_state()  # Get once for all tickers

        results = {}
        for ticker in tickers:
            results[ticker] = self.generate_signal(ticker, regime)

        return results

    def update_parameters(self, new_params: dict[str, Any]):
        """Update signal generation parameters."""
        self.params.update(new_params)

    def get_signal_explanation(self, signal: Signal) -> dict[str, Any]:
        """Get detailed explanation of signal logic."""
        risk_amount = (
            abs(signal.entry_price - signal.stop_loss)
            if (signal.entry_price is not None and signal.stop_loss is not None)
            else None
        )
        reward_amount = (
            abs(signal.take_profit - signal.entry_price)
            if (signal.entry_price is not None and signal.take_profit is not None)
            else None
        )
        return {
            "signal_type": signal.signal_type.value,
            "direction": signal.direction.value,
            "confidence": signal.confidence,
            "regime_context": signal.regime_context,
            "reason": signal.reason,
            "features_used": signal.features_snapshot,
            "price_levels": {
                "entry": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
            },
            "risk_metrics": {
                "risk_amount": risk_amount,
                "reward_amount": reward_amount,
                "risk_reward_ratio": signal.risk_reward_ratio,
            },
        }


# Global signal generator instance
signal_generator = SignalGenerator()


def generate_ticker_signal(ticker: str) -> dict:
    """Convenience function to generate signal for a ticker."""
    return signal_generator.generate_signal(ticker)


def generate_signals_for_watchlist(tickers: list[str]) -> dict[str, dict]:
    """Generate signals for a list of tickers."""
    return signal_generator.generate_signals_bulk(tickers)


async def generate_ticker_signal_async(ticker: str) -> dict:
    """
    Async-safe wrapper for signal generation.

    Offloads blocking signal computation to executor to prevent event loop blocking.

    Args:
        ticker: Stock symbol

    Returns:
        Signal dictionary
    """
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, generate_ticker_signal, ticker)


async def generate_signals_for_watchlist_async(tickers: list[str]) -> dict[str, dict]:
    """
    Async-safe wrapper for bulk signal generation.

    Offloads blocking signal computation to executor to prevent event loop blocking.

    Args:
        tickers: List of stock symbols

    Returns:
        Dictionary mapping ticker to signal dictionary
    """
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, generate_signals_for_watchlist, tickers)
