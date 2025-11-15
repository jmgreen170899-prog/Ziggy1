"""
ZiggyAI Paper Trading Lab Package.

This package provides a complete autonomous paper trading system including:
- Paper broker with realistic execution simulation
- Micro-trade engine with rate limiting and concurrency control
- Trading theory registry with plug-in architecture
- Multi-armed bandit allocation system
- Feature engineering and labeling pipeline
- Online learning with multiple backends
"""

from .allocator import BanditAlgorithm, BanditAllocator
from .engine import PaperEngine, RunParams, RunStats, Signal
from .features import (
    FeatureComputer,
    PriceData,
    compute_features_async,
    feature_computer,
)
from .labels import LabelGenerator, TradeLabel, label_generator
from .learner import OnlineLearner, PredictionResult, TrainingBatch
from .theories import MarketFeatures, Theory, theory_registry


__all__ = [
    "BanditAlgorithm",
    "BanditAllocator",
    "FeatureComputer",
    "LabelGenerator",
    "MarketFeatures",
    "OnlineLearner",
    "PaperEngine",
    "PredictionResult",
    "PriceData",
    "RunParams",
    "RunStats",
    "Signal",
    "Theory",
    "TradeLabel",
    "TrainingBatch",
    "compute_features_async",
    "feature_computer",
    "label_generator",
    "theory_registry",
]
