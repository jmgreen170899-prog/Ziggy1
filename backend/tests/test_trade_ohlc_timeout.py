import asyncio

from fastapi.testclient import TestClient

import app.api.routes_trading as rt
from app.main import app


class _SlowProvider:
    async def fetch_ohlc(self, symbols, period_days=60, adjusted=True, **kwargs):
        # Simulate a slow upstream call that should be cut off by timeout
        await asyncio.sleep(10)
        return {}


def test_trade_ohlc_timeout_returns_shape(monkeypatch):
    # Patch provider to our slow dummy provider
    monkeypatch.setattr(rt, "_price_provider", lambda: _SlowProvider())
    # Speed up the route timeout for tests by monkeypatching the module constant
    monkeypatch.setenv("PYTHONASYNCIODEBUG", "0")
    monkeypatch.setattr(rt, "_OHLC_TIMEOUT_SECS", 0.05)
    # Since the timeout value is local in the route, we simulate by running the test client
    client = TestClient(app)
    # Call endpoint; even if provider is slow, the route should return quickly with empty data
    resp = client.get("/trade/ohlc", params={"tickers": "AAPL,MSFT"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "AAPL" in data and "MSFT" in data
    assert isinstance(data["AAPL"], list) and isinstance(data["MSFT"], list)
