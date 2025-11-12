from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


Side = Literal["BUY", "SELL"]


def now_utc() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class Order:
    symbol: str
    side: Side
    qty: int
    order_type: Literal["MARKET"] = "MARKET"
    client_order_id: str | None = None
    ts: str = field(default_factory=now_utc)


@dataclass
class Fill:
    order_id: int
    symbol: str
    side: Side
    qty: int
    avg_price: float
    ts: str = field(default_factory=now_utc)


@dataclass
class Position:
    symbol: str
    qty: int
    avg_price: float
