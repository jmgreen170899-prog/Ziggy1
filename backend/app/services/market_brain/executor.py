"""
Trade Executor Module - Signal Execution Interface

Handles trade execution for market brain signals:
- Interface with existing trading infrastructure
- Risk checks and validation
- Order management and tracking
- Execution reporting

This module bridges the market brain system with the trading system.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .signals import Signal
from .sizer import PositionSize


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of trade execution."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL_FILL = "partial_fill"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


class OrderSide(Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass
class ExecutionRequest:
    """Trade execution request combining signal and position size."""

    signal: Signal
    position_size: PositionSize
    ticker: str
    order_type: str = "market"  # market, limit, stop
    limit_price: float | None = None
    time_in_force: str = "DAY"  # DAY, GTC, IOC
    dry_run: bool = True  # Safety default

    # Risk override flags
    force_execution: bool = False
    skip_risk_checks: bool = False


@dataclass
class ExecutionResult:
    """Result of trade execution attempt."""

    request_id: str
    ticker: str
    status: ExecutionStatus
    order_id: str | None = None
    filled_quantity: int = 0
    filled_price: float | None = None
    executed_value: float = 0.0
    commission: float = 0.0
    timestamp: datetime = None

    # Risk and validation results
    risk_checks_passed: bool = True
    validation_errors: list[str] = None
    warnings: list[str] = None

    # Execution details
    order_side: OrderSide | None = None
    entry_signal: Signal | None = None
    position_size_used: PositionSize | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.validation_errors is None:
            self.validation_errors = []
        if self.warnings is None:
            self.warnings = []


class TradeExecutor:
    """
    Trade execution engine for market brain signals.

    Validates signals, performs risk checks, and interfaces with
    the trading system to execute orders.
    """

    def __init__(self, trading_adapter=None, max_position_size: float = 100000):
        """
        Initialize executor.

        Args:
            trading_adapter: Trading system adapter (optional)
            max_position_size: Maximum position size limit
        """
        self.trading_adapter = trading_adapter
        self.max_position_size = max_position_size
        self.execution_history: list[ExecutionResult] = []

        # Risk parameters
        self.max_daily_trades = 10
        self.max_daily_risk = 0.05  # 5% of account
        self.daily_trades_count = 0
        self.daily_risk_used = 0.0

        logger.info("TradeExecutor initialized")

    def execute_signal(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a trading signal.

        Args:
            request: ExecutionRequest with signal and position details

        Returns:
            ExecutionResult with execution status and details
        """
        request_id = f"{request.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Executing signal for {request.ticker} - ID: {request_id}")

        # Create initial result
        result = ExecutionResult(
            request_id=request_id,
            ticker=request.ticker,
            status=ExecutionStatus.PENDING,
            entry_signal=request.signal,
            position_size_used=request.position_size,
        )

        try:
            # Step 1: Validate request
            if not self._validate_request(request, result):
                result.status = ExecutionStatus.REJECTED
                return result

            # Step 2: Risk checks
            if not request.skip_risk_checks and not self._perform_risk_checks(
                request, result
            ):
                result.status = ExecutionStatus.REJECTED
                return result

            # Step 3: Prepare order details
            order_details = self._prepare_order(request, result)
            if not order_details:
                result.status = ExecutionStatus.ERROR
                result.validation_errors.append("Failed to prepare order details")
                return result

            # Step 4: Execute order
            if request.dry_run:
                result = self._simulate_execution(request, result, order_details)
            else:
                result = self._execute_real_order(request, result, order_details)

        except Exception as e:
            logger.error(f"Execution error for {request.ticker}: {e}")
            result.status = ExecutionStatus.ERROR
            result.validation_errors.append(f"Execution exception: {e!s}")

        # Store execution history
        self.execution_history.append(result)

        logger.info(
            f"Execution completed for {request.ticker} - Status: {result.status.value}"
        )
        return result

    def _validate_request(
        self, request: ExecutionRequest, result: ExecutionResult
    ) -> bool:
        """Validate execution request."""

        # Check signal validity
        if not request.signal or not request.signal.ticker:
            result.validation_errors.append("Invalid signal provided")
            return False

        # Check position size
        if not request.position_size or request.position_size.quantity == 0:
            result.validation_errors.append("Invalid position size")
            return False

        # Check ticker match
        if request.ticker != request.signal.ticker:
            result.validation_errors.append(
                "Ticker mismatch between request and signal"
            )
            return False

        # Check order type
        if request.order_type not in ["market", "limit", "stop"]:
            result.validation_errors.append(
                f"Unsupported order type: {request.order_type}"
            )
            return False

        # Check limit price for limit orders
        if request.order_type == "limit" and request.limit_price is None:
            result.validation_errors.append("Limit price required for limit orders")
            return False

        return True

    def _perform_risk_checks(
        self, request: ExecutionRequest, result: ExecutionResult
    ) -> bool:
        """Perform risk validation checks."""

        # Daily trade limit
        if self.daily_trades_count >= self.max_daily_trades:
            result.validation_errors.append(
                f"Daily trade limit exceeded ({self.max_daily_trades})"
            )
            return False

        # Position size limit
        position_value = request.position_size.quantity * request.signal.entry_price
        if position_value > self.max_position_size:
            result.validation_errors.append(
                f"Position size too large: ${position_value:,.0f} > ${self.max_position_size:,.0f}"
            )
            return False

        # Daily risk limit
        estimated_risk = request.position_size.risk_percent or 0.01
        if self.daily_risk_used + estimated_risk > self.max_daily_risk:
            result.validation_errors.append("Daily risk limit would be exceeded")
            return False

        # Signal confidence check
        if request.signal.confidence and request.signal.confidence < 0.3:
            result.warnings.append(
                f"Low signal confidence: {request.signal.confidence:.2f}"
            )

        return True

    def _prepare_order(
        self, request: ExecutionRequest, result: ExecutionResult
    ) -> dict[str, Any] | None:
        """Prepare order details for execution."""

        # Determine order side
        if request.signal.direction.value == "LONG":
            order_side = OrderSide.BUY
        else:
            order_side = OrderSide.SELL

        result.order_side = order_side

        # Get current market price for validation
        try:
            market_data = get_market_data(request.ticker)
            if not market_data or not market_data.get("price"):
                logger.warning(f"Could not get market data for {request.ticker}")
                return None

            current_price = market_data["price"]
        except Exception as e:
            logger.warning(f"Error getting market data for {request.ticker}: {e}")
            current_price = request.signal.entry_price

        # Prepare order details
        order_details = {
            "ticker": request.ticker,
            "side": order_side.value,
            "quantity": request.position_size.quantity,
            "order_type": request.order_type,
            "time_in_force": request.time_in_force,
            "current_price": current_price,
        }

        # Add price for limit orders
        if request.order_type == "limit":
            order_details["limit_price"] = request.limit_price

        return order_details

    def _simulate_execution(
        self,
        request: ExecutionRequest,
        result: ExecutionResult,
        order_details: dict[str, Any],
    ) -> ExecutionResult:
        """Simulate order execution for dry run."""

        # Use current market price or entry price
        execution_price = order_details.get("current_price", request.signal.entry_price)

        # Simulate full fill
        result.status = ExecutionStatus.FILLED
        result.filled_quantity = request.position_size.quantity
        result.filled_price = execution_price
        result.executed_value = result.filled_quantity * execution_price
        result.commission = self._calculate_commission(result.executed_value)

        # Update counters (even for simulation)
        self.daily_trades_count += 1
        self.daily_risk_used += request.position_size.risk_percent or 0.01

        logger.info(
            f"SIMULATED execution: {request.ticker} {order_details['side']} "
            f"{result.filled_quantity} @ ${execution_price:.2f}"
        )

        return result

    def _execute_real_order(
        self,
        request: ExecutionRequest,
        result: ExecutionResult,
        order_details: dict[str, Any],
    ) -> ExecutionResult:
        """Execute real order through trading adapter."""

        if not self.trading_adapter:
            result.status = ExecutionStatus.ERROR
            result.validation_errors.append("No trading adapter configured")
            return result

        try:
            # Submit order through adapter
            order_response = self.trading_adapter.submit_order(order_details)

            if order_response.get("success"):
                result.status = ExecutionStatus.SUBMITTED
                result.order_id = order_response.get("order_id")

                # Check for immediate fill
                if order_response.get("filled"):
                    result.status = ExecutionStatus.FILLED
                    result.filled_quantity = order_response.get("filled_quantity", 0)
                    result.filled_price = order_response.get("fill_price")
                    result.executed_value = result.filled_quantity * (
                        result.filled_price or 0
                    )
                    result.commission = order_response.get("commission", 0)

                    # Update counters
                    self.daily_trades_count += 1
                    self.daily_risk_used += request.position_size.risk_percent or 0.01

            else:
                result.status = ExecutionStatus.REJECTED
                result.validation_errors.append(
                    order_response.get("error", "Order rejected")
                )

        except Exception as e:
            result.status = ExecutionStatus.ERROR
            result.validation_errors.append(f"Trading adapter error: {e!s}")

        return result

    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate estimated commission for trade."""
        # Simple commission model - can be customized
        return max(1.0, trade_value * 0.001)  # $1 minimum or 0.1%

    def get_execution_history(
        self, ticker: str | None = None, limit: int = 50
    ) -> list[ExecutionResult]:
        """Get execution history, optionally filtered by ticker."""
        history = self.execution_history

        if ticker:
            history = [r for r in history if r.ticker == ticker]

        return history[-limit:]

    def get_daily_stats(self) -> dict[str, Any]:
        """Get daily execution statistics."""
        return {
            "trades_today": self.daily_trades_count,
            "max_daily_trades": self.max_daily_trades,
            "risk_used_today": self.daily_risk_used,
            "max_daily_risk": self.max_daily_risk,
            "trades_remaining": max(0, self.max_daily_trades - self.daily_trades_count),
            "risk_remaining": max(0, self.max_daily_risk - self.daily_risk_used),
        }

    def reset_daily_counters(self):
        """Reset daily counters (called at market open)."""
        self.daily_trades_count = 0
        self.daily_risk_used = 0.0
        logger.info("Daily execution counters reset")


# Global executor instance
trade_executor = TradeExecutor()


def execute_trade_signal(
    signal: Signal, position_size: PositionSize, dry_run: bool = True
) -> ExecutionResult:
    """Convenience function to execute a trade signal."""
    request = ExecutionRequest(
        signal=signal,
        position_size=position_size,
        ticker=signal.ticker,
        dry_run=dry_run,
    )
    return trade_executor.execute_signal(request)


def get_execution_status(request_id: str) -> ExecutionResult | None:
    """Get execution status by request ID."""
    for result in trade_executor.execution_history:
        if result.request_id == request_id:
            return result
    return None
