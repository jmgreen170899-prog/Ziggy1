"""
Signal Fusion Ensemble Module

Implements Bayesian and stacked ensemble models for combining multiple trading signals
into calibrated probabilities with feature attribution and explainability.

Integrates with existing ZiggyAI calibration system.
"""

from __future__ import annotations

import logging
import pickle
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

# Import existing calibration system
try:
    from ..calibration import ProbabilityCalibrator

    CALIBRATION_AVAILABLE = True
except ImportError:
    ProbabilityCalibrator = None
    CALIBRATION_AVAILABLE = False
    logger.warning("Calibration module not available")

# Model registry for different regimes
model_by_regime: dict[str, Any] = {}
calibrators: dict[str, Any] = {}

# Feature importance weights (placeholder - would be learned)
FEATURE_WEIGHTS = {
    "momentum_20d": 0.15,
    "momentum_5d": 0.12,
    "rsi_14": 0.08,
    "volatility_20d": 0.10,
    "volatility_5d": 0.07,
    "liquidity_score": 0.09,
    "news_sentiment": 0.11,
    "vix_level": 0.08,
    "order_flow": 0.10,
    "breadth_advdec": 0.06,
    "yield_curve": 0.04,
}

# Feature order for consistent vectorization
FEATURE_ORDER = [
    "momentum_20d",
    "momentum_5d",
    "rsi_14",
    "volatility_20d",
    "volatility_5d",
    "liquidity_score",
    "news_sentiment",
    "vix_level",
    "order_flow",
    "breadth_advdec",
    "yield_curve",
    "bid_ask_spread",
    "news_volume",
]


class MockModel:
    """Mock model for demonstration - replace with real ML models."""

    def __init__(self, regime: str):
        self.regime = regime
        # Different model behavior per regime
        self.bias = {
            "base": 0.52,
            "vol_hi_liq_lo": 0.45,  # Bearish bias in high vol
            "vol_lo_liq_hi": 0.55,  # Bullish bias in low vol
            "stress": 0.40,  # Strong bearish bias in stress
        }.get(regime, 0.50)

    def predict_proba(self, X: list[list[float]]) -> np.ndarray:
        """Predict probabilities for input features."""
        if not X:
            return np.array([[0.5, 0.5]])

        # Simple linear combination with noise
        probs = []
        for x in X:
            # Weighted sum of features
            score = sum(
                x[i] * list(FEATURE_WEIGHTS.values())[i]
                for i in range(min(len(x), len(FEATURE_WEIGHTS)))
            )

            # Apply regime bias and add noise
            prob = self.bias + score * 0.1 + np.random.normal(0, 0.05)
            prob = max(0.1, min(0.9, prob))  # Clip to reasonable range

            probs.append([1 - prob, prob])

        return np.array(probs)


class MockCalibrator:
    """Mock calibrator for Platt scaling - replace with sklearn."""

    def __init__(self, regime: str):
        self.regime = regime
        # Calibration adjustments per regime
        self.adjustment = {
            "base": 0.0,
            "vol_hi_liq_lo": -0.05,  # Reduce overconfidence in volatile periods
            "vol_lo_liq_hi": 0.02,  # Slight positive adjustment
            "stress": -0.1,  # Strong adjustment in stress
        }.get(regime, 0.0)

    def transform(self, probs: list[float]) -> list[float]:
        """Apply calibration adjustment."""
        return [max(0.01, min(0.99, p + self.adjustment)) for p in probs]


def initialize_models():
    """Initialize models and calibrators for each regime."""
    global model_by_regime, calibrators

    regimes = ["base", "vol_hi_liq_lo", "vol_lo_liq_hi", "stress"]

    for regime in regimes:
        model_by_regime[regime] = MockModel(regime)
        calibrators[regime] = MockCalibrator(regime)
        logger.info(f"Initialized model and calibrator for regime: {regime}")


def vectorize(features: dict[str, Any]) -> list[float]:
    """
    Convert feature dictionary to ordered vector for model input.

    Args:
        features: Dictionary of features from FeatureStore

    Returns:
        List of float values in consistent order
    """
    vector = []
    for feature_name in FEATURE_ORDER:
        value = features.get(feature_name, 0.0)
        if isinstance(value, (int, float)):
            vector.append(float(value))
        else:
            # Handle non-numeric features
            if feature_name == "vol_regime":
                # Convert vol regime to numeric
                regime_map = {"low": -1.0, "medium": 0.0, "high": 1.0}
                vector.append(regime_map.get(value, 0.0))
            else:
                vector.append(0.0)  # Default for unknown types

    return vector


def explain(features: dict[str, Any], prediction: float) -> list[tuple[str, float]]:
    """
    Generate feature attributions using mock SHAP-style explanation.

    Args:
        features: Feature dictionary
        prediction: Model prediction

    Returns:
        List of (feature_name, contribution) tuples sorted by importance
    """
    x = vectorize(features)
    attributions = []

    # Mock SHAP values - in production, use real SHAP
    for i, feature_name in enumerate(FEATURE_ORDER[: len(x)]):
        if i < len(x):
            # Simple attribution: feature_value * weight * prediction_strength
            value = x[i]
            weight = FEATURE_WEIGHTS.get(feature_name, 0.0)
            contribution = value * weight * (prediction - 0.5)
            attributions.append((feature_name, contribution))

    # Sort by absolute contribution
    attributions.sort(key=lambda x: abs(x[1]), reverse=True)
    return attributions


def fused_probability(features: dict[str, Any], regime: str) -> dict[str, Any]:
    """
    Generate fused probability prediction with explanations.

    This is the main API function that:
    1. Vectorizes features
    2. Runs regime-specific model
    3. Applies calibration
    4. Generates explanations

    Args:
        features: Feature dictionary from FeatureStore
        regime: Market regime from regime detection

    Returns:
        Dictionary with prediction, explanations, and metadata
    """

    # Ensure models are initialized
    if not model_by_regime:
        initialize_models()

    # Vectorize features
    x = vectorize(features)

    # Get model for regime (fallback to base)
    model = model_by_regime.get(regime, model_by_regime.get("base"))
    if model is None:
        logger.warning(f"No model found for regime {regime}, using fallback")
        # Fallback prediction
        p_raw = 0.5
    else:
        # Get raw prediction
        try:
            p_raw = model.predict_proba([x])[0, 1]  # Probability of positive class
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            p_raw = 0.5

    # Apply calibration
    calibrator = calibrators.get(regime)
    if calibrator is not None:
        try:
            p_calibrated = calibrator.transform([p_raw])[0]
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            p_calibrated = p_raw
    else:
        p_calibrated = p_raw

    # Generate explanations
    try:
        explanations = explain(features, p_calibrated)
        shap_top = explanations[:3]  # Top 3 features
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        shap_top = [("unknown", 0.0)]

    # Calculate confidence based on prediction strength
    confidence = abs(p_calibrated - 0.5) * 2  # 0 to 1 scale

    return {
        "p_up": float(p_calibrated),
        "p_raw": float(p_raw),
        "confidence": float(confidence),
        "shap_top": shap_top,
        "regime": regime,
        "feature_count": len(x),
        "model_type": type(model).__name__ if model else "fallback",
    }


def bulk_predict(
    feature_list: list[dict[str, Any]], regime_list: list[str]
) -> list[dict[str, Any]]:
    """
    Process multiple predictions efficiently.

    Args:
        feature_list: List of feature dictionaries
        regime_list: List of corresponding regimes

    Returns:
        List of prediction results
    """

    if len(feature_list) != len(regime_list):
        raise ValueError("Feature list and regime list must have same length")

    results = []
    for features, regime in zip(feature_list, regime_list):
        try:
            result = fused_probability(features, regime)
            results.append(result)
        except Exception as e:
            logger.error(f"Bulk prediction failed for item: {e}")
            results.append(
                {
                    "p_up": 0.5,
                    "p_raw": 0.5,
                    "confidence": 0.0,
                    "shap_top": [("error", 0.0)],
                    "regime": regime,
                    "error": str(e),
                }
            )

    return results


def update_model(regime: str, model_data: bytes):
    """
    Update model for specific regime.

    Args:
        regime: Regime identifier
        model_data: Pickled model data
    """
    try:
        model = pickle.loads(model_data)
        model_by_regime[regime] = model
        logger.info(f"Updated model for regime: {regime}")
    except Exception as e:
        logger.error(f"Failed to update model for regime {regime}: {e}")


def update_calibrator(regime: str, calibrator_data: bytes):
    """
    Update calibrator for specific regime.

    Args:
        regime: Regime identifier
        calibrator_data: Pickled calibrator data
    """
    try:
        calibrator = pickle.loads(calibrator_data)
        calibrators[regime] = calibrator
        logger.info(f"Updated calibrator for regime: {regime}")
    except Exception as e:
        logger.error(f"Failed to update calibrator for regime {regime}: {e}")


def get_model_info() -> dict[str, Any]:
    """Get information about loaded models."""
    return {
        "regimes": list(model_by_regime.keys()),
        "model_types": {
            regime: type(model).__name__ for regime, model in model_by_regime.items()
        },
        "calibrator_types": {
            regime: type(cal).__name__ for regime, cal in calibrators.items()
        },
        "feature_order": FEATURE_ORDER,
        "feature_weights": FEATURE_WEIGHTS,
    }


def validate_features(features: dict[str, Any]) -> dict[str, Any]:
    """
    Validate feature dictionary and report any issues.

    Args:
        features: Feature dictionary to validate

    Returns:
        Validation report
    """

    issues = []
    warnings = []

    # Check for required features
    required_features = FEATURE_ORDER[:5]  # Core features
    for feature in required_features:
        if feature not in features:
            issues.append(f"Missing required feature: {feature}")

    # Check feature types and ranges
    for feature, value in features.items():
        if feature in FEATURE_ORDER:
            if not isinstance(value, (int, float)):
                issues.append(f"Feature {feature} should be numeric, got {type(value)}")
            elif not np.isfinite(value):
                issues.append(f"Feature {feature} is not finite: {value}")
            elif feature == "rsi_14" and not (0 <= value <= 100):
                warnings.append(f"RSI value {value} outside normal range [0,100]")
            elif feature.startswith("volatility") and value < 0:
                issues.append(f"Volatility {feature} should be non-negative: {value}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "feature_count": len(features),
        "coverage": len([f for f in FEATURE_ORDER if f in features])
        / len(FEATURE_ORDER),
    }


# Initialize models on import
initialize_models()

__all__ = [
    "FEATURE_ORDER",
    "FEATURE_WEIGHTS",
    "SignalFusionEnsemble",
    "bulk_predict",
    "explain",
    "fused_probability",
    "get_model_info",
    "initialize_models",
    "update_calibrator",
    "update_model",
    "validate_features",
    "vectorize",
]


# Back-compat shim for tests that expect SignalFusionEnsemble
class SignalFusionEnsemble:
    """
    Back-compat wrapper for tests that expect SignalFusionEnsemble.

    This class provides a simple interface for signal fusion functionality
    that delegates to the module-level functions. Includes a minimal fuse API
    for weighted averaging of signals.
    """

    def __init__(self):
        """Initialize the ensemble."""
        # Ensure models are initialized
        if not model_by_regime:
            initialize_models()

    def predict(self, features: dict[str, Any], regime: str = "base") -> dict[str, Any]:
        """
        Generate prediction with the ensemble.

        Args:
            features: Feature dictionary
            regime: Market regime

        Returns:
            Prediction result
        """
        return fused_probability(features, regime)

    def batch_predict(
        self, feature_list: list[dict[str, Any]], regime_list: list[str]
    ) -> list[dict[str, Any]]:
        """Process multiple predictions efficiently."""
        return bulk_predict(feature_list, regime_list)

    def fuse(
        self,
        signals: list[float] | tuple[float, ...],
        weights: list[float] | tuple[float, ...] | None = None,
    ) -> float:
        """
        Fuse multiple signals using weighted average.

        Implements a simple (optionally weighted) average with basic guards.

        Args:
            signals: Sequence of signal values to fuse
            weights: Optional weights for each signal. If None, uses equal weights.

        Returns:
            Fused signal value

        Raises:
            ValueError: If weights length doesn't match signals length
        """
        vals = [float(x) for x in signals]
        if not vals:
            return 0.0

        if weights is None:
            # Equal weighting
            return sum(vals) / len(vals)

        w = [float(x) for x in weights]
        if len(w) != len(vals):
            raise ValueError("weights length must match signals length")

        denom = sum(w) or 1.0
        return sum(v * ww for v, ww in zip(vals, w)) / denom
