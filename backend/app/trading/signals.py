"""
Enhanced Trading Signals System with Real Broker Integration
Replaces basic stubs with actual broker connectivity and order management.
"""

import logging
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any


logger = logging.getLogger("ziggy")


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL_FILL = "partial_fill"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class Order:
    """Enhanced order representation with full lifecycle tracking."""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "DAY",
        broker_order_id: str | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.symbol = symbol.upper()
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.status = OrderStatus.PENDING
        self.broker_order_id = broker_order_id

        self.filled_quantity = 0.0
        self.avg_fill_price = 0.0
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at
        self.fills: list[dict] = []
        self.broker_data: dict = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert order to dictionary for API responses."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "avg_fill_price": self.avg_fill_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "broker_order_id": self.broker_order_id,
            "fills": self.fills,
        }


class Position:
    """Enhanced position tracking with P&L calculation."""

    def __init__(self, symbol: str, quantity: float = 0.0, avg_price: float = 0.0):
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.avg_price = avg_price
        self.market_price = 0.0
        self.updated_at = datetime.now(UTC)

    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        return self.quantity * self.market_price

    @property
    def cost_basis(self) -> float:
        """Original cost basis."""
        return abs(self.quantity) * self.avg_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L."""
        if self.quantity == 0:
            return 0.0
        return (self.market_price - self.avg_price) * self.quantity

    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage."""
        if self.avg_price == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def update_market_price(self, price: float):
        """Update current market price."""
        self.market_price = price
        self.updated_at = datetime.now(UTC)

    def add_fill(self, quantity: float, price: float):
        """Add a fill to this position."""
        if self.quantity == 0:
            # New position
            self.quantity = quantity
            self.avg_price = price
        else:
            # Existing position - calculate new average
            if (self.quantity > 0 and quantity > 0) or (
                self.quantity < 0 and quantity < 0
            ):
                # Same side - add to position
                total_cost = (self.quantity * self.avg_price) + (quantity * price)
                self.quantity += quantity
                self.avg_price = total_cost / self.quantity if self.quantity != 0 else 0
            else:
                # Opposite side - reduce position
                self.quantity += quantity
                # Keep the same avg_price for remaining position

        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert position to dictionary for API responses."""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "market_price": self.market_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_percent": self.unrealized_pnl_percent,
            "updated_at": self.updated_at.isoformat(),
        }


class TradingSignalsManager:
    """Enhanced trading signals manager with real broker integration."""

    def __init__(self):
        self.orders: dict[str, Order] = {}
        self.positions: dict[str, Position] = {}
        self.broker_connector = None
        self.paper_trading = True  # Start in paper trading mode

    def set_broker_connector(self, connector):
        """Set the broker connector for live trading."""
        self.broker_connector = connector
        self.paper_trading = False
        logger.info("Broker connector set - live trading enabled")

    def enable_paper_trading(self):
        """Enable paper trading mode."""
        self.paper_trading = True
        logger.info("Paper trading mode enabled")

    async def enqueue_execute(
        self, signal_id: str, signal_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Enhanced execute function that handles real broker integration.
        """
        try:
            # Extract order details from signal
            symbol = signal_data.get("symbol", "").upper()
            side_str = signal_data.get("side", "buy").lower()
            quantity = float(signal_data.get("qty", signal_data.get("quantity", 0)))
            order_type_str = signal_data.get("order_type", "market").lower()
            limit_price = signal_data.get("limit_price") or signal_data.get("entry")
            stop_price = signal_data.get("stop_price") or signal_data.get("stop")

            if not symbol or quantity <= 0:
                return {
                    "ok": False,
                    "error": "Invalid symbol or quantity",
                    "signal_id": signal_id,
                }

            # Convert to enums
            side = OrderSide.BUY if side_str in ["buy", "long"] else OrderSide.SELL
            order_type = OrderType.MARKET
            if order_type_str == "limit":
                order_type = OrderType.LIMIT
            elif order_type_str == "stop":
                order_type = OrderType.STOP
            elif order_type_str == "stop_limit":
                order_type = OrderType.STOP_LIMIT

            # Create order
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=float(limit_price) if limit_price else None,
                stop_price=float(stop_price) if stop_price else None,
            )

            # Store order
            self.orders[order.id] = order

            if self.paper_trading:
                # Paper trading - simulate immediate fill at market price
                await self._simulate_paper_fill(order)
                result = {
                    "ok": True,
                    "mode": "paper",
                    "order_id": order.id,
                    "message": f"Paper trade executed: {side.value} {quantity} {symbol}",
                    "signal_id": signal_id,
                }
            else:
                # Live trading - submit to broker
                if not self.broker_connector:
                    return {
                        "ok": False,
                        "error": "No broker connector available",
                        "signal_id": signal_id,
                    }

                broker_result = await self.broker_connector.submit_order(order)
                if broker_result.get("ok"):
                    order.broker_order_id = broker_result.get("broker_order_id")
                    order.status = OrderStatus.SUBMITTED
                    result = {
                        "ok": True,
                        "mode": "live",
                        "order_id": order.id,
                        "broker_order_id": order.broker_order_id,
                        "message": f"Order submitted: {side.value} {quantity} {symbol}",
                        "signal_id": signal_id,
                    }
                else:
                    order.status = OrderStatus.REJECTED
                    result = {
                        "ok": False,
                        "error": broker_result.get("error", "Order rejected"),
                        "order_id": order.id,
                        "signal_id": signal_id,
                    }

            logger.info(f"[trading.signals] Execute signal {signal_id}: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error executing signal {signal_id}")
            return {"ok": False, "error": str(e), "signal_id": signal_id}

    async def cancel_signal(self, signal_id: str) -> dict[str, Any]:
        """
        Enhanced cancel function with broker integration.
        """
        try:
            # Find order by signal_id (we'd need to track this mapping)
            # For now, assume signal_id is the order_id
            order = self.orders.get(signal_id)
            if not order:
                return {"ok": False, "error": "Order not found", "signal_id": signal_id}

            if order.status in [
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            ]:
                return {
                    "ok": False,
                    "error": f"Cannot cancel order in {order.status.value} status",
                    "signal_id": signal_id,
                }

            if self.paper_trading:
                # Paper trading - simple cancellation
                order.status = OrderStatus.CANCELLED
                result = {
                    "ok": True,
                    "cancelled": True,
                    "mode": "paper",
                    "signal_id": signal_id,
                }
            else:
                # Live trading - cancel with broker
                if not self.broker_connector or not order.broker_order_id:
                    return {
                        "ok": False,
                        "error": "Cannot cancel - no broker connection",
                        "signal_id": signal_id,
                    }

                broker_result = await self.broker_connector.cancel_order(
                    order.broker_order_id
                )
                if broker_result.get("ok"):
                    order.status = OrderStatus.CANCELLED
                    result = {
                        "ok": True,
                        "cancelled": True,
                        "mode": "live",
                        "signal_id": signal_id,
                    }
                else:
                    result = {
                        "ok": False,
                        "error": broker_result.get("error", "Cancel failed"),
                        "signal_id": signal_id,
                    }

            logger.info(f"[trading.signals] Cancel signal {signal_id}: {result}")
            return result

        except Exception as e:
            logger.exception(f"Error cancelling signal {signal_id}")
            return {"ok": False, "error": str(e), "signal_id": signal_id}

    async def _simulate_paper_fill(self, order: Order):
        """Simulate a paper trading fill."""
        # For paper trading, assume immediate fill at limit price or simulated market price
        fill_price = order.limit_price or 100.0  # Default mock price

        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.updated_at = datetime.now(UTC)

        # Add fill record
        fill = {
            "quantity": order.quantity,
            "price": fill_price,
            "timestamp": order.updated_at.isoformat(),
            "execution_id": str(uuid.uuid4()),
        }
        order.fills.append(fill)

        # Update position
        await self._update_position(
            order.symbol,
            order.quantity if order.side == OrderSide.BUY else -order.quantity,
            fill_price,
        )

    async def _update_position(self, symbol: str, quantity: float, price: float):
        """Update position with a new fill."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)

        self.positions[symbol].add_fill(quantity, price)

        # Remove position if quantity is zero
        if abs(self.positions[symbol].quantity) < 1e-8:
            del self.positions[symbol]

    def get_orders(self, status_filter: str | None = None) -> list[dict[str, Any]]:
        """Get all orders, optionally filtered by status."""
        orders = list(self.orders.values())
        if status_filter:
            orders = [o for o in orders if o.status.value == status_filter]
        return [o.to_dict() for o in orders]

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all current positions."""
        return [p.to_dict() for p in self.positions.values()]

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Get portfolio summary with total values and P&L."""
        total_value = sum(p.market_value for p in self.positions.values())
        total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        total_cost = sum(p.cost_basis for p in self.positions.values())

        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_pnl": total_pnl,
            "total_pnl_percent": (
                (total_pnl / total_cost * 100) if total_cost > 0 else 0
            ),
            "position_count": len(self.positions),
            "mode": "paper" if self.paper_trading else "live",
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Global instance
_trading_manager = TradingSignalsManager()


# Enhanced public API functions
async def enqueue_execute(
    signal_id: str, signal_data: dict | None = None
) -> dict[str, Any]:
    """Enhanced execute function - now supports full signal data."""
    if signal_data is None:
        # Backward compatibility - treat signal_id as simple identifier
        signal_data = {"signal_id": signal_id}
    return await _trading_manager.enqueue_execute(signal_id, signal_data)


async def cancel_signal(signal_id: str) -> dict[str, Any]:
    """Enhanced cancel function."""
    return await _trading_manager.cancel_signal(signal_id)


def get_trading_manager() -> TradingSignalsManager:
    """Get the global trading manager instance."""
    return _trading_manager


# Additional API functions for the trading system
def get_orders(status_filter: str | None = None) -> list[dict[str, Any]]:
    """Get orders from the trading manager."""
    return _trading_manager.get_orders(status_filter)


def get_positions() -> list[dict[str, Any]]:
    """Get positions from the trading manager."""
    return _trading_manager.get_positions()


def get_portfolio_summary() -> dict[str, Any]:
    """Get portfolio summary."""
    return _trading_manager.get_portfolio_summary()
