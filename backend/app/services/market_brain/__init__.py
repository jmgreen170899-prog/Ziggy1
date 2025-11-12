"""
Ziggy AI Market Brain - Modular Market Intelligence System

This package provides explainable, rule-based market analysis with:
- Technical feature computation
- Market regime detection
- Signal generation with confidence scoring
- Risk-based position sizing
- Execution integration
- Backtesting and validation

All modules prioritize interpretability and explainability over black-box ML.
"""

__version__ = "1.0.0"
__author__ = "Ziggy AI"

# Core modules
from .backtest import BacktestConfig, Backtester, BacktestResults, backtester
from .executor import ExecutionResult, ExecutionStatus, TradeExecutor, trade_executor

# Convenience functions
from .regime import (
    RegimeDetector,
    RegimeResult,
    RegimeState,
    get_regime_state,
    get_regime_string,
    is_defensive_regime,
    is_risk_regime,
    regime_detector,
)
from .signals import (
    Signal,
    SignalDirection,
    SignalGenerator,
    SignalType,
    generate_signals_for_watchlist,
    generate_ticker_signal,
    signal_generator,
)
from .simple_data_hub import (
    DataSource,
    EnhancedData,
    SimpleMarketBrainDataHub,
    enhance_market_data,
    simple_data_hub,
)
from .sizer import (
    PositionSize,
    PositionSizer,
    SizingMethod,
    calculate_position_for_signal,
    position_sizer,
)


# Legacy support - try to import features if available
try:
    from .features import (
        FeatureComputer,
        FeatureSet,
        feature_computer,
        get_multiple_ticker_features,
        get_ticker_features,
    )

    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False
from .backtest import analyze_signals, quick_backtest
from .executor import execute_trade_signal, get_execution_status


__all__ = [
    # Classes
    "FeatureComputer",
    "FeatureSet",
    "RegimeDetector",
    "RegimeResult",
    "RegimeState",
    "SignalGenerator",
    "Signal",
    "SignalDirection",
    "SignalType",
    "PositionSizer",
    "PositionSize",
    "SizingMethod",
    "TradeExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "Backtester",
    "BacktestResults",
    "BacktestConfig",
    # Global instances
    "feature_computer",
    "regime_detector",
    "signal_generator",
    "position_sizer",
    "trade_executor",
    "backtester",
    # Convenience functions
    "get_ticker_features",
    "get_multiple_ticker_features",
    "get_regime_state",
    "get_regime_string",
    "is_risk_regime",
    "is_defensive_regime",
    "generate_ticker_signal",
    "generate_signals_for_watchlist",
    "calculate_position_for_signal",
    "execute_trade_signal",
    "get_execution_status",
    "quick_backtest",
    "analyze_signals",
]
