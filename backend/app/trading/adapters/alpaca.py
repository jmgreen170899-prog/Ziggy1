from __future__ import annotations

from typing import Any

import httpx

from .base import BrokerAdapter


class AlpacaAdapter(BrokerAdapter):
    def __init__(self, base_url: str, key_id: str, secret: str):
        self.base = base_url.rstrip("/")
        self.key, self.secret = key_id, secret
        self._client: httpx.AsyncClient | None = None

    async def connect(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "APCA-API-KEY-ID": self.key,
                    "APCA-API-SECRET-KEY": self.secret,
                    "Content-Type": "application/json",
                }
            )

    async def _ensure(self):
        if self._client is None:
            await self.connect()

    async def place_market_order(self, symbol: str, qty: int) -> dict[str, Any]:
        await self._ensure()
        side = "buy" if qty > 0 else "sell"
        payload = {
            "symbol": symbol,
            "qty": abs(qty),
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }
        r = await self._client.post(f"{self.base}/v2/orders", json=payload)
        r.raise_for_status()
        data = r.json()
        return {"orderId": data.get("id"), "status": data.get("status", "submitted")}

    async def positions(self) -> list[dict[str, Any]]:
        await self._ensure()
        r = await self._client.get(f"{self.base}/v2/positions")
        r.raise_for_status()
        arr = r.json()
        return [
            {
                "symbol": x["symbol"],
                "qty": int(float(x["qty"])),
                "avg_price": float(x["avg_entry_price"]),
            }
            for x in arr
        ]

    async def cancel_all(self) -> None:
        await self._ensure()
        r = await self._client.delete(f"{self.base}/v2/orders")
        r.raise_for_status()
