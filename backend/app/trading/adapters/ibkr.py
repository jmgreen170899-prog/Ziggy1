"""
IBKR Broker Adapter - DEMO STUB

This module provides a mock implementation of the Interactive Brokers adapter.
In this public demo version, live trading is disabled and all methods return
simulated responses.

For production use with real IBKR integration, this module would require:
- ib_insync library installation
- Valid IBKR account credentials
- TWS or IB Gateway running locally

SECURITY NOTE: This stub prevents any actual trading operations.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, UTC
from typing import Any

from .base import BrokerAdapter

logger = logging.getLogger("ziggy.trading.ibkr")


class IBKRAdapter(BrokerAdapter):
    """
    Demo stub for Interactive Brokers adapter.
    
    This implementation returns mock data and does not connect to any
    real trading infrastructure. All operations are simulated for
    demonstration purposes.
    """
    
    def __init__(self, host: str, port: int, client_id: int):
        """Initialize the mock IBKR adapter."""
        self.host = host
        self.port = port
        self.client_id = client_id
        self._connected = False
        self._mock_positions: list[dict[str, Any]] = []
        self._order_counter = 1000
        logger.info(
            "IBKR adapter initialized in DEMO MODE - "
            "no real trading will occur"
        )

    async def connect(self) -> None:
        """Simulate connection to IBKR (demo mode - no actual connection)."""
        logger.info("DEMO: Simulating IBKR connection (no real connection made)")
        self._connected = True

    async def _ensure(self) -> None:
        """Ensure connection is established."""
        if not self._connected:
            await self.connect()

    async def place_market_order(self, symbol: str, qty: int) -> dict[str, Any]:
        """
        Simulate placing a market order (demo mode - no real order placed).
        
        Returns mock order data without executing any actual trades.
        """
        await self._ensure()
        
        # Generate mock response
        self._order_counter += 1
        mock_price = round(100 + random.uniform(-10, 10), 2)  # noqa: S311
        
        logger.info(
            f"DEMO: Simulated {symbol} order for {qty} shares "
            f"(no real order placed)"
        )
        
        return {
            "orderId": self._order_counter,
            "avgFillPrice": mock_price,
            "filled": abs(qty),
            "status": "DEMO_FILLED",
            "timestamp": datetime.now(UTC).isoformat(),
            "demo_mode": True,
        }

    async def positions(self) -> list[dict[str, Any]]:
        """
        Return mock positions (demo mode - no real positions queried).
        
        Returns sample position data for demonstration purposes.
        """
        await self._ensure()
        
        # Return demo positions for illustration
        demo_positions = [
            {"symbol": "AAPL", "qty": 100, "avg_price": 185.50, "demo": True},
            {"symbol": "MSFT", "qty": 50, "avg_price": 378.25, "demo": True},
            {"symbol": "GOOGL", "qty": 25, "avg_price": 141.80, "demo": True},
        ]
        
        logger.info("DEMO: Returning mock positions (not real account data)")
        return demo_positions

    async def cancel_all(self) -> None:
        """Simulate cancelling all orders (demo mode - no real cancellation)."""
        await self._ensure()
        logger.info("DEMO: Simulated cancel all orders (no real orders cancelled)")

    @property
    def is_demo_mode(self) -> bool:
        """Return True to indicate this is a demo adapter."""
        return True
