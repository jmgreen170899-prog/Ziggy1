"""
Backtesting Package for ZiggyAI Cognitive Core

Provides comprehensive backtesting capabilities with cost modeling and metrics.
"""

from .engine import (
    BacktestEngine,
    BacktestResults,
    BorrowModel,
    FeeModel,
    SlippageModel,
    Trade,
    run_backtest,
)


__all__ = [
    "BacktestEngine",
    "BacktestResults",
    "BorrowModel",
    "FeeModel",
    "SlippageModel",
    "Trade",
    "run_backtest",
]
