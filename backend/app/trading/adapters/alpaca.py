"""
Alpaca Broker Adapter - DEMO STUB

This module provides a mock implementation of the Alpaca broker adapter.
In this public demo version, live trading is disabled and all methods return
simulated responses.

For production use with real Alpaca integration, this module would require:
- Valid Alpaca API credentials
- Alpaca account setup (paper or live)

SECURITY NOTE: This stub prevents any actual trading operations.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, UTC
from typing import Any

from .base import BrokerAdapter

logger = logging.getLogger("ziggy.trading.alpaca")


class AlpacaAdapter(BrokerAdapter):
    """
    Demo stub for Alpaca broker adapter.
    
    This implementation returns mock data and does not connect to any
    real trading infrastructure. All operations are simulated for
    demonstration purposes.
    """
    
    def __init__(self, base_url: str, key_id: str, secret: str):
        """Initialize the mock Alpaca adapter."""
        self.base = base_url.rstrip("/")
        self.key = key_id
        self.secret = secret
        self._connected = False
        self._order_counter = 2000
        logger.info(
            "Alpaca adapter initialized in DEMO MODE - "
            "no real trading will occur"
        )

    async def connect(self) -> None:
        """Simulate connection to Alpaca (demo mode - no actual connection)."""
        logger.info("DEMO: Simulating Alpaca connection (no real connection made)")
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
        side = "buy" if qty > 0 else "sell"
        
        logger.info(
            f"DEMO: Simulated {symbol} {side} order for {abs(qty)} shares "
            f"(no real order placed)"
        )
        
        return {
            "orderId": f"demo-{self._order_counter}",
            "status": "DEMO_FILLED",
            "symbol": symbol,
            "qty": abs(qty),
            "side": side,
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
            {"symbol": "TSLA", "qty": 30, "avg_price": 248.75, "demo": True},
            {"symbol": "NVDA", "qty": 20, "avg_price": 875.30, "demo": True},
            {"symbol": "AMD", "qty": 100, "avg_price": 156.20, "demo": True},
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
