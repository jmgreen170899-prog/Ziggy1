"""
Position Sizing Module for ZiggyAI Cognitive Core

Implements risk-aware position sizing using ATR, Kelly criterion, and account risk budgets.
Provides optimal position sizing with stop loss and take profit levels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Position sizing recommendation."""

    symbol: str
    quantity: int
    dollar_amount: float
    position_pct: float  # Percentage of account
    stop_loss: float
    take_profit: float
    risk_per_trade: float
    kelly_fraction: float
    atr_multiple: float
    confidence: float
    reasoning: str


@dataclass
class RiskBudget:
    """Risk budget parameters."""

    max_position_pct: float = 0.05  # Max 5% per position
    max_total_risk_pct: float = 0.20  # Max 20% total risk
    max_correlation_exposure: float = 0.30  # Max 30% in correlated positions
    max_sector_exposure: float = 0.25  # Max 25% in single sector
    max_daily_var: float = 0.02  # Max 2% daily VaR


class ATRCalculator:
    """Average True Range calculator for volatility-based sizing."""

    @staticmethod
    def calculate_atr(
        high_prices: list[float],
        low_prices: list[float],
        close_prices: list[float],
        period: int = 14,
    ) -> float:
        """
        Calculate Average True Range.

        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of close prices
            period: ATR period (default 14)

        Returns:
            ATR value
        """
        if len(high_prices) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(high_prices)):
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i - 1])
            tr3 = abs(low_prices[i] - close_prices[i - 1])
            true_ranges.append(max(tr1, tr2, tr3))

        # Calculate ATR as simple moving average of true ranges
        if len(true_ranges) >= period:
            return np.mean(true_ranges[-period:])
        else:
            return np.mean(true_ranges)

    @staticmethod
    def mock_atr(symbol: str, volatility: float = 0.20) -> float:
        """Generate mock ATR for testing."""
        # Base ATR around 2% of price with volatility adjustment
        base_atr = 2.0 * (1.0 + volatility)
        # Add symbol-specific noise for realism
        symbol_hash = hash(symbol) % 1000
        noise = (symbol_hash / 1000.0 - 0.5) * 0.5
        return max(0.5, base_atr + noise)


class KellyCalculator:
    """Kelly Criterion calculator for optimal position sizing."""

    @staticmethod
    def calculate_kelly_fraction(
        win_probability: float, avg_win: float, avg_loss: float, confidence: float = 1.0
    ) -> float:
        """
        Calculate Kelly fraction.

        Formula: f = (bp - q) / b
        Where:
        - f = Kelly fraction
        - b = odds (avg_win / avg_loss)
        - p = win probability
        - q = loss probability (1 - p)

        Args:
            win_probability: Probability of winning trade
            avg_win: Average winning amount
            avg_loss: Average losing amount (positive)
            confidence: Confidence multiplier (0-1)

        Returns:
            Kelly fraction (should be capped)
        """
        if avg_loss <= 0 or win_probability <= 0 or win_probability >= 1:
            return 0.0

        b = avg_win / avg_loss  # Odds
        p = win_probability
        q = 1 - p

        kelly_f = (b * p - q) / b

        # Apply confidence multiplier and cap
        adjusted_kelly = kelly_f * confidence

        # Cap Kelly at reasonable levels (25% max)
        return max(0.0, min(0.25, adjusted_kelly))

    @staticmethod
    def kelly_from_signal(
        signal_probability: float,
        confidence: float,
        historical_performance: dict[str, float] | None = None,
    ) -> float:
        """
        Calculate Kelly fraction from trading signal.

        Args:
            signal_probability: Model probability (0-1)
            confidence: Signal confidence (0-1)
            historical_performance: Historical win/loss stats

        Returns:
            Kelly fraction
        """
        # Use historical performance or defaults
        if historical_performance:
            avg_win = historical_performance.get("avg_win", 1.5)
            avg_loss = historical_performance.get("avg_loss", 1.0)
            base_win_rate = historical_performance.get("win_rate", 0.55)
        else:
            avg_win = 1.5  # Default: wins are 1.5x larger than losses
            avg_loss = 1.0
            base_win_rate = 0.55  # Default 55% win rate

        # Adjust win probability based on signal strength
        signal_strength = abs(signal_probability - 0.5) * 2  # 0 to 1
        adjusted_win_prob = base_win_rate + (
            signal_strength * 0.1 * (1 if signal_probability > 0.5 else -1)
        )
        adjusted_win_prob = max(0.1, min(0.9, adjusted_win_prob))

        return KellyCalculator.calculate_kelly_fraction(
            adjusted_win_prob, avg_win, avg_loss, confidence
        )


class PositionSizer:
    """Main position sizing calculator."""

    def __init__(self, risk_budget: RiskBudget | None = None):
        """Initialize position sizer."""
        self.risk_budget = risk_budget or RiskBudget()
        self.atr_calc = ATRCalculator()
        self.kelly_calc = KellyCalculator()

    def compute_position(
        self,
        symbol: str,
        account_equity: float,
        current_price: float,
        signal_probability: float,
        signal_confidence: float,
        atr: float | None = None,
        volatility: float | None = None,
        historical_performance: dict[str, float] | None = None,
        existing_positions: dict[str, dict[str, Any]] | None = None,
    ) -> PositionSize:
        """
        Compute optimal position size.

        Args:
            symbol: Trading symbol
            account_equity: Current account equity
            current_price: Current stock price
            signal_probability: Model probability of up move
            signal_confidence: Confidence in signal (0-1)
            atr: Average True Range (if None, will be estimated)
            volatility: Stock volatility (if None, will be estimated)
            historical_performance: Historical trading stats
            existing_positions: Current positions for risk management

        Returns:
            Position sizing recommendation
        """

        # Estimate missing values
        if volatility is None:
            volatility = 0.20  # Default 20% volatility

        if atr is None:
            atr = self.atr_calc.mock_atr(symbol, volatility)

        # Base risk per trade (1% of equity default)
        base_risk_pct = 0.01
        risk_per_trade = account_equity * base_risk_pct

        # Calculate Kelly fraction
        kelly_fraction = self.kelly_calc.kelly_from_signal(
            signal_probability, signal_confidence, historical_performance
        )

        # ATR-based stop distance (2x ATR default)
        atr_multiple = 2.0
        stop_distance = atr * atr_multiple

        # Position size based on risk
        # Quantity = Risk Amount / Stop Distance
        base_quantity = int(risk_per_trade / stop_distance) if stop_distance > 0 else 0

        # Apply Kelly sizing adjustment
        kelly_adjusted_quantity = int(base_quantity * (1 + kelly_fraction))

        # Apply confidence adjustment
        confidence_multiplier = 0.5 + (signal_confidence * 0.5)  # 0.5 to 1.0
        final_quantity = int(kelly_adjusted_quantity * confidence_multiplier)

        # Apply position limits
        max_position_value = account_equity * self.risk_budget.max_position_pct
        max_quantity_by_value = int(max_position_value / current_price)
        final_quantity = min(final_quantity, max_quantity_by_value)

        # Apply existing position constraints
        if existing_positions:
            final_quantity = self._apply_risk_constraints(
                final_quantity, symbol, current_price, account_equity, existing_positions
            )

        # Ensure minimum viable quantity
        final_quantity = max(0, final_quantity)

        # Calculate levels
        dollar_amount = final_quantity * current_price
        position_pct = dollar_amount / account_equity if account_equity > 0 else 0

        # Stop loss and take profit
        if signal_probability > 0.5:  # Long position
            stop_loss = current_price - stop_distance
            take_profit = current_price + (stop_distance * 2)  # 2:1 reward/risk
        else:  # Short position (negative quantity)
            final_quantity = -abs(final_quantity)  # Make negative for short
            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * 2)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal_probability,
            signal_confidence,
            kelly_fraction,
            atr_multiple,
            position_pct,
            base_risk_pct,
        )

        return PositionSize(
            symbol=symbol,
            quantity=final_quantity,
            dollar_amount=abs(dollar_amount),
            position_pct=position_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_per_trade=risk_per_trade,
            kelly_fraction=kelly_fraction,
            atr_multiple=atr_multiple,
            confidence=signal_confidence,
            reasoning=reasoning,
        )

    def _apply_risk_constraints(
        self,
        quantity: int,
        symbol: str,
        price: float,
        account_equity: float,
        existing_positions: dict[str, dict[str, Any]],
    ) -> int:
        """Apply portfolio-level risk constraints."""

        # Calculate total exposure after this position
        new_position_value = abs(quantity * price)
        total_exposure = new_position_value

        for pos_symbol, position in existing_positions.items():
            if pos_symbol != symbol:  # Don't double-count if updating existing position
                pos_value = abs(position.get("quantity", 0) * position.get("price", 0))
                total_exposure += pos_value

        # Check total risk budget
        max_total_exposure = account_equity * self.risk_budget.max_total_risk_pct
        if total_exposure > max_total_exposure:
            # Reduce position to fit within total risk budget
            available_budget = max_total_exposure - (total_exposure - new_position_value)
            if available_budget > 0:
                max_quantity = int(available_budget / price)
                quantity = min(quantity, max_quantity)
            else:
                quantity = 0

        # Additional constraints could be added here:
        # - Sector exposure limits
        # - Correlation limits
        # - Concentration limits

        return quantity

    def _generate_reasoning(
        self,
        signal_prob: float,
        confidence: float,
        kelly_fraction: float,
        atr_multiple: float,
        position_pct: float,
        base_risk_pct: float,
    ) -> str:
        """Generate human-readable reasoning for position size."""

        direction = "Long" if signal_prob > 0.5 else "Short"
        signal_strength = abs(signal_prob - 0.5) * 2

        parts = [
            f"{direction} signal with {signal_strength:.1%} strength",
            f"{confidence:.1%} confidence",
            f"Kelly fraction: {kelly_fraction:.2%}",
            f"ATR stop: {atr_multiple}x",
            f"Position size: {position_pct:.1%} of account",
            f"Base risk: {base_risk_pct:.1%} per trade",
        ]

        return " | ".join(parts)

    def calculate_portfolio_risk(
        self,
        positions: dict[str, PositionSize],
        correlations: dict[tuple[str, str], float] | None = None,
    ) -> dict[str, float]:
        """
        Calculate portfolio-level risk metrics.

        Args:
            positions: Dictionary of position sizes by symbol
            correlations: Pairwise correlations between symbols

        Returns:
            Dictionary of risk metrics
        """

        if not positions:
            return {"total_var": 0.0, "diversification_ratio": 1.0}

        # Simple portfolio risk calculation
        total_exposure = sum(pos.dollar_amount for pos in positions.values())
        position_weights = {
            symbol: pos.dollar_amount / total_exposure for symbol, pos in positions.items()
        }

        # Individual position variances (simplified)
        individual_vars = {}
        for symbol, position in positions.items():
            # Estimate variance from position characteristics
            vol_estimate = 0.20  # Default 20% volatility
            var_estimate = (vol_estimate**2) * (position_weights[symbol] ** 2)
            individual_vars[symbol] = var_estimate

        # Portfolio variance (without correlations, assumes independence)
        if correlations is None:
            portfolio_var = sum(individual_vars.values())
        else:
            # Full covariance calculation
            portfolio_var = 0.0
            symbols = list(positions.keys())

            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i == j:
                        # Variance term
                        portfolio_var += individual_vars[symbol1]
                    else:
                        # Covariance term
                        corr = correlations.get((symbol1, symbol2), 0.0)
                        cov = corr * np.sqrt(individual_vars[symbol1] * individual_vars[symbol2])
                        portfolio_var += (
                            2 * position_weights[symbol1] * position_weights[symbol2] * cov
                        )

        # Diversification ratio
        sum_individual_risk = sum(
            np.sqrt(var) * weight
            for (symbol, var), weight in zip(individual_vars.items(), position_weights.values())
        )
        portfolio_risk = np.sqrt(portfolio_var)
        diversification_ratio = sum_individual_risk / portfolio_risk if portfolio_risk > 0 else 1.0

        return {
            "total_var": portfolio_var,
            "portfolio_volatility": portfolio_risk,
            "diversification_ratio": diversification_ratio,
            "individual_vars": individual_vars,
            "position_weights": position_weights,
        }


def compute_position(
    account_equity: float,
    symbol: str,
    current_price: float,
    signal_probability: float,
    signal_confidence: float,
    atr: float | None = None,
    kelly_edge: float | None = None,
    risk_budget: float = 0.01,
) -> dict[str, Any]:
    """
    Convenience function for position sizing computation.

    This matches the API specified in the original requirements.

    Args:
        account_equity: Current account equity
        symbol: Trading symbol (added for context)
        current_price: Current stock price (added for calculations)
        signal_probability: Probability signal (replaces kelly_edge concept)
        signal_confidence: Confidence in signal
        atr: Average True Range
        kelly_edge: Legacy parameter (ignored, use signal_probability)
        risk_budget: Risk budget percentage

    Returns:
        Dictionary with qty, stop, take_profit
    """

    sizer = PositionSizer(RiskBudget(max_position_pct=risk_budget * 5))

    position = sizer.compute_position(
        symbol=symbol,
        account_equity=account_equity,
        current_price=current_price,
        signal_probability=signal_probability,
        signal_confidence=signal_confidence,
        atr=atr,
    )

    return {
        "qty": position.quantity,
        "stop": position.stop_loss,
        "take_profit": position.take_profit,
        "dollar_amount": position.dollar_amount,
        "position_pct": position.position_pct,
        "kelly_fraction": position.kelly_fraction,
        "reasoning": position.reasoning,
    }


__all__ = [
    "ATRCalculator",
    "KellyCalculator",
    "PositionSize",
    "PositionSizer",
    "RiskBudget",
    "compute_position",
]
