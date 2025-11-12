from __future__ import annotations

import os


FLAG_ENV = "TRADING_ENABLED"


def trading_enabled() -> bool:
    return os.getenv(FLAG_ENV, "false").strip().lower() in {"1", "true", "yes", "on"}


def set_trading_enabled(v: bool) -> None:
    os.environ[FLAG_ENV] = "true" if v else "false"
