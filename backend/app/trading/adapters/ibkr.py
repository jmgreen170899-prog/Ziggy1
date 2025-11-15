from __future__ import annotations

from typing import Any

from .base import BrokerAdapter


try:
    from ib_insync import IB, MarketOrder, Order, Stock
except Exception:
    IB = None  # type: ignore


class IBKRAdapter(BrokerAdapter):
    def __init__(self, host: str, port: int, client_id: int):
        if IB is None:
            raise RuntimeError("ib_insync is not installed. pip install ib-insync")
        self.ib = IB()
        self.host, self.port, self.client_id = host, port, client_id

    async def connect(self):
        if not self.ib.isConnected():
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)

    async def _ensure(self):
        if not self.ib.isConnected():
            await self.connect()

    async def place_market_order(self, symbol: str, qty: int) -> dict[str, Any]:
        await self._ensure()
        contract = Stock(symbol, "SMART", "USD")
        order: Order = MarketOrder("BUY" if qty > 0 else "SELL", abs(qty))
        trade = self.ib.placeOrder(contract, order)
        fill = await trade.filledEvent  # wait for first fill
        return {
            "orderId": trade.order.orderId,
            "avgFillPrice": fill.execution.avgPrice,
            "filled": fill.execution.shares,
        }

    async def positions(self) -> list[dict[str, Any]]:
        await self._ensure()
        poss = await self.ib.positionsAsync()
        return [
            {"symbol": p.contract.symbol, "qty": p.position, "avg_price": p.avgCost}
            for p in poss
        ]

    async def cancel_all(self) -> None:
        await self._ensure()
        self.ib.reqGlobalCancel()
