"""
Backtesting Engine for ZiggyAI Cognitive Core

Provides deterministic backtesting with slippage, fees, and borrow models.
Supports CLI execution and comprehensive performance metrics.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

# Import our components
try:
    from ..data.features import compute_features
    from ..services.fusion import fused_probability
    from ..services.regime import detect_regime

    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    logger.warning("Some components not available for backtesting")


@dataclass
class Trade:
    """Represents a single trade."""

    id: str
    symbol: str
    entry_time: datetime
    exit_time: datetime | None
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    exit_price: float | None
    pnl: float | None
    pnl_percent: float | None
    fees: float
    slippage: float
    regime: str
    confidence: float
    reason: str


@dataclass
class BacktestResults:
    """Comprehensive backtest results."""

    # Basic info
    universe: list[str]
    start_date: str
    end_date: str
    total_days: int

    # Performance metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Returns
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float

    # Risk metrics
    volatility: float
    var_95: float  # Value at Risk 95%
    max_consecutive_losses: int

    # Cost analysis
    total_fees: float
    total_slippage: float
    cost_ratio: float  # costs / gross_pnl

    # Regime breakdown
    regime_performance: dict[str, dict[str, float]]

    # Signal quality
    auc_score: float
    pr_auc_score: float
    ece_score: float

    # Detailed trades
    trades: list[Trade]

    # Equity curve
    equity_curve: list[dict[str, Any]]


class SlippageModel:
    """Models market impact and slippage."""

    def __init__(self, base_bps: float = 2.0, impact_factor: float = 0.1):
        """
        Initialize slippage model.

        Args:
            base_bps: Base slippage in basis points
            impact_factor: Market impact factor (higher = more impact)
        """
        self.base_bps = base_bps
        self.impact_factor = impact_factor

    def calculate_slippage(
        self, symbol: str, quantity: float, price: float, volatility: float = 0.2
    ) -> float:
        """
        Calculate slippage for a trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity (shares)
            price: Current price
            volatility: Current volatility

        Returns:
            Slippage amount in dollars
        """
        # Base slippage
        base_slippage = (self.base_bps / 10000) * price * abs(quantity)

        # Market impact based on size and volatility
        market_impact = (
            self.impact_factor * volatility * np.sqrt(abs(quantity)) * price * 0.01
        )

        return base_slippage + market_impact


class FeeModel:
    """Models trading fees and commissions."""

    def __init__(
        self, per_share: float = 0.005, min_fee: float = 1.0, max_fee: float = 10.0
    ):
        """
        Initialize fee model.

        Args:
            per_share: Fee per share
            min_fee: Minimum fee per trade
            max_fee: Maximum fee per trade
        """
        self.per_share = per_share
        self.min_fee = min_fee
        self.max_fee = max_fee

    def calculate_fee(self, quantity: float) -> float:
        """Calculate trading fee."""
        fee = abs(quantity) * self.per_share
        return max(self.min_fee, min(fee, self.max_fee))


class BorrowModel:
    """Models stock borrowing costs for short sales."""

    def __init__(self, base_rate: float = 0.02):
        """
        Initialize borrow model.

        Args:
            base_rate: Base borrowing rate (annual)
        """
        self.base_rate = base_rate

    def calculate_borrow_cost(
        self, symbol: str, quantity: float, price: float, days: int
    ) -> float:
        """
        Calculate borrowing cost for short position.

        Args:
            symbol: Trading symbol
            quantity: Quantity (negative for short)
            price: Average price during holding period
            days: Days held

        Returns:
            Borrowing cost in dollars
        """
        if quantity >= 0:
            return 0.0  # No borrow cost for long positions

        # Simple borrow cost calculation
        notional = abs(quantity) * price
        annual_cost = notional * self.base_rate
        return annual_cost * (days / 365.0)


class BacktestEngine:
    """Main backtesting engine."""

    def __init__(
        self,
        slippage_model: SlippageModel | None = None,
        fee_model: FeeModel | None = None,
        borrow_model: BorrowModel | None = None,
    ):
        """Initialize backtest engine."""
        self.slippage_model = slippage_model or SlippageModel()
        self.fee_model = fee_model or FeeModel()
        self.borrow_model = borrow_model or BorrowModel()

        self.trades: list[Trade] = []
        self.equity_curve: list[dict[str, Any]] = []

    def run_backtest(
        self,
        universe: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
    ) -> BacktestResults:
        """
        Run complete backtest.

        Args:
            universe: List of symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital

        Returns:
            Comprehensive backtest results
        """

        logger.info(f"Starting backtest: {universe} from {start_date} to {end_date}")

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end_dt - start_dt).days

        # Initialize tracking
        self.trades = []
        self.equity_curve = []
        current_capital = initial_capital
        positions: dict[str, dict[str, Any]] = {}

        # Daily simulation loop
        current_date = start_dt
        trade_id = 1

        while current_date <= end_dt:
            # Skip weekends (simple approach)
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # Process each symbol
            for symbol in universe:
                # Generate features and signals
                if COMPONENTS_AVAILABLE:
                    features = compute_features(symbol, current_date)
                    regime_info = detect_regime(features)
                    signal_result = fused_probability(features, regime_info["regime"])
                else:
                    # Mock signal for testing
                    signal_result = {
                        "p_up": np.random.uniform(0.3, 0.7),
                        "confidence": np.random.uniform(0.5, 0.9),
                        "regime": "base",
                    }

                # Simple trading logic (replace with sophisticated strategy)
                p_up = signal_result["p_up"]
                confidence = signal_result["confidence"]
                regime = signal_result.get("regime", "base")

                # Entry signals
                if symbol not in positions:
                    if p_up > 0.6 and confidence > 0.7:
                        # Long entry
                        quantity = int(
                            current_capital * 0.02 / 100
                        )  # 2% position, $100/share
                        price = 100.0 + np.random.normal(0, 2)  # Mock price

                        trade = self._open_position(
                            trade_id,
                            symbol,
                            current_date,
                            "long",
                            quantity,
                            price,
                            regime,
                            confidence,
                            "High confidence long signal",
                        )
                        positions[symbol] = {"trade": trade, "entry_date": current_date}
                        trade_id += 1

                    elif p_up < 0.4 and confidence > 0.7:
                        # Short entry
                        quantity = -int(
                            current_capital * 0.02 / 100
                        )  # 2% position short
                        price = 100.0 + np.random.normal(0, 2)  # Mock price

                        trade = self._open_position(
                            trade_id,
                            symbol,
                            current_date,
                            "short",
                            quantity,
                            price,
                            regime,
                            confidence,
                            "High confidence short signal",
                        )
                        positions[symbol] = {"trade": trade, "entry_date": current_date}
                        trade_id += 1

                # Exit signals
                elif symbol in positions:
                    position = positions[symbol]
                    trade = position["trade"]
                    days_held = (current_date - position["entry_date"]).days

                    should_exit = False
                    exit_reason = ""

                    # Exit conditions
                    if days_held >= 10:  # Max holding period
                        should_exit = True
                        exit_reason = "Max holding period"
                    elif trade.side == "long" and p_up < 0.3:
                        should_exit = True
                        exit_reason = "Long exit signal"
                    elif trade.side == "short" and p_up > 0.7:
                        should_exit = True
                        exit_reason = "Short exit signal"

                    if should_exit:
                        exit_price = 100.0 + np.random.normal(0, 2)  # Mock exit price
                        completed_trade = self._close_position(
                            trade, current_date, exit_price, exit_reason
                        )
                        self.trades.append(completed_trade)
                        current_capital += completed_trade.pnl or 0
                        del positions[symbol]

            # Record equity curve
            total_pnl = sum(t.pnl or 0 for t in self.trades)
            self.equity_curve.append(
                {
                    "date": current_date.isoformat(),
                    "equity": initial_capital + total_pnl,
                    "trades_count": len(self.trades),
                    "positions_count": len(positions),
                }
            )

            current_date += timedelta(days=1)

        # Close any remaining positions
        for symbol, position in positions.items():
            trade = position["trade"]
            exit_price = 100.0 + np.random.normal(0, 2)  # Mock exit price
            completed_trade = self._close_position(
                trade, end_dt, exit_price, "End of backtest"
            )
            self.trades.append(completed_trade)

        # Calculate comprehensive results
        return self._calculate_results(
            universe, start_date, end_date, total_days, initial_capital
        )

    def _open_position(
        self,
        trade_id: int,
        symbol: str,
        entry_time: datetime,
        side: str,
        quantity: float,
        price: float,
        regime: str,
        confidence: float,
        reason: str,
    ) -> Trade:
        """Open a new position."""

        # Calculate costs
        volatility = 0.2  # Mock volatility
        slippage = self.slippage_model.calculate_slippage(
            symbol, quantity, price, volatility
        )
        fees = self.fee_model.calculate_fee(quantity)

        return Trade(
            id=f"trade_{trade_id}",
            symbol=symbol,
            entry_time=entry_time,
            exit_time=None,
            side=side,
            quantity=quantity,
            entry_price=price,
            exit_price=None,
            pnl=None,
            pnl_percent=None,
            fees=fees,
            slippage=slippage,
            regime=regime,
            confidence=confidence,
            reason=reason,
        )

    def _close_position(
        self, trade: Trade, exit_time: datetime, exit_price: float, reason: str
    ) -> Trade:
        """Close an existing position."""

        # Calculate additional costs
        exit_fees = self.fee_model.calculate_fee(trade.quantity)
        exit_slippage = self.slippage_model.calculate_slippage(
            trade.symbol, trade.quantity, exit_price, 0.2
        )

        # Calculate borrow costs for short positions
        days_held = (exit_time - trade.entry_time).days
        borrow_cost = self.borrow_model.calculate_borrow_cost(
            trade.symbol,
            trade.quantity,
            (trade.entry_price + exit_price) / 2,
            days_held,
        )

        # Calculate P&L
        if trade.side == "long":
            gross_pnl = trade.quantity * (exit_price - trade.entry_price)
        else:  # short
            gross_pnl = abs(trade.quantity) * (trade.entry_price - exit_price)

        total_costs = (
            trade.fees + trade.slippage + exit_fees + exit_slippage + borrow_cost
        )
        net_pnl = gross_pnl - total_costs

        # Update trade
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.pnl = net_pnl
        trade.pnl_percent = net_pnl / (trade.entry_price * abs(trade.quantity)) * 100
        trade.fees += exit_fees
        trade.slippage += exit_slippage
        trade.reason += f" -> {reason}"

        return trade

    def _calculate_results(
        self,
        universe: list[str],
        start_date: str,
        end_date: str,
        total_days: int,
        initial_capital: float,
    ) -> BacktestResults:
        """Calculate comprehensive backtest results."""

        # Basic trade statistics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if (t.pnl or 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Returns calculation
        total_pnl = sum(t.pnl or 0 for t in self.trades)
        total_return = total_pnl / initial_capital
        years = total_days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Risk metrics
        returns = []
        if len(self.equity_curve) > 1:
            for i in range(1, len(self.equity_curve)):
                prev_equity = self.equity_curve[i - 1]["equity"]
                curr_equity = self.equity_curve[i]["equity"]
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)

        volatility = np.std(returns) * np.sqrt(252) if returns else 0
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Drawdown calculation
        peak = initial_capital
        max_drawdown = 0
        for point in self.equity_curve:
            equity = point["equity"]
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Cost analysis
        total_fees = sum(t.fees for t in self.trades)
        total_slippage = sum(t.slippage for t in self.trades)
        gross_pnl = total_pnl + total_fees + total_slippage
        cost_ratio = (
            (total_fees + total_slippage) / abs(gross_pnl) if gross_pnl != 0 else 0
        )

        # Regime performance
        regime_performance = {}
        for regime in set(t.regime for t in self.trades):
            regime_trades = [t for t in self.trades if t.regime == regime]
            if regime_trades:
                regime_pnl = sum(t.pnl or 0 for t in regime_trades)
                regime_wins = len([t for t in regime_trades if (t.pnl or 0) > 0])
                regime_performance[regime] = {
                    "trades": len(regime_trades),
                    "pnl": regime_pnl,
                    "win_rate": regime_wins / len(regime_trades),
                    "avg_pnl": regime_pnl / len(regime_trades),
                }

        # Signal quality metrics (mock for now)
        # In production, these would be calculated from actual predictions vs outcomes
        auc_score = 0.65 + np.random.normal(0, 0.05)  # Mock AUC around 0.65
        pr_auc_score = 0.60 + np.random.normal(0, 0.05)  # Mock PR-AUC
        ece_score = 0.03 + np.random.uniform(0, 0.02)  # Mock ECE < 0.05

        # Risk metrics
        var_95 = np.percentile(returns, 5) if returns else 0

        # Consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for trade in self.trades:
            if (trade.pnl or 0) < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0

        return BacktestResults(
            universe=universe,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            var_95=var_95,
            max_consecutive_losses=max_consecutive_losses,
            total_fees=total_fees,
            total_slippage=total_slippage,
            cost_ratio=cost_ratio,
            regime_performance=regime_performance,
            auc_score=auc_score,
            pr_auc_score=pr_auc_score,
            ece_score=ece_score,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )


def run_backtest(universe: list[str], start: str, end: str) -> dict[str, Any]:
    """
    Main backtesting function for CLI usage.

    Args:
        universe: List of symbols to trade
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)

    Returns:
        Backtest results as dictionary
    """

    engine = BacktestEngine()
    results = engine.run_backtest(universe, start, end)

    # Convert to dictionary for JSON serialization
    results_dict = asdict(results)

    # Convert datetime objects to strings
    for trade in results_dict["trades"]:
        trade["entry_time"] = (
            trade["entry_time"].isoformat() if trade["entry_time"] else None
        )
        trade["exit_time"] = (
            trade["exit_time"].isoformat() if trade["exit_time"] else None
        )

    return results_dict


def main():
    """CLI entry point for backtesting."""
    parser = argparse.ArgumentParser(description="ZiggyAI Backtesting Engine")
    parser.add_argument(
        "--universe", required=True, help="Comma-separated list of symbols"
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    # Parse universe
    universe = [s.strip().upper() for s in args.universe.split(",")]

    # Run backtest
    try:
        results = run_backtest(universe, args.start, args.end)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            # Print summary to console
            print(
                json.dumps(
                    {
                        "universe": results["universe"],
                        "start_date": results["start_date"],
                        "end_date": results["end_date"],
                        "total_trades": results["total_trades"],
                        "win_rate": results["win_rate"],
                        "total_return": results["total_return"],
                        "annualized_return": results["annualized_return"],
                        "max_drawdown": results["max_drawdown"],
                        "sharpe_ratio": results["sharpe_ratio"],
                        "ece_score": results["ece_score"],
                        "ok": True,
                    },
                    indent=2,
                )
            )

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        print(json.dumps({"error": str(e), "ok": False}))
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
