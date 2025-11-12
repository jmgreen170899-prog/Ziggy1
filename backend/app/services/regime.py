"""
Regime Detection Module for ZiggyAI Cognitive Core

Detects market regimes based on volatility, liquidity, and macro conditions.
Provides regime labels and vector representations for model conditioning.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

# Regime definitions and thresholds
REGIME_THRESHOLDS = {
    "volatility": {"low": 0.15, "high": 0.35},
    "liquidity": {"low": 0.3, "high": 0.7},
    "vix": {"low": 15, "high": 30},
}

REGIME_VECTORS = {
    "base": [1.0, 0.0, 0.0, 0.0],
    "vol_hi_liq_lo": [0.0, 1.0, 0.0, 0.0],
    "vol_lo_liq_hi": [0.0, 0.0, 1.0, 0.0],
    "stress": [0.0, 0.0, 0.0, 1.0],
}


def regime_label(features: dict[str, Any]) -> str:
    """
    Determine market regime based on feature values.

    Args:
        features: Dictionary of computed features from FeatureStore

    Returns:
        String label representing the current market regime

    Regime Types:
        - base: Normal market conditions
        - vol_hi_liq_lo: High volatility, low liquidity (crisis mode)
        - vol_lo_liq_hi: Low volatility, high liquidity (complacency mode)
        - stress: Extreme stress conditions (VIX spike, illiquidity)
    """

    # Extract key regime indicators
    volatility = float(features.get("volatility_20d", 0.2))
    liquidity = float(features.get("liquidity_score", 0.5))
    vix_level = float(features.get("vix_level", 20))
    # breadth = float(features.get("breadth_advdec", 1.0))  # TODO: Use in enhanced regime detection
    # yield_curve = float(features.get("yield_curve", 1.5))  # TODO: Use in enhanced regime detection

    # Stress regime: Multiple warning signals
    if (
        vix_level > REGIME_THRESHOLDS["vix"]["high"]
        and volatility > REGIME_THRESHOLDS["volatility"]["high"]
        and liquidity < REGIME_THRESHOLDS["liquidity"]["low"]
    ):
        logger.debug("Detected stress regime")
        return "stress"

    # High vol, low liquidity regime
    if (
        volatility > REGIME_THRESHOLDS["volatility"]["high"]
        and liquidity < REGIME_THRESHOLDS["liquidity"]["low"]
    ):
        logger.debug("Detected vol_hi_liq_lo regime")
        return "vol_hi_liq_lo"

    # Low vol, high liquidity regime (complacency)
    if (
        volatility < REGIME_THRESHOLDS["volatility"]["low"]
        and liquidity > REGIME_THRESHOLDS["liquidity"]["high"]
        and vix_level < REGIME_THRESHOLDS["vix"]["low"]
    ):
        logger.debug("Detected vol_lo_liq_hi regime")
        return "vol_lo_liq_hi"

    # Default to base regime
    logger.debug("Detected base regime")
    return "base"


def regime_vector(label: str) -> list[float]:
    """
    Convert regime label to vector representation for model input.

    Args:
        label: Regime label from regime_label()

    Returns:
        List of floats representing the regime as a one-hot encoded vector
    """
    return REGIME_VECTORS.get(label, REGIME_VECTORS["base"]).copy()


def regime_confidence(features: dict[str, Any], regime: str) -> float:
    """
    Calculate confidence in the regime classification.

    Args:
        features: Dictionary of computed features
        regime: Detected regime label

    Returns:
        Confidence score between 0.0 and 1.0
    """

    volatility = float(features.get("volatility_20d", 0.2))
    liquidity = float(features.get("liquidity_score", 0.5))
    vix_level = float(features.get("vix_level", 20))

    if regime == "stress":
        # High confidence if multiple stress indicators align
        stress_signals = sum([vix_level > 35, volatility > 0.5, liquidity < 0.2])
        return min(0.6 + stress_signals * 0.13, 1.0)

    elif regime == "vol_hi_liq_lo":
        # Confidence based on how extreme the values are
        vol_score = min((volatility - 0.35) / 0.2, 1.0) if volatility > 0.35 else 0
        liq_score = min((0.3 - liquidity) / 0.3, 1.0) if liquidity < 0.3 else 0
        return max(0.5, (vol_score + liq_score) / 2)

    elif regime == "vol_lo_liq_hi":
        # Confidence for low vol regime
        vol_score = min((0.15 - volatility) / 0.15, 1.0) if volatility < 0.15 else 0
        liq_score = min((liquidity - 0.7) / 0.3, 1.0) if liquidity > 0.7 else 0
        vix_score = min((15 - vix_level) / 15, 1.0) if vix_level < 15 else 0
        return max(0.5, (vol_score + liq_score + vix_score) / 3)

    else:  # base regime
        # Lower confidence when not clearly in other regimes
        return 0.7


def regime_description(regime: str) -> str:
    """
    Get human-readable description of regime.

    Args:
        regime: Regime label

    Returns:
        Description string
    """
    descriptions = {
        "base": "Normal market conditions with typical volatility and liquidity",
        "vol_hi_liq_lo": "High volatility, low liquidity - risk-off environment",
        "vol_lo_liq_hi": "Low volatility, high liquidity - complacency phase",
        "stress": "Market stress with extreme volatility and illiquidity",
    }
    return descriptions.get(regime, "Unknown regime")


def get_regime_weights(regime: str) -> dict[str, float]:
    """
    Get model weights/adjustments for different regimes.

    Args:
        regime: Regime label

    Returns:
        Dictionary of weight adjustments for different signal types
    """

    weights = {
        "base": {"momentum": 1.0, "mean_reversion": 1.0, "volatility": 1.0, "sentiment": 1.0},
        "vol_hi_liq_lo": {
            "momentum": 0.7,  # Momentum less reliable in volatile periods
            "mean_reversion": 1.3,  # Mean reversion stronger
            "volatility": 1.5,  # Vol signals more important
            "sentiment": 0.8,  # Sentiment less reliable
        },
        "vol_lo_liq_hi": {
            "momentum": 1.2,  # Momentum works better in trending markets
            "mean_reversion": 0.8,  # Less mean reversion
            "volatility": 0.7,  # Vol signals less important
            "sentiment": 1.1,  # Sentiment more reliable
        },
        "stress": {
            "momentum": 0.5,  # Momentum breaks down
            "mean_reversion": 1.5,  # Strong mean reversion
            "volatility": 2.0,  # Volatility signals critical
            "sentiment": 0.6,  # Sentiment unreliable
        },
    }

    return weights.get(regime, weights["base"])


class RegimeDetector:
    """
    Object-oriented wrapper around regime detection functions.

    Provides a class-based API for tests and services that expect
    an OO interface while maintaining the functional API.
    """

    def __init__(self):
        """Initialize the regime detector."""
        pass

    def detect_regime(self, features: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Detect market regime from features.

        Args:
            features: Feature dictionary. If None, will attempt to get current features.

        Returns:
            Complete regime analysis
        """
        if features is None:
            # Placeholder: in production, would fetch current market features
            features = {"volatility_20d": 0.2, "liquidity_score": 0.5, "vix_level": 20}

        return detect_regime(features)

    def get_regime_label(self, features: dict[str, Any]) -> str:
        """Get regime label from features."""
        return regime_label(features)

    def get_regime_vector(self, label: str) -> list[float]:
        """Convert regime label to vector."""
        return regime_vector(label)

    def get_regime_confidence(self, features: dict[str, Any], regime: str) -> float:
        """Calculate confidence in regime classification."""
        return regime_confidence(features, regime)


def analyze_regime_history(feature_history: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze regime transitions over time.

    Args:
        feature_history: List of feature dictionaries over time

    Returns:
        Dictionary with regime analysis
    """

    if not feature_history:
        return {"error": "No feature history provided"}

    regimes = [regime_label(features) for features in feature_history]

    # Count regime occurrences
    regime_counts = {}
    for regime in regimes:
        regime_counts[regime] = regime_counts.get(regime, 0) + 1

    # Count transitions
    transitions = {}
    for i in range(1, len(regimes)):
        prev_regime = regimes[i - 1]
        curr_regime = regimes[i]
        if prev_regime != curr_regime:
            transition = f"{prev_regime}->{curr_regime}"
            transitions[transition] = transitions.get(transition, 0) + 1

    # Calculate regime persistence
    persistence = {}
    for regime in set(regimes):
        regime_runs = []
        current_run = 0
        for r in regimes:
            if r == regime:
                current_run += 1
            else:
                if current_run > 0:
                    regime_runs.append(current_run)
                current_run = 0
        if current_run > 0:
            regime_runs.append(current_run)

        persistence[regime] = {
            "avg_duration": np.mean(regime_runs) if regime_runs else 0,
            "max_duration": max(regime_runs) if regime_runs else 0,
        }

    return {
        "total_periods": len(regimes),
        "regime_distribution": {k: v / len(regimes) for k, v in regime_counts.items()},
        "transitions": transitions,
        "persistence": persistence,
        "current_regime": regimes[-1] if regimes else "unknown",
    }


# Convenience functions for API integration
def detect_regime(features: dict[str, Any]) -> dict[str, Any]:
    """
    One-stop regime detection with full output.

    Args:
        features: Feature dictionary from FeatureStore

    Returns:
        Complete regime analysis
    """

    regime = regime_label(features)
    confidence = regime_confidence(features, regime)
    vector = regime_vector(regime)
    description = regime_description(regime)
    weights = get_regime_weights(regime)

    return {
        "regime": regime,
        "confidence": confidence,
        "vector": vector,
        "description": description,
        "weights": weights,
        "thresholds": REGIME_THRESHOLDS,
    }


class RegimeDetector:
    """
    OO wrapper for regime detection functionality.

    Provides a class-based interface for regime detection with optional
    feature computer injection. No I/O operations on import or init.
    """

    def __init__(self, feature_computer=None):
        """
        Initialize regime detector.

        Args:
            feature_computer: Optional feature computer for computing features
        """
        self.feature_computer = feature_computer
        self.thresholds = REGIME_THRESHOLDS.copy()
        logger.debug("RegimeDetector initialized")

    def detect(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Detect market regime from features.

        Args:
            features: Dictionary of computed features

        Returns:
            Complete regime analysis
        """
        return detect_regime(features)

    def get_label(self, features: dict[str, Any]) -> str:
        """Get regime label only."""
        return regime_label(features)

    def get_vector(self, features: dict[str, Any]) -> list[float]:
        """Get regime vector representation."""
        label = self.get_label(features)
        return regime_vector(label)

    def get_confidence(self, features: dict[str, Any]) -> float:
        """Get confidence in regime detection."""
        label = self.get_label(features)
        return regime_confidence(features, label)

    def analyze_history(self, feature_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze regime transitions over time."""
        return analyze_regime_history(feature_history)

    def set_thresholds(self, thresholds: dict[str, dict[str, float]]) -> None:
        """Update detection thresholds (for calibration)."""
        self.thresholds.update(thresholds)


__all__ = [
    "REGIME_THRESHOLDS",
    "REGIME_VECTORS",
    "RegimeDetector",
    "analyze_regime_history",
    "detect_regime",
    "get_regime_weights",
    "regime_confidence",
    "regime_description",
    "regime_label",
    "regime_vector",
]
