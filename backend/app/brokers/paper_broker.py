"""
Paper trading broker implementation for ZiggyAI autonomous trading lab.

This module provides a fully simulated broker for paper trading that includes:
- Order execution with configurable slippage and latency
- Fee simulation
- Position tracking
- Deterministic RNG for reproducible experiments
"""

from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.core.logging import get_logger
from app.trading.models import Order, Position, Side


logger = get_logger("ziggy.paper_broker")

OrderType = Literal["MARKET", "LIMIT", "STOP"]
OrderStatus = Literal["PENDING", "FILLED", "CANCELLED", "REJECTED"]


@dataclass
class PaperOrder:
    """Extended order for paper trading with simulation metadata."""

    id: str
    symbol: str
    side: Side
    qty: int
    order_type: OrderType
    price: float | None = None  # For limit/stop orders
    status: OrderStatus = "PENDING"
    client_order_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: datetime | None = None
    fill_price: float | None = None
    fees: float = 0.0
    slippage_bps: float = 0.0
    latency_ms: int = 0


@dataclass
class PaperPosition:
    """Position tracking for paper broker."""

    symbol: str
    qty: int
    avg_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    def update_unrealized(self, current_price: float) -> None:
        """Update unrealized PnL based on current market price."""
        if self.qty != 0:
            self.unrealized_pnl = (current_price - self.avg_price) * self.qty


@dataclass
class OrderFill:
    """Result of order execution."""

    order_id: str
    symbol: str
    side: Side
    qty: int
    avg_price: float
    fees: float
    slippage_bps: float
    latency_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PaperBroker:
    """
    Paper trading broker with realistic execution simulation.

    Features:
    - Configurable slippage (basis points)
    - Execution latency simulation
    - Fee calculation
    - Deterministic RNG for reproducible tests
    - Position tracking and mark-to-market
    """

    def __init__(
        self,
        slippage_bps: float = 1.5,
        latency_ms_base: int = 50,
        latency_ms_variance: int = 20,
        fees_per_notional_bps: float = 0.2,
        seed: int | None = None,
    ):
        self.slippage_bps = slippage_bps
        self.latency_ms_base = latency_ms_base
        self.latency_ms_variance = latency_ms_variance
        self.fees_per_notional_bps = fees_per_notional_bps

        # Deterministic RNG for reproducible experiments
        self.rng = random.Random(seed)

        # State tracking
        self._orders: dict[str, PaperOrder] = {}
        self._positions: dict[str, PaperPosition] = {}
        self.fills: list[OrderFill] = []

        # Market data cache (for mark-to-market)
        self.market_prices: dict[str, float] = {}

        logger.info(
            "PaperBroker initialized",
            extra={
                "slippage_bps": slippage_bps,
                "latency_ms_base": latency_ms_base,
                "fees_per_notional_bps": fees_per_notional_bps,
                "seed": seed,
            },
        )

    async def submit(self, order: Order) -> OrderFill:
        """
        Submit an order for execution.

        Args:
            order: Order to execute

        Returns:
            OrderFill with execution details
        """
        # Create paper order with unique ID
        paper_order = PaperOrder(
            id=str(uuid.uuid4()),
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            order_type=order.order_type,
            client_order_id=order.client_order_id,
        )

        self._orders[paper_order.id] = paper_order

        # Simulate latency
        latency_ms = max(
            0,
            int(self.rng.normalvariate(self.latency_ms_base, self.latency_ms_variance)),
        )
        paper_order.latency_ms = latency_ms

        if latency_ms > 0:
            await asyncio.sleep(latency_ms / 1000.0)

        # Get market price (simulate current price)
        market_price = self._get_market_price(order.symbol)

        # Calculate execution price with slippage
        slippage_bps = self.rng.normalvariate(
            self.slippage_bps, self.slippage_bps * 0.3
        )
        slippage_factor = 1.0 + (slippage_bps / 10000.0)

        if order.side == "BUY":
            fill_price = market_price * slippage_factor
        else:  # SELL
            fill_price = market_price / slippage_factor

        # Calculate fees
        notional = fill_price * order.qty
        fees = notional * (self.fees_per_notional_bps / 10000.0)

        # Update order
        paper_order.status = "FILLED"
        paper_order.filled_at = datetime.utcnow()
        paper_order.fill_price = fill_price
        paper_order.fees = fees
        paper_order.slippage_bps = abs(slippage_bps)

        # Update position
        self._update_position(order.symbol, order.side, order.qty, fill_price, fees)

        # Create fill
        fill = OrderFill(
            order_id=paper_order.id,
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            avg_price=fill_price,
            fees=fees,
            slippage_bps=abs(slippage_bps),
            latency_ms=latency_ms,
        )

        self.fills.append(fill)

        logger.debug(
            "Order filled",
            extra={
                "order_id": paper_order.id,
                "symbol": order.symbol,
                "side": order.side,
                "qty": order.qty,
                "fill_price": fill_price,
                "slippage_bps": abs(slippage_bps),
                "fees": fees,
                "latency_ms": latency_ms,
            },
        )

        return fill

    async def cancel(self, order_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if successfully cancelled, False otherwise
        """
        if order_id not in self._orders:
            return False

        order = self._orders[order_id]
        if order.status != "PENDING":
            return False

        order.status = "CANCELLED"
        logger.debug("Order cancelled", extra={"order_id": order_id})
        return True

    async def positions(self) -> dict[str, Position]:
        """
        Get current positions.

        Returns:
            Dict mapping symbol to Position
        """
        return {
            symbol: Position(symbol=symbol, qty=pos.qty, avg_price=pos.avg_price)
            for symbol, pos in self._positions.items()
            if pos.qty != 0
        }

    async def orders(self, status: str | None = None) -> list[PaperOrder]:
        """
        Get orders, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of orders
        """
        if status is None:
            return list(self._orders.values())

        return [order for order in self._orders.values() if order.status == status]

    async def mark_to_market(self) -> dict[str, float]:
        """
        Mark all positions to market and return unrealized PnL.

        Returns:
            Dict mapping symbol to unrealized PnL
        """
        unrealized_pnl = {}

        for symbol, position in self._positions.items():
            if position.qty != 0:
                current_price = self._get_market_price(symbol)
                position.update_unrealized(current_price)
                unrealized_pnl[symbol] = position.unrealized_pnl

        return unrealized_pnl

    def _get_market_price(self, symbol: str) -> float:
        """
        Get current market price for symbol.

        In a real implementation, this would fetch from market data.
        For simulation, we'll use cached prices or generate synthetic ones.
        """
        if symbol in self.market_prices:
            # Add some realistic price movement
            base_price = self.market_prices[symbol]
            volatility = 0.001  # 0.1% volatility per update
            price_change = self.rng.normalvariate(0, volatility)
            new_price = base_price * (1 + price_change)
            self.market_prices[symbol] = max(0.01, new_price)  # Floor at 1 cent
            return new_price
        else:
            # Generate initial price for new symbol
            if symbol.startswith("^"):  # Index
                initial_price = self.rng.uniform(3000, 5000)
            else:  # Stock
                initial_price = self.rng.uniform(10, 500)

            self.market_prices[symbol] = initial_price
            return initial_price

    def set_market_price(self, symbol: str, price: float) -> None:
        """Set market price for testing purposes."""
        self.market_prices[symbol] = price

    def _update_position(
        self, symbol: str, side: Side, qty: int, price: float, fees: float
    ) -> None:
        """Update position after a fill."""
        if symbol not in self._positions:
            self._positions[symbol] = PaperPosition(symbol=symbol, qty=0, avg_price=0.0)

        position = self._positions[symbol]

        # Calculate new position
        if side == "BUY":
            new_qty = position.qty + qty
            if new_qty == 0:
                new_avg_price = 0.0
            elif position.qty >= 0:
                # Adding to long position
                total_cost = (position.avg_price * position.qty) + (price * qty) + fees
                new_avg_price = total_cost / new_qty if new_qty != 0 else 0.0
            else:
                # Covering short position
                if new_qty >= 0:
                    # Realize PnL on covered portion
                    covered_qty = min(qty, abs(position.qty))
                    realized_pnl = (position.avg_price - price) * covered_qty - fees
                    position.realized_pnl += realized_pnl

                    if new_qty > 0:
                        # Remainder becomes new long position
                        new_avg_price = price
                    else:
                        new_avg_price = position.avg_price
                else:
                    # Still short, update average
                    new_avg_price = position.avg_price
        else:  # SELL
            new_qty = position.qty - qty
            if new_qty == 0:
                new_avg_price = 0.0
            elif position.qty <= 0:
                # Adding to short position
                total_value = abs(position.avg_price * position.qty) + (price * qty)
                new_avg_price = total_value / abs(new_qty) if new_qty != 0 else 0.0
            else:
                # Selling long position
                if new_qty <= 0:
                    # Realize PnL on sold portion
                    sold_qty = min(qty, position.qty)
                    realized_pnl = (price - position.avg_price) * sold_qty - fees
                    position.realized_pnl += realized_pnl

                    if new_qty < 0:
                        # Remainder becomes new short position
                        new_avg_price = price
                    else:
                        new_avg_price = position.avg_price
                else:
                    # Still long, keep average
                    new_avg_price = position.avg_price

        position.qty = new_qty
        position.avg_price = new_avg_price

    def get_performance_summary(self) -> dict[str, float]:
        """Get overall performance summary."""
        total_fees = sum(fill.fees for fill in self.fills)
        total_realized_pnl = sum(pos.realized_pnl for pos in self._positions.values())

        # Calculate unrealized PnL
        total_unrealized_pnl = 0.0
        for symbol, position in self._positions.items():
            if position.qty != 0:
                current_price = self._get_market_price(symbol)
                position.update_unrealized(current_price)
                total_unrealized_pnl += position.unrealized_pnl

        total_pnl = total_realized_pnl + total_unrealized_pnl

        return {
            "total_pnl": total_pnl,
            "realized_pnl": total_realized_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "total_fees": total_fees,
            "net_pnl": total_pnl - total_fees,
            "num_trades": len(self.fills),
            "num_positions": len([p for p in self._positions.values() if p.qty != 0]),
        }
