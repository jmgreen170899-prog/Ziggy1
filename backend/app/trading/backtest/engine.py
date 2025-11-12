from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class BacktestResult:
    def __init__(self, trades: list[dict[str, Any]], equity_curve: list[float]):
        self.trades = trades
        self.equity_curve = equity_curve


def run_backtest(prices: Iterable[float]) -> BacktestResult:
    eq = 10000.0
    curve = [eq for _ in prices]
    return BacktestResult(trades=[], equity_curve=curve)
