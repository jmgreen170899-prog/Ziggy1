"""
Market Regime Detection Module

Implements a simple, explainable regime detector with 4 market states:
- Panic: High fear, major selloffs
- RiskOff: Cautious, defensive positioning
- Chop: Sideways, unclear direction
- RiskOn: Risk appetite, trending up

Logic is rule-based and interpretable for debugging and validation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .features import FeatureSet


# Note: FeatureComputer not available in this module currently
# from .features import FeatureComputer


logger = logging.getLogger(__name__)


class RegimeState(Enum):
    """Market regime states in order of risk appetite."""

    PANIC = "Panic"
    RISK_OFF = "RiskOff"
    CHOP = "Chop"
    RISK_ON = "RiskOn"


@dataclass
class RegimeMetrics:
    """Supporting metrics for regime determination."""

    vix_level: float | None
    spy_change_1d: float | None
    breadth_50dma: float | None
    spy_slope_20d: float | None
    spy_vs_sma20: float | None
    spy_vs_sma50: float | None

    # Rule triggers
    panic_triggered: bool = False
    risk_off_triggered: bool = False
    risk_on_triggered: bool = False

    # Confidence score (0-1)
    confidence: float = 0.0

    # Rule explanations
    reasons: list = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


@dataclass
class RegimeResult:
    """Complete regime detection result."""

    regime: RegimeState
    confidence: float
    timestamp: datetime
    metrics: RegimeMetrics
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "explanation": self.explanation,
            "metrics": {
                "vix_level": self.metrics.vix_level,
                "spy_change_1d": self.metrics.spy_change_1d,
                "breadth_50dma": self.metrics.breadth_50dma,
                "spy_slope_20d": self.metrics.spy_slope_20d,
                "spy_vs_sma20": self.metrics.spy_vs_sma20,
                "spy_vs_sma50": self.metrics.spy_vs_sma50,
                "rule_triggers": {
                    "panic": self.metrics.panic_triggered,
                    "risk_off": self.metrics.risk_off_triggered,
                    "risk_on": self.metrics.risk_on_triggered,
                },
                "reasons": self.metrics.reasons,
            },
        }


class RegimeDetector:
    """
    Market regime detector using rule-based logic.

    Regime Rules:
    1. Panic: VIX > 30 OR SPY 1-day < -3%
    2. RiskOff: breadth < 40% AND 20D slope < 0
    3. RiskOn: breadth > 60% AND 20D slope > 0
    4. Chop: Everything else

    Rules are hierarchical - Panic overrides everything, then RiskOff/RiskOn.
    """

    def __init__(self, feature_computer=None):
        # Note: FeatureComputer not available in this module currently
        # self.feature_computer = feature_computer or FeatureComputer()
        self.feature_computer = feature_computer
        self._last_regime_cache: tuple[RegimeResult, datetime] | None = None
        self.cache_ttl = timedelta(minutes=1)  # Cache regime for 1 minute

        # Regime thresholds (configurable)
        self.thresholds = {
            "vix_panic": 30.0,
            "spy_panic_change": -3.0,
            "breadth_risk_off": 40.0,
            "breadth_risk_on": 60.0,
            "slope_threshold": 0.0,
        }

    def detect_regime(self, force_refresh: bool = False) -> RegimeResult:
        """
        Detect current market regime.

        Args:
            force_refresh: Skip cache and recompute

        Returns:
            RegimeResult with regime state and supporting metrics
        """

        # Check cache first
        if not force_refresh and self._last_regime_cache:
            result, cache_time = self._last_regime_cache
            if datetime.now() - cache_time < self.cache_ttl:
                return result

        try:
            # Get market features
            if not self.feature_computer:
                # Return default if no feature computer available
                return self._create_default_regime()

            spy_features = self.feature_computer.get_features("SPY", force_refresh)
            if not spy_features:
                # Return default if no data
                return self._create_default_regime()

            # Extract key metrics
            metrics = self._extract_metrics(spy_features)

            # Apply regime rules
            regime_result = self._apply_regime_rules(metrics)

            # Cache result
            self._last_regime_cache = (regime_result, datetime.now())

            return regime_result

        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return self._create_default_regime()

    def _extract_metrics(self, spy_features: FeatureSet) -> RegimeMetrics:
        """Extract key metrics from SPY features."""

        # Calculate relative position vs moving averages
        spy_vs_sma20 = ((spy_features.close / spy_features.sma_20) - 1) * 100
        spy_vs_sma50 = ((spy_features.close / spy_features.sma_50) - 1) * 100

        return RegimeMetrics(
            vix_level=spy_features.vix_level,
            spy_change_1d=spy_features.price_change_1d,
            breadth_50dma=spy_features.breadth_50dma,
            spy_slope_20d=spy_features.slope_20d,
            spy_vs_sma20=spy_vs_sma20,
            spy_vs_sma50=spy_vs_sma50,
        )

    def _apply_regime_rules(self, metrics: RegimeMetrics) -> RegimeResult:
        """Apply hierarchical regime rules."""

        reasons = []
        confidence = 0.0
        regime = RegimeState.CHOP  # Default

        # Rule 1: Panic (highest priority)
        panic_vix = metrics.vix_level and metrics.vix_level > self.thresholds["vix_panic"]
        panic_spy = (
            metrics.spy_change_1d and metrics.spy_change_1d < self.thresholds["spy_panic_change"]
        )

        if panic_vix or panic_spy:
            regime = RegimeState.PANIC
            metrics.panic_triggered = True
            confidence = 0.9  # High confidence for panic signals

            if panic_vix:
                reasons.append(f"VIX at {metrics.vix_level:.1f} > {self.thresholds['vix_panic']}")
            if panic_spy:
                reasons.append(
                    f"SPY 1-day change {metrics.spy_change_1d:.1f}% < {self.thresholds['spy_panic_change']}%"
                )

        # Rule 2: RiskOff (second priority)
        elif (
            metrics.breadth_50dma
            and metrics.breadth_50dma < self.thresholds["breadth_risk_off"]
            and metrics.spy_slope_20d
            and metrics.spy_slope_20d < self.thresholds["slope_threshold"]
        ):
            regime = RegimeState.RISK_OFF
            metrics.risk_off_triggered = True
            confidence = 0.75

            reasons.append(
                f"Market breadth {metrics.breadth_50dma:.1f}% < {self.thresholds['breadth_risk_off']}%"
            )
            reasons.append(f"20-day slope {metrics.spy_slope_20d:.2f}% negative")

        # Rule 3: RiskOn (third priority)
        elif (
            metrics.breadth_50dma
            and metrics.breadth_50dma > self.thresholds["breadth_risk_on"]
            and metrics.spy_slope_20d
            and metrics.spy_slope_20d > self.thresholds["slope_threshold"]
        ):
            regime = RegimeState.RISK_ON
            metrics.risk_on_triggered = True
            confidence = 0.75

            reasons.append(
                f"Market breadth {metrics.breadth_50dma:.1f}% > {self.thresholds['breadth_risk_on']}%"
            )
            reasons.append(f"20-day slope {metrics.spy_slope_20d:.2f}% positive")

        # Rule 4: Chop (default)
        else:
            regime = RegimeState.CHOP
            confidence = 0.6  # Moderate confidence for default state
            reasons.append("No clear directional signals - sideways market")

            # Add context for why it's chop
            if metrics.breadth_50dma:
                reasons.append(f"Breadth at {metrics.breadth_50dma:.1f}% (neutral zone)")
            if metrics.spy_slope_20d:
                reasons.append(f"20-day slope {metrics.spy_slope_20d:.2f}% (low momentum)")

        # Store reasons in metrics
        metrics.reasons = reasons
        metrics.confidence = confidence

        # Create explanation
        explanation = f"{regime.value}: " + "; ".join(reasons)

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            timestamp=datetime.now(),
            metrics=metrics,
            explanation=explanation,
        )

    def _create_default_regime(self) -> RegimeResult:
        """Create default regime when data is unavailable."""
        metrics = RegimeMetrics(
            vix_level=None,
            spy_change_1d=None,
            breadth_50dma=None,
            spy_slope_20d=None,
            spy_vs_sma20=None,
            spy_vs_sma50=None,
            reasons=["Insufficient market data available"],
        )

        return RegimeResult(
            regime=RegimeState.CHOP,
            confidence=0.3,  # Low confidence without data
            timestamp=datetime.now(),
            metrics=metrics,
            explanation="Chop: Default regime due to insufficient data",
        )

    def get_regime_history(self, days: int = 5) -> list:
        """Get regime history for backtesting (simplified)."""
        # This would typically query a database of historical regimes
        # For now, return current regime as placeholder
        current = self.detect_regime()
        return [current.to_dict()]

    def update_thresholds(self, new_thresholds: dict[str, float]):
        """Update regime detection thresholds."""
        self.thresholds.update(new_thresholds)
        # Clear cache when thresholds change
        self._last_regime_cache = None


# Global detector instance
regime_detector = RegimeDetector()


def get_regime_state(force_refresh: bool = False) -> RegimeResult:
    """
    Convenience function to get current market regime.

    Args:
        force_refresh: Skip cache and recompute

    Returns:
        RegimeResult with current market regime and metrics
    """
    return regime_detector.detect_regime(force_refresh)


def get_regime_string() -> str:
    """Get just the regime name as string."""
    return get_regime_state().regime.value


def is_risk_regime() -> bool:
    """Check if current regime supports risk-taking."""
    regime = get_regime_state().regime
    return regime in [RegimeState.RISK_ON, RegimeState.CHOP]


def is_defensive_regime() -> bool:
    """Check if current regime suggests defensive positioning."""
    regime = get_regime_state().regime
    return regime in [RegimeState.PANIC, RegimeState.RISK_OFF]
