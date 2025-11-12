"""
Position Sizing Module

Computes position sizes using volatility targeting and risk management.
Implements Kelly Criterion, volatility targeting, and portfolio risk limits.

Key features:
- Volatility-based position sizing
- Account equity risk limits
- Stop loss and take profit calculation
- Position validation and guardrails
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .features import FeatureSet
from .signals import Signal, SignalDirection


logger = logging.getLogger(__name__)


class SizingMethod(Enum):
    """Position sizing methodologies."""

    FIXED_DOLLAR = "FixedDollar"
    FIXED_PERCENT = "FixedPercent"
    VOLATILITY_TARGET = "VolatilityTarget"
    KELLY_CRITERION = "KellyCriterion"
    ATR_BASED = "ATRBased"


@dataclass
class PositionSize:
    """
    Complete position sizing result.

    Contains all information needed to execute a trade including
    position size, risk metrics, and validation status.
    """

    ticker: str
    direction: SignalDirection

    # Position sizing
    quantity: int
    dollar_amount: float
    position_value: float

    # Price levels
    entry_price: float
    stop_loss: float | None
    take_profit: float | None

    # Risk metrics
    risk_per_share: float
    total_risk_dollar: float
    total_risk_percent: float  # % of account
    reward_dollar: float | None
    risk_reward_ratio: float | None

    # Volatility metrics
    target_volatility: float
    expected_volatility: float
    atr_multiple: float

    # Validation
    is_valid: bool
    validation_errors: list
    sizing_method: SizingMethod

    # Context
    timestamp: datetime
    account_size: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            "ticker": self.ticker,
            "direction": self.direction.value,
            "position": {
                "quantity": self.quantity,
                "dollar_amount": self.dollar_amount,
                "position_value": self.position_value,
                "entry_price": self.entry_price,
            },
            "price_levels": {"stop_loss": self.stop_loss, "take_profit": self.take_profit},
            "risk_metrics": {
                "risk_per_share": self.risk_per_share,
                "total_risk_dollar": self.total_risk_dollar,
                "total_risk_percent": self.total_risk_percent,
                "reward_dollar": self.reward_dollar,
                "risk_reward_ratio": self.risk_reward_ratio,
            },
            "volatility": {
                "target_volatility": self.target_volatility,
                "expected_volatility": self.expected_volatility,
                "atr_multiple": self.atr_multiple,
            },
            "validation": {
                "is_valid": self.is_valid,
                "errors": self.validation_errors,
                "sizing_method": self.sizing_method.value,
            },
            "context": {
                "timestamp": self.timestamp.isoformat(),
                "account_size": self.account_size,
                "confidence": self.confidence,
            },
        }


class PositionSizer:
    """
    Position sizing engine with multiple methodologies.

    Supports various position sizing approaches:
    1. Volatility targeting (default)
    2. Fixed percentage of portfolio
    3. Kelly Criterion optimization
    4. ATR-based sizing
    """

    def __init__(self, account_size: float = 100000.0):
        self.account_size = account_size

        # Risk management parameters
        self.config = {
            # Target portfolio volatility (annualized)
            "target_volatility": 0.15,  # 15%
            # Maximum risk per trade (% of account)
            "max_risk_per_trade": 0.02,  # 2%
            # Minimum position size (shares)
            "min_position_shares": 1,
            # Maximum position size (% of account)
            "max_position_percent": 0.10,  # 10%
            # ATR multiples for stops/targets
            "stop_loss_atr_multiple": 2.0,
            "take_profit_atr_multiple": 3.0,
            # Kelly Criterion parameters
            "kelly_win_rate_default": 0.55,
            "kelly_avg_win_default": 0.08,
            "kelly_avg_loss_default": 0.04,
            "kelly_max_allocation": 0.25,  # Cap Kelly at 25%
            # Transaction costs
            "commission_per_share": 0.005,
            "bid_ask_spread_bps": 5.0,  # 5 basis points
        }

    def calculate_position_size(
        self,
        signal: Signal,
        features: FeatureSet,
        method: SizingMethod = SizingMethod.VOLATILITY_TARGET,
    ) -> PositionSize:
        """
        Calculate optimal position size for a signal.

        Args:
            signal: Trading signal with direction and confidence
            features: Market features for volatility calculation
            method: Sizing methodology to use

        Returns:
            PositionSize object with complete sizing information
        """

        validation_errors = []

        try:
            # Validate inputs
            if not self._validate_inputs(signal, features, validation_errors):
                return self._create_invalid_position(signal, features, validation_errors, method)

            # Calculate position size based on method
            if method == SizingMethod.VOLATILITY_TARGET:
                position = self._volatility_target_sizing(signal, features)
            elif method == SizingMethod.KELLY_CRITERION:
                position = self._kelly_criterion_sizing(signal, features)
            elif method == SizingMethod.ATR_BASED:
                position = self._atr_based_sizing(signal, features)
            elif method == SizingMethod.FIXED_PERCENT:
                position = self._fixed_percent_sizing(signal, features)
            else:
                position = self._volatility_target_sizing(signal, features)  # Default

            # Apply risk management guardrails
            position = self._apply_risk_guardrails(position)

            # Final validation
            position.is_valid = self._validate_final_position(position, validation_errors)
            position.validation_errors = validation_errors

            return position

        except Exception as e:
            logger.error(f"Error calculating position size for {signal.ticker}: {e}")
            validation_errors.append(f"Calculation error: {e!s}")
            return self._create_invalid_position(signal, features, validation_errors, method)

    def _volatility_target_sizing(self, signal: Signal, features: FeatureSet) -> PositionSize:
        """Position sizing using volatility targeting."""

        # Calculate expected volatility
        daily_vol = features.volatility_20d / 100  # Convert from percentage

        # Target dollar volatility for this position
        target_portfolio_vol = self.config["target_volatility"]
        target_position_vol = target_portfolio_vol * 0.5  # Conservative allocation
        target_dollar_vol = self.account_size * target_position_vol

        # Position size to achieve target volatility
        position_value = target_dollar_vol / daily_vol

        # Convert to shares
        quantity = int(position_value / signal.entry_price)

        # Calculate actual position metrics
        actual_position_value = quantity * signal.entry_price
        actual_dollar_vol = actual_position_value * daily_vol

        # Risk calculation
        if signal.stop_loss:
            risk_per_share = abs(signal.entry_price - signal.stop_loss)
            total_risk_dollar = quantity * risk_per_share
        else:
            # Use ATR-based stop if no stop provided
            risk_per_share = features.atr_14 * self.config["stop_loss_atr_multiple"]
            total_risk_dollar = quantity * risk_per_share
            stop_loss = (
                signal.entry_price - risk_per_share
                if signal.direction == SignalDirection.LONG
                else signal.entry_price + risk_per_share
            )

        total_risk_percent = total_risk_dollar / self.account_size

        # Reward calculation
        reward_dollar = None
        risk_reward_ratio = None
        if signal.take_profit:
            reward_per_share = abs(signal.take_profit - signal.entry_price)
            reward_dollar = quantity * reward_per_share
            risk_reward_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else None

        return PositionSize(
            ticker=signal.ticker,
            direction=signal.direction,
            quantity=quantity,
            dollar_amount=actual_position_value,
            position_value=actual_position_value,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            risk_per_share=risk_per_share,
            total_risk_dollar=total_risk_dollar,
            total_risk_percent=total_risk_percent,
            reward_dollar=reward_dollar,
            risk_reward_ratio=risk_reward_ratio,
            target_volatility=target_position_vol,
            expected_volatility=daily_vol,
            atr_multiple=self.config["stop_loss_atr_multiple"],
            is_valid=True,
            validation_errors=[],
            sizing_method=SizingMethod.VOLATILITY_TARGET,
            timestamp=datetime.now(),
            account_size=self.account_size,
            confidence=signal.confidence,
        )

    def _kelly_criterion_sizing(self, signal: Signal, features: FeatureSet) -> PositionSize:
        """Position sizing using Kelly Criterion."""

        # Get historical performance or use defaults
        win_rate = signal.confidence or self.config["kelly_win_rate_default"]
        avg_win = self.config["kelly_avg_win_default"]
        avg_loss = self.config["kelly_avg_loss_default"]

        # Kelly formula: f = (bp - q) / b
        # where b = odds received on the wager, p = probability of win, q = probability of loss
        b = avg_win / avg_loss  # Odds ratio
        p = win_rate
        q = 1 - win_rate

        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(0, min(kelly_fraction, self.config["kelly_max_allocation"]))

        # Calculate position size
        position_value = self.account_size * kelly_fraction
        quantity = int(position_value / signal.entry_price)

        # Use standard risk calculation for other metrics
        return self._calculate_standard_metrics(
            signal, features, quantity, SizingMethod.KELLY_CRITERION
        )

    def _atr_based_sizing(self, signal: Signal, features: FeatureSet) -> PositionSize:
        """Position sizing based on ATR and fixed risk amount."""

        # Fixed risk amount per trade
        risk_amount = self.account_size * self.config["max_risk_per_trade"]

        # Risk per share based on ATR
        atr_stop_distance = features.atr_14 * self.config["stop_loss_atr_multiple"]

        # Position size to achieve target risk
        quantity = int(risk_amount / atr_stop_distance)

        return self._calculate_standard_metrics(signal, features, quantity, SizingMethod.ATR_BASED)

    def _fixed_percent_sizing(self, signal: Signal, features: FeatureSet) -> PositionSize:
        """Fixed percentage of portfolio sizing."""

        allocation_percent = 0.05  # 5% of portfolio
        position_value = self.account_size * allocation_percent
        quantity = int(position_value / signal.entry_price)

        return self._calculate_standard_metrics(
            signal, features, quantity, SizingMethod.FIXED_PERCENT
        )

    def _calculate_standard_metrics(
        self, signal: Signal, features: FeatureSet, quantity: int, method: SizingMethod
    ) -> PositionSize:
        """Calculate standard position metrics for any sizing method."""

        actual_position_value = quantity * signal.entry_price

        # Risk calculation
        if signal.stop_loss:
            risk_per_share = abs(signal.entry_price - signal.stop_loss)
        else:
            risk_per_share = features.atr_14 * self.config["stop_loss_atr_multiple"]

        total_risk_dollar = quantity * risk_per_share
        total_risk_percent = total_risk_dollar / self.account_size

        # Reward calculation
        reward_dollar = None
        risk_reward_ratio = None
        if signal.take_profit:
            reward_per_share = abs(signal.take_profit - signal.entry_price)
            reward_dollar = quantity * reward_per_share
            risk_reward_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else None

        # Volatility metrics
        daily_vol = features.volatility_20d / 100
        target_vol = total_risk_dollar / self.account_size

        return PositionSize(
            ticker=signal.ticker,
            direction=signal.direction,
            quantity=quantity,
            dollar_amount=actual_position_value,
            position_value=actual_position_value,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            risk_per_share=risk_per_share,
            total_risk_dollar=total_risk_dollar,
            total_risk_percent=total_risk_percent,
            reward_dollar=reward_dollar,
            risk_reward_ratio=risk_reward_ratio,
            target_volatility=target_vol,
            expected_volatility=daily_vol,
            atr_multiple=self.config["stop_loss_atr_multiple"],
            is_valid=True,
            validation_errors=[],
            sizing_method=method,
            timestamp=datetime.now(),
            account_size=self.account_size,
            confidence=signal.confidence,
        )

    def _apply_risk_guardrails(self, position: PositionSize) -> PositionSize:
        """Apply risk management guardrails."""

        # Maximum risk per trade check
        if position.total_risk_percent > self.config["max_risk_per_trade"]:
            # Scale down position
            scale_factor = self.config["max_risk_per_trade"] / position.total_risk_percent
            position.quantity = int(position.quantity * scale_factor)

            # Recalculate metrics
            position.position_value = position.quantity * position.entry_price
            position.dollar_amount = position.position_value
            position.total_risk_dollar = position.quantity * position.risk_per_share
            position.total_risk_percent = position.total_risk_dollar / self.account_size

        # Maximum position size check
        max_position_value = self.account_size * self.config["max_position_percent"]
        if position.position_value > max_position_value:
            position.quantity = int(max_position_value / position.entry_price)
            position.position_value = position.quantity * position.entry_price
            position.dollar_amount = position.position_value
            position.total_risk_dollar = position.quantity * position.risk_per_share
            position.total_risk_percent = position.total_risk_dollar / self.account_size

        # Minimum position size check
        if position.quantity < self.config["min_position_shares"]:
            position.quantity = self.config["min_position_shares"]
            position.position_value = position.quantity * position.entry_price
            position.dollar_amount = position.position_value
            position.total_risk_dollar = position.quantity * position.risk_per_share
            position.total_risk_percent = position.total_risk_dollar / self.account_size

        return position

    def _validate_inputs(self, signal: Signal, features: FeatureSet, errors: list) -> bool:
        """Validate inputs for position sizing."""

        valid = True

        if not signal.entry_price or signal.entry_price <= 0:
            errors.append("Invalid entry price")
            valid = False

        if not features.atr_14 or features.atr_14 <= 0:
            errors.append("Invalid ATR value")
            valid = False

        if not features.volatility_20d or features.volatility_20d <= 0:
            errors.append("Invalid volatility data")
            valid = False

        if signal.direction == SignalDirection.FLAT:
            errors.append("No trade signal direction")
            valid = False

        return valid

    def _validate_final_position(self, position: PositionSize, errors: list) -> bool:
        """Final validation of calculated position."""

        valid = True

        if position.quantity <= 0:
            errors.append("Invalid position quantity")
            valid = False

        if position.total_risk_percent > self.config["max_risk_per_trade"] * 1.1:  # 10% tolerance
            errors.append(f"Risk too high: {position.total_risk_percent:.1%}")
            valid = False

        if position.position_value > self.account_size * self.config["max_position_percent"] * 1.1:
            errors.append("Position size too large")
            valid = False

        return valid

    def _create_invalid_position(
        self, signal: Signal, features: FeatureSet, errors: list, method: SizingMethod
    ) -> PositionSize:
        """Create invalid position object for error cases."""

        return PositionSize(
            ticker=signal.ticker,
            direction=signal.direction,
            quantity=0,
            dollar_amount=0.0,
            position_value=0.0,
            entry_price=signal.entry_price or 0.0,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            risk_per_share=0.0,
            total_risk_dollar=0.0,
            total_risk_percent=0.0,
            reward_dollar=None,
            risk_reward_ratio=None,
            target_volatility=0.0,
            expected_volatility=0.0,
            atr_multiple=0.0,
            is_valid=False,
            validation_errors=errors,
            sizing_method=method,
            timestamp=datetime.now(),
            account_size=self.account_size,
            confidence=signal.confidence or 0.0,
        )

    def update_account_size(self, new_size: float):
        """Update account size for position calculations."""
        self.account_size = new_size

    def update_config(self, new_config: dict[str, Any]):
        """Update position sizing configuration."""
        self.config.update(new_config)


# Global position sizer instance
position_sizer = PositionSizer()


def calculate_position_for_signal(
    signal: Signal, features: FeatureSet, method: SizingMethod = SizingMethod.VOLATILITY_TARGET
) -> PositionSize:
    """Convenience function to calculate position size."""
    return position_sizer.calculate_position_size(signal, features, method)
