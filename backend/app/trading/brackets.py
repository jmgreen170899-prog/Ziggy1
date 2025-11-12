"""
Bracket Orders & OCO System - Action & Execution Layer

Mission: Safety ↑, slippage ↓
Support bracket orders (stop/limit), OCO, time-in-force, partial fills tracking.
Unified order composition across IBKR, CCXT, and other adapters.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported across adapters."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order sides."""

    BUY = "buy"
    SELL = "sell"


class TimeInForce(Enum):
    """Time-in-force options."""

    DAY = "day"
    GTC = "gtc"  # Good Till Canceled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    GTD = "gtd"  # Good Till Date


class OrderStatus(Enum):
    """Order status tracking."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class OrderLeg:
    """Individual order leg with all parameters."""

    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: float = 0.0
    order_type: OrderType = OrderType.MARKET
    price: float | None = None
    stop_price: float | None = None
    trail_amount: float | None = None
    trail_percent: float | None = None
    time_in_force: TimeInForce = TimeInForce.DAY
    good_till_date: str | None = None

    # Metadata
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float | None = None
    commission: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    submitted_at: str | None = None
    filled_at: str | None = None

    # Linkage for bracket/OCO orders
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    oco_group: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/logging."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "price": self.price,
            "stop_price": self.stop_price,
            "trail_amount": self.trail_amount,
            "trail_percent": self.trail_percent,
            "time_in_force": self.time_in_force.value,
            "good_till_date": self.good_till_date,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "avg_fill_price": self.avg_fill_price,
            "commission": self.commission,
            "created_at": self.created_at,
            "submitted_at": self.submitted_at,
            "filled_at": self.filled_at,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "oco_group": self.oco_group,
        }

    def is_complete(self) -> bool:
        """Check if order is completely filled."""
        return abs(self.filled_quantity) >= abs(self.quantity)

    def remaining_quantity(self) -> float:
        """Get remaining quantity to fill."""
        return self.quantity - self.filled_quantity


@dataclass
class BracketOrder:
    """Bracket order with parent entry and child stop/profit orders."""

    bracket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent: OrderLeg = field(default_factory=OrderLeg)
    stop_loss: OrderLeg | None = None
    take_profit: OrderLeg | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self):
        """Set up parent-child relationships."""
        if self.stop_loss:
            self.stop_loss.parent_id = self.parent.order_id
            self.parent.child_ids.append(self.stop_loss.order_id)

        if self.take_profit:
            self.take_profit.parent_id = self.parent.order_id
            self.parent.child_ids.append(self.take_profit.order_id)

        # Set up OCO relationship between stop and take profit
        if self.stop_loss and self.take_profit:
            oco_group = f"oco_{self.bracket_id}"
            self.stop_loss.oco_group = oco_group
            self.take_profit.oco_group = oco_group

    def get_all_orders(self) -> list[OrderLeg]:
        """Get all orders in the bracket."""
        orders = [self.parent]
        if self.stop_loss:
            orders.append(self.stop_loss)
        if self.take_profit:
            orders.append(self.take_profit)
        return orders

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/logging."""
        return {
            "bracket_id": self.bracket_id,
            "parent": self.parent.to_dict(),
            "stop_loss": self.stop_loss.to_dict() if self.stop_loss else None,
            "take_profit": self.take_profit.to_dict() if self.take_profit else None,
            "created_at": self.created_at,
        }


class BracketComposer:
    """
    Compose bracket orders with proper parent-child linkage and OCO relationships.

    Handles different adapter requirements and ensures consistent behavior
    across IBKR, CCXT, and other execution venues.
    """

    def __init__(self):
        self.active_brackets: dict[str, BracketOrder] = {}
        self.active_orders: dict[str, OrderLeg] = {}

    def create_bracket(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        entry: dict[str, Any],
        stop: dict[str, Any],
        take: dict[str, Any] | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
    ) -> BracketOrder:
        """
        Create a bracket order with entry, stop loss, and optional take profit.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares/units
            entry: Entry order parameters {type, price?, ...}
            stop: Stop loss parameters {type, price, ...}
            take: Take profit parameters {type, price, ...} (optional)
            time_in_force: Default time in force for all legs

        Returns:
            BracketOrder with linked parent-child relationships
        """
        try:
            # Create parent entry order
            parent = self._create_order_leg(
                symbol=symbol, side=side, quantity=quantity, time_in_force=time_in_force, **entry
            )

            # Create stop loss order (opposite side of parent)
            stop_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
            stop_leg = self._create_order_leg(
                symbol=symbol,
                side=stop_side,
                quantity=abs(quantity),  # Always positive quantity
                time_in_force=time_in_force,
                **stop,
            )

            # Create take profit order (if specified)
            take_leg = None
            if take:
                take_leg = self._create_order_leg(
                    symbol=symbol,
                    side=stop_side,  # Same side as stop
                    quantity=abs(quantity),
                    time_in_force=time_in_force,
                    **take,
                )

            # Compose bracket
            bracket = BracketOrder(parent=parent, stop_loss=stop_leg, take_profit=take_leg)

            # Register orders
            self.active_brackets[bracket.bracket_id] = bracket
            for order in bracket.get_all_orders():
                self.active_orders[order.order_id] = order

            logger.info(f"Created bracket order {bracket.bracket_id} for {symbol}")
            return bracket

        except Exception as e:
            logger.error(f"Failed to create bracket order: {e}")
            raise

    def create_oco(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order1: dict[str, Any],
        order2: dict[str, Any],
        time_in_force: TimeInForce = TimeInForce.DAY,
    ) -> list[OrderLeg]:
        """
        Create One-Cancels-Other (OCO) order pair.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of shares/units
            order1: First order parameters
            order2: Second order parameters
            time_in_force: Time in force for both orders

        Returns:
            List of two OrderLeg objects with OCO linkage
        """
        try:
            oco_group = f"oco_{uuid.uuid4()}"

            # Create first order
            leg1 = self._create_order_leg(
                symbol=symbol,
                side=side,
                quantity=quantity,
                time_in_force=time_in_force,
                oco_group=oco_group,
                **order1,
            )

            # Create second order
            leg2 = self._create_order_leg(
                symbol=symbol,
                side=side,
                quantity=quantity,
                time_in_force=time_in_force,
                oco_group=oco_group,
                **order2,
            )

            # Register orders
            self.active_orders[leg1.order_id] = leg1
            self.active_orders[leg2.order_id] = leg2

            logger.info(f"Created OCO orders {leg1.order_id}, {leg2.order_id} for {symbol}")
            return [leg1, leg2]

        except Exception as e:
            logger.error(f"Failed to create OCO orders: {e}")
            raise

    def _create_order_leg(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: str = "market",
        price: float | None = None,
        stop_price: float | None = None,
        trail_amount: float | None = None,
        trail_percent: float | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        good_till_date: str | None = None,
        oco_group: str | None = None,
        **kwargs,
    ) -> OrderLeg:
        """Create individual order leg with validation."""

        # Validate and convert order type
        try:
            order_type_enum = OrderType(order_type.lower())
        except ValueError:
            raise ValueError(f"Invalid order type: {order_type}")

        # Validate price parameters
        if order_type_enum in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price is None:
            raise ValueError(f"Price required for {order_type} orders")

        if (
            order_type_enum in [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.TRAILING_STOP]
            and stop_price is None
        ):
            raise ValueError(f"Stop price required for {order_type} orders")

        return OrderLeg(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type_enum,
            price=price,
            stop_price=stop_price,
            trail_amount=trail_amount,
            trail_percent=trail_percent,
            time_in_force=time_in_force,
            good_till_date=good_till_date,
            oco_group=oco_group,
        )

    def update_fill(
        self, order_id: str, filled_quantity: float, fill_price: float, commission: float = 0.0
    ) -> bool:
        """
        Update order with partial or complete fill.

        Args:
            order_id: Order ID to update
            filled_quantity: Quantity filled in this update
            fill_price: Price of the fill
            commission: Commission charged

        Returns:
            True if order exists and was updated
        """
        if order_id not in self.active_orders:
            logger.warning(f"Order {order_id} not found for fill update")
            return False

        order = self.active_orders[order_id]

        # Update fill information
        order.filled_quantity += filled_quantity

        # Calculate average fill price
        if order.avg_fill_price is None:
            order.avg_fill_price = fill_price
        else:
            total_filled = order.filled_quantity
            if total_filled > 0:
                order.avg_fill_price = (
                    order.avg_fill_price * (total_filled - filled_quantity)
                    + fill_price * filled_quantity
                ) / total_filled

        order.commission += commission
        order.filled_at = datetime.now(UTC).isoformat()

        # Update status
        if order.is_complete():
            order.status = OrderStatus.FILLED
            self._handle_order_completion(order)
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        logger.info(f"Updated order {order_id} fill: {filled_quantity} @ {fill_price}")
        return True

    def _handle_order_completion(self, completed_order: OrderLeg) -> None:
        """Handle order completion and OCO/bracket logic."""
        try:
            # Handle OCO cancellation
            if completed_order.oco_group:
                self._cancel_oco_siblings(completed_order)

            # Handle bracket order child activation
            if completed_order.child_ids:
                self._activate_child_orders(completed_order)

        except Exception as e:
            logger.error(f"Error handling order completion: {e}")

    def _cancel_oco_siblings(self, completed_order: OrderLeg) -> None:
        """Cancel sibling orders in the same OCO group."""
        for order_id, order in self.active_orders.items():
            if (
                order.oco_group == completed_order.oco_group
                and order.order_id != completed_order.order_id
                and order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]
            ):
                order.status = OrderStatus.CANCELED
                logger.info(f"Canceled OCO sibling order {order_id}")

    def _activate_child_orders(self, parent_order: OrderLeg) -> None:
        """Activate child orders when parent is filled."""
        for child_id in parent_order.child_ids:
            if child_id in self.active_orders:
                child_order = self.active_orders[child_id]
                if child_order.status == OrderStatus.PENDING:
                    child_order.status = OrderStatus.SUBMITTED
                    logger.info(f"Activated child order {child_id}")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order and handle cascade effects."""
        if order_id not in self.active_orders:
            return False

        order = self.active_orders[order_id]

        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELED]:
            return False  # Already terminal

        order.status = OrderStatus.CANCELED

        # Cancel OCO siblings
        if order.oco_group:
            self._cancel_oco_siblings(order)

        # Cancel child orders
        for child_id in order.child_ids:
            if child_id in self.active_orders:
                self.cancel_order(child_id)

        logger.info(f"Canceled order {order_id}")
        return True

    def get_bracket(self, bracket_id: str) -> BracketOrder | None:
        """Get bracket order by ID."""
        return self.active_brackets.get(bracket_id)

    def get_order(self, order_id: str) -> OrderLeg | None:
        """Get order by ID."""
        return self.active_orders.get(order_id)

    def get_active_orders(self) -> list[OrderLeg]:
        """Get all active orders."""
        return [
            order
            for order in self.active_orders.values()
            if order.status
            not in [
                OrderStatus.FILLED,
                OrderStatus.CANCELED,
                OrderStatus.REJECTED,
                OrderStatus.EXPIRED,
            ]
        ]

    def get_open_brackets(self) -> list[BracketOrder]:
        """Get all open bracket orders."""
        return [
            bracket for bracket in self.active_brackets.values() if not bracket.parent.is_complete()
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get bracket system statistics."""
        active_count = len(self.get_active_orders())
        bracket_count = len(self.get_open_brackets())

        status_counts = {}
        for order in self.active_orders.values():
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_orders": len(self.active_orders),
            "active_orders": active_count,
            "active_brackets": bracket_count,
            "status_distribution": status_counts,
        }


# Global bracket composer instance
bracket_composer = BracketComposer()


# Convenience functions
def compose_bracket(
    symbol: str,
    side: str,
    qty: float,
    entry: dict[str, Any],
    stop: dict[str, Any],
    take: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Legacy function for bracket composition.

    Returns normalized order bundle with OCO linkage metadata.
    """
    try:
        side_enum = OrderSide(side.lower())
        bracket = bracket_composer.create_bracket(symbol, side_enum, qty, entry, stop, take)
        return bracket.to_dict()
    except Exception as e:
        logger.error(f"Bracket composition failed: {e}")
        return {"error": str(e)}


def create_bracket_order(
    symbol: str,
    side: str,
    quantity: float,
    entry: dict[str, Any],
    stop: dict[str, Any],
    take: dict[str, Any] | None = None,
) -> BracketOrder:
    """Create bracket order with full OrderLeg objects."""
    side_enum = OrderSide(side.lower())
    return bracket_composer.create_bracket(symbol, side_enum, quantity, entry, stop, take)


def create_oco_order(
    symbol: str, side: str, quantity: float, order1: dict[str, Any], order2: dict[str, Any]
) -> list[OrderLeg]:
    """Create OCO order pair."""
    side_enum = OrderSide(side.lower())
    return bracket_composer.create_oco(symbol, side_enum, quantity, order1, order2)


def update_order_fill(
    order_id: str, filled_qty: float, fill_price: float, commission: float = 0.0
) -> bool:
    """Update order with fill information."""
    return bracket_composer.update_fill(order_id, filled_qty, fill_price, commission)


def get_bracket_stats() -> dict[str, Any]:
    """Get bracket system statistics."""
    return bracket_composer.get_stats()
