from __future__ import annotations

from .adapters.alpaca import AlpacaAdapter
from .adapters.base import BrokerAdapter
from .adapters.ibkr import IBKRAdapter
from .config import get_settings


def make_adapter() -> BrokerAdapter:
    """
    Create broker adapter with strict isolation checks for paper trading.

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
    if s.BROKER == "IBKR":
        return IBKRAdapter(s.IB_HOST, s.IB_PORT, s.IB_CLIENT_ID)
    elif s.BROKER == "ALPACA":
        if not (s.ALPACA_KEY_ID and s.ALPACA_SECRET):
            raise RuntimeError("ALPACA_KEY_ID/ALPACA_SECRET missing")
        return AlpacaAdapter(s.ALPACA_BASE_URL, s.ALPACA_KEY_ID, s.ALPACA_SECRET)
    raise RuntimeError(f"Unsupported broker: {s.BROKER}")
