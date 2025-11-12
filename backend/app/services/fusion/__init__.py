"""
Signal Fusion Package for ZiggyAI Cognitive Core

Provides ensemble models and calibration for trading signal fusion.
"""

from .ensemble import (
    FEATURE_ORDER,
    FEATURE_WEIGHTS,
    bulk_predict,
    explain,
    fused_probability,
    get_model_info,
    initialize_models,
    validate_features,
    vectorize,
)


__all__ = [
    "FEATURE_ORDER",
    "FEATURE_WEIGHTS",
    "bulk_predict",
    "explain",
    "fused_probability",
    "get_model_info",
    "initialize_models",
    "validate_features",
    "vectorize",
]
