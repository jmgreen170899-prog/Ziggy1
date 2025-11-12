from __future__ import annotations

from typing import Any


class BrokerAdapter:
    async def connect(self):
        raise NotImplementedError

    async def place_market_order(self, symbol: str, qty: int) -> dict[str, Any]:
        raise NotImplementedError

    async def positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def cancel_all(self) -> None:
        raise NotImplementedError
