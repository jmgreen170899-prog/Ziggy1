from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


@dataclass
class TradingSettings:
    BROKER: str = os.getenv("BROKER", "IBKR").upper()  # IBKR | ALPACA
    TRADING_ENABLED: bool = _bool("TRADING_ENABLED", "false")
    DB_PATH: str = os.getenv("TRADING_DB_PATH", "./trading.db")

    # Risk
    MAX_NOTIONAL_PER_TRADE: float = _float("MAX_NOTIONAL_PER_TRADE", 1000.0)
    MAX_GROSS_EXPOSURE: float = _float("MAX_GROSS_EXPOSURE", 5000.0)
    MAX_DAILY_LOSS: float = _float("MAX_DAILY_LOSS", 200.0)
    MAX_POSITIONS: int = _int("MAX_POSITIONS", 5)

    # IBKR
    IB_HOST: str = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT: int = _int("IB_PORT", 7497)  # 7497 = TWS paper
    IB_CLIENT_ID: int = _int("IB_CLIENT_ID", 7)

    # Alpaca
    ALPACA_BASE_URL: str = os.getenv(
        "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
    )
    ALPACA_KEY_ID: str | None = os.getenv("ALPACA_KEY_ID")
    ALPACA_SECRET: str | None = os.getenv("ALPACA_SECRET")


def get_settings() -> TradingSettings:
    return TradingSettings()
