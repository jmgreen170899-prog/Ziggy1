"""
Demo utilities for safe demonstrations.

Provides deterministic data and safe operations when DEMO_MODE is enabled.
"""

from app.demo.data_generators import (
    get_demo_market_data,
    get_demo_portfolio,
    get_demo_signals,
    get_demo_news,
    get_demo_backtest_result,
    is_demo_mode,
)

__all__ = [
    "get_demo_market_data",
    "get_demo_portfolio",
    "get_demo_signals",
    "get_demo_news",
    "get_demo_backtest_result",
    "is_demo_mode",
]
