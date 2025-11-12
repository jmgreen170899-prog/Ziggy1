"""
Backtesting Module - Historical Signal Validation

Comprehensive backtesting framework for market brain signals:
- Walk-forward backtesting with realistic execution
- Performance analytics and risk metrics
- Signal quality analysis and optimization
- Regime-aware testing and reporting

Supports both single-ticker and portfolio-level backtesting.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

# Note: FeatureComputer not used in this module currently
# from .features import FeatureComputer
from .regime import RegimeDetector
from .signals import SignalGenerator
from .sizer import PositionSizer, SizingMethod


logger = logging.getLogger(__name__)


class BacktestPeriod(Enum):
    """Predefined backtest periods."""

    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"
    FIVE_YEARS = "5Y"


@dataclass
class Trade:
    """Individual trade record in backtest."""

    ticker: str
    entry_date: datetime
    exit_date: datetime | None
    entry_price: float
    exit_price: float | None
    quantity: int
    side: str  # "LONG" or "SHORT"

    # Signal information
    signal_confidence: float
    signal_type: str
    entry_regime: str

    # Trade outcomes
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    hold_days: int = 0

    # Risk metrics
    max_drawdown: float = 0.0
    max_runup: float = 0.0

    # Exit reason
    exit_reason: str = "UNKNOWN"  # TAKE_PROFIT, STOP_LOSS, TIME_LIMIT, SIGNAL_EXIT

    def __post_init__(self):
        if self.exit_date and self.exit_price:
            # Calculate PnL
            if self.side == "LONG":
                self.pnl = (self.exit_price - self.entry_price) * self.quantity
            else:
                self.pnl = (self.entry_price - self.exit_price) * self.quantity

            self.pnl_percent = self.pnl / (self.entry_price * self.quantity) * 100
            self.hold_days = (self.exit_date - self.entry_date).days


@dataclass
class BacktestConfig:
    """Configuration for backtest run."""

    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000
    commission_per_trade: float = 1.0
    commission_percent: float = 0.001  # 0.1%

    # Position sizing
    sizing_method: SizingMethod = SizingMethod.VOLATILITY_TARGET
    max_position_size: float = 0.2  # 20% of capital
    max_positions: int = 10

    # Risk management
    global_stop_loss: float = 0.05  # 5% stop
    max_hold_days: int = 30
    daily_loss_limit: float = 0.02  # 2% daily loss limit

    # Signal filtering
    min_confidence: float = 0.5
    allowed_regimes: list[str] = field(default_factory=lambda: ["RISK_ON", "CHOP"])

    # Rebalancing
    rebalance_frequency: str = "daily"  # daily, weekly, monthly

    def __post_init__(self):
        if isinstance(self.allowed_regimes, list) and len(self.allowed_regimes) == 0:
            self.allowed_regimes = ["RISK_ON", "CHOP"]


@dataclass
class BacktestResults:
    """Comprehensive backtest results."""

    config: BacktestConfig
    trades: list[Trade]

    # Performance metrics
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0

    # Daily performance
    daily_returns: list[float] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    dates: list[datetime] = field(default_factory=list)

    # Risk metrics
    volatility: float = 0.0
    calmar_ratio: float = 0.0
    var_95: float = 0.0  # Value at Risk

    # Regime analysis
    regime_performance: dict[str, dict[str, float]] = field(default_factory=dict)

    def __post_init__(self):
        if self.trades:
            self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate all performance metrics."""
        if not self.trades:
            return

        # Basic trade stats
        self.total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]

        self.winning_trades = len(winning_trades)
        self.losing_trades = len(losing_trades)
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        if winning_trades:
            self.avg_win = np.mean([t.pnl for t in winning_trades])
        if losing_trades:
            self.avg_loss = np.mean([t.pnl for t in losing_trades])

        # Calculate total return
        total_pnl = sum(t.pnl for t in self.trades)
        self.total_return = total_pnl / self.config.initial_capital

        # Calculate daily returns and equity curve
        if self.daily_returns:
            self.annual_return = np.mean(self.daily_returns) * 252  # 252 trading days
            self.volatility = np.std(self.daily_returns) * np.sqrt(252)

            if self.volatility > 0:
                self.sharpe_ratio = self.annual_return / self.volatility

            # Calculate maximum drawdown
            equity = np.array(self.equity_curve)
            running_max = np.maximum.accumulate(equity)
            drawdown = (equity - running_max) / running_max
            self.max_drawdown = abs(np.min(drawdown))

            # Calmar ratio
            if self.max_drawdown > 0:
                self.calmar_ratio = self.annual_return / self.max_drawdown

            # Value at Risk (95th percentile)
            self.var_95 = np.percentile(self.daily_returns, 5)


class Backtester:
    """
    Market brain backtesting engine.

    Performs walk-forward backtesting of signals with realistic execution,
    commission costs, and risk management.
    """

    def __init__(self):
        """Initialize backtester."""
        self.signal_generator = SignalGenerator()
        self.position_sizer = PositionSizer()
        # Note: feature_computer not available in this module
        # self.feature_computer = FeatureComputer()
        self.regime_detector = RegimeDetector()

        logger.info("Backtester initialized")

    def run_backtest(self, tickers: list[str], config: BacktestConfig) -> BacktestResults:
        """
        Run comprehensive backtest.

        Args:
            tickers: List of tickers to test
            config: Backtest configuration

        Returns:
            BacktestResults with complete analysis
        """
        logger.info(
            f"Starting backtest: {len(tickers)} tickers, "
            f"{config.start_date.date()} to {config.end_date.date()}"
        )

        # Initialize results
        results = BacktestResults(config=config, trades=[])

        # Generate date range
        date_range = pd.date_range(start=config.start_date, end=config.end_date, freq="D")

        # Initialize portfolio state
        capital = config.initial_capital
        positions = {}  # ticker -> Trade (for open positions)
        daily_values = []
        daily_returns = []

        for current_date in date_range:
            # Skip weekends (basic market calendar)
            if current_date.weekday() >= 5:
                continue

            try:
                daily_value = self._process_trading_day(
                    current_date, tickers, config, positions, capital, results
                )

                daily_values.append(daily_value)
                if len(daily_values) > 1:
                    daily_return = (daily_value - daily_values[-2]) / daily_values[-2]
                    daily_returns.append(daily_return)
                else:
                    daily_returns.append(0.0)

                results.dates.append(current_date)

            except Exception as e:
                logger.warning(f"Error processing {current_date.date()}: {e}")
                continue

        # Store performance data
        results.equity_curve = daily_values
        results.daily_returns = daily_returns

        # Close any remaining positions
        self._close_all_positions(positions, results, config.end_date)

        logger.info(
            f"Backtest completed: {len(results.trades)} trades, "
            f"{results.total_return:.2%} total return"
        )

        return results

    def _process_trading_day(
        self,
        current_date: datetime,
        tickers: list[str],
        config: BacktestConfig,
        positions: dict[str, Trade],
        capital: float,
        results: BacktestResults,
    ) -> float:
        """Process a single trading day."""

        # Update capital based on current positions
        current_value = capital

        # Check exit conditions for existing positions
        to_close = []
        for ticker, trade in positions.items():
            try:
                # Get current price (simplified - would need historical data)
                market_data = get_market_data(ticker)
                if not market_data:
                    continue

                current_price = market_data.get("price", trade.entry_price)

                # Check exit conditions
                exit_reason = self._check_exit_conditions(
                    trade, current_price, current_date, config
                )
                if exit_reason:
                    trade.exit_date = current_date
                    trade.exit_price = current_price
                    trade.exit_reason = exit_reason
                    to_close.append(ticker)
                    results.trades.append(trade)

                    # Update capital
                    capital += trade.pnl - self._calculate_commission(trade, config)

                # Update current value
                if trade.side == "LONG":
                    current_value += (current_price - trade.entry_price) * trade.quantity
                else:
                    current_value += (trade.entry_price - current_price) * trade.quantity

            except Exception as e:
                logger.warning(f"Error checking exit for {ticker}: {e}")

        # Close marked positions
        for ticker in to_close:
            del positions[ticker]

        # Check for new signals if we have capacity
        if len(positions) < config.max_positions:
            self._check_new_signals(current_date, tickers, config, positions, capital)

        return current_value

    def _check_exit_conditions(
        self, trade: Trade, current_price: float, current_date: datetime, config: BacktestConfig
    ) -> str | None:
        """Check if position should be exited."""

        # Time-based exit
        if (current_date - trade.entry_date).days >= config.max_hold_days:
            return "TIME_LIMIT"

        # Global stop loss
        if trade.side == "LONG":
            loss_percent = (trade.entry_price - current_price) / trade.entry_price
        else:
            loss_percent = (current_price - trade.entry_price) / trade.entry_price

        if loss_percent >= config.global_stop_loss:
            return "STOP_LOSS"

        # Take profit (simplified - could use signal's take_profit)
        profit_percent = abs(loss_percent)
        if profit_percent >= 0.15:  # 15% take profit
            return "TAKE_PROFIT"

        return None

    def _check_new_signals(
        self,
        current_date: datetime,
        tickers: list[str],
        config: BacktestConfig,
        positions: dict[str, Trade],
        capital: float,
    ):
        """Check for new trading signals."""

        # Get current regime
        try:
            regime_result = self.regime_detector.detect_regime()
            current_regime = regime_result.regime.value
        except Exception:
            current_regime = "UNKNOWN"

        # Skip if regime not allowed
        if current_regime not in config.allowed_regimes:
            return

        # Check each ticker for signals
        for ticker in tickers:
            # Skip if already have position
            if ticker in positions:
                continue

            try:
                # Generate signal
                signal = self.signal_generator.generate_signal(ticker)
                if not signal or signal.confidence < config.min_confidence:
                    continue

                # Get features for position sizing
                # Note: feature computation not available in this module currently
                # features = self.feature_computer.get_features(ticker)
                # if not features:
                #     continue
                # For now, use a minimal features dict
                features = {"volatility_20d": 0.2}  # Placeholder

                # Calculate position size
                position_size = self.position_sizer.calculate_position_size(
                    signal, features, config.sizing_method
                )

                # Check position size limits
                position_value = position_size.quantity * signal.entry_price
                if position_value > capital * config.max_position_size:
                    continue

                # Create trade
                trade = Trade(
                    ticker=ticker,
                    entry_date=current_date,
                    exit_date=None,
                    entry_price=signal.entry_price,
                    exit_price=None,
                    quantity=position_size.quantity,
                    side=signal.direction.value,
                    signal_confidence=signal.confidence,
                    signal_type=signal.signal_type.value,
                    entry_regime=current_regime,
                )

                # Add to positions
                positions[ticker] = trade

                logger.debug(
                    f"Opened position: {ticker} {trade.side} {trade.quantity} @ ${trade.entry_price:.2f}"
                )

            except Exception as e:
                logger.warning(f"Error generating signal for {ticker}: {e}")

    def _close_all_positions(
        self, positions: dict[str, Trade], results: BacktestResults, end_date: datetime
    ):
        """Close all remaining positions at backtest end."""
        for ticker, trade in positions.items():
            try:
                # Get final price
                market_data = get_market_data(ticker)
                final_price = (
                    market_data.get("price", trade.entry_price)
                    if market_data
                    else trade.entry_price
                )

                trade.exit_date = end_date
                trade.exit_price = final_price
                trade.exit_reason = "BACKTEST_END"
                results.trades.append(trade)

            except Exception as e:
                logger.warning(f"Error closing position {ticker}: {e}")

    def _calculate_commission(self, trade: Trade, config: BacktestConfig) -> float:
        """Calculate commission for trade."""
        trade_value = trade.quantity * (trade.exit_price or trade.entry_price)
        commission = max(config.commission_per_trade, trade_value * config.commission_percent)
        return commission * 2  # Entry + exit

    def run_single_ticker_backtest(self, ticker: str, period: BacktestPeriod) -> BacktestResults:
        """Run backtest for single ticker over specified period."""

        # Calculate date range
        end_date = datetime.now()
        if period == BacktestPeriod.ONE_MONTH:
            start_date = end_date - timedelta(days=30)
        elif period == BacktestPeriod.THREE_MONTHS:
            start_date = end_date - timedelta(days=90)
        elif period == BacktestPeriod.SIX_MONTHS:
            start_date = end_date - timedelta(days=180)
        elif period == BacktestPeriod.ONE_YEAR:
            start_date = end_date - timedelta(days=365)
        elif period == BacktestPeriod.TWO_YEARS:
            start_date = end_date - timedelta(days=730)
        else:  # FIVE_YEARS
            start_date = end_date - timedelta(days=1825)

        config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            max_positions=1,  # Single ticker
        )

        return self.run_backtest([ticker], config)

    def analyze_signal_quality(self, ticker: str, period: BacktestPeriod) -> dict[str, Any]:
        """Analyze quality and consistency of signals for a ticker."""

        results = self.run_single_ticker_backtest(ticker, period)

        # Signal quality metrics
        if not results.trades:
            return {"error": "No trades generated"}

        # Group by signal type
        signal_analysis = {}
        for trade in results.trades:
            signal_type = trade.signal_type
            if signal_type not in signal_analysis:
                signal_analysis[signal_type] = {
                    "count": 0,
                    "wins": 0,
                    "total_pnl": 0.0,
                    "avg_confidence": 0.0,
                }

            signal_analysis[signal_type]["count"] += 1
            if trade.pnl > 0:
                signal_analysis[signal_type]["wins"] += 1
            signal_analysis[signal_type]["total_pnl"] += trade.pnl
            signal_analysis[signal_type]["avg_confidence"] += trade.signal_confidence

        # Calculate averages
        for signal_type, stats in signal_analysis.items():
            if stats["count"] > 0:
                stats["win_rate"] = stats["wins"] / stats["count"]
                stats["avg_pnl"] = stats["total_pnl"] / stats["count"]
                stats["avg_confidence"] /= stats["count"]

        return {
            "ticker": ticker,
            "period": period.value,
            "total_trades": len(results.trades),
            "overall_return": results.total_return,
            "win_rate": results.win_rate,
            "sharpe_ratio": results.sharpe_ratio,
            "signal_breakdown": signal_analysis,
        }


# Global backtester instance
backtester = Backtester()


def quick_backtest(
    ticker: str, period: BacktestPeriod = BacktestPeriod.THREE_MONTHS
) -> BacktestResults:
    """Quick backtest for a single ticker."""
    return backtester.run_single_ticker_backtest(ticker, period)


def analyze_signals(
    ticker: str, period: BacktestPeriod = BacktestPeriod.THREE_MONTHS
) -> dict[str, Any]:
    """Analyze signal quality for a ticker."""
    return backtester.analyze_signal_quality(ticker, period)
