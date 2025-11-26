"""
Broker Adapter Factory - DEMO VERSION

This module creates broker adapters for the trading system.
In this public demo version, all broker adapters are stubbed implementations
that return mock data without performing real trades.

SECURITY NOTE: No real broker credentials are used in this demo version.
"""
from __future__ import annotations

import logging

from .adapters.alpaca import AlpacaAdapter
from .adapters.base import BrokerAdapter
from .adapters.ibkr import IBKRAdapter
from .config import get_settings

logger = logging.getLogger("ziggy.trading.factory")


def make_adapter() -> BrokerAdapter:
    """
    Create broker adapter with strict isolation checks for paper trading.
    
    DEMO MODE: All adapters are mock implementations that do not
    connect to real brokers or execute real trades.

    Raises:
        RuntimeError: If strict isolation is violated or broker config is invalid
    """
    # Import isolation utilities
    try:
        from app.utils.isolation import (
            enforce_strict_isolation,
            should_enforce_isolation,
        )

        # Enforce strict isolation if enabled
        if should_enforce_isolation():
            enforce_strict_isolation()
    except ImportError:
        # Fallback if isolation utils not available
        pass

    s = get_settings()
    
    logger.info(
        f"Creating {s.BROKER} adapter in DEMO MODE - "
        "no real trading will occur"
    )
    
    if s.BROKER == "IBKR":
        return IBKRAdapter(s.IB_HOST, s.IB_PORT, s.IB_CLIENT_ID)
    elif s.BROKER == "ALPACA":
        if not (s.ALPACA_KEY_ID and s.ALPACA_SECRET):
            raise RuntimeError("ALPACA_KEY_ID/ALPACA_SECRET missing")
        return AlpacaAdapter(s.ALPACA_BASE_URL, s.ALPACA_KEY_ID, s.ALPACA_SECRET)
    raise RuntimeError(f"Unsupported broker: {s.BROKER}")
