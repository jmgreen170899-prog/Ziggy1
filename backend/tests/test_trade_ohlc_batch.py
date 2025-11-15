import asyncio

from fastapi.testclient import TestClient

import app.api.routes_trading as rt
from app.main import app


class _MixedProvider:
    async def fetch_ohlc(self, symbols, period_days=60, adjusted=True, **kwargs):
        # Simulate behavior per single ticker call (batch mode calls one ticker at a time)
        if not symbols or len(symbols) != 1:
            return {}
        t = symbols[0].upper()
        if t == "AAPL":
            # Minimal DataFrame-like object substitute: use pandas for realistic structure
            import pandas as pd

            df = pd.DataFrame(
                {
                    "Date": ["2025-01-01", "2025-01-02"],
                    "Open": [1.0, 2.0],
                    "High": [1.5, 2.5],
                    "Low": [0.9, 1.9],
                    "Close": [1.2, 2.2],
                    "Adj Close": [1.2, 2.2],
                    "Volume": [100, 200],
                }
            )
            return {t: df}
        if t == "SLOW":
            await asyncio.sleep(0.2)
            return {}
        if t == "FAIL":
            raise RuntimeError("provider blew up")
        return {}


def test_batch_mixed_success(monkeypatch):
    # Force batch mode provider
    monkeypatch.setattr(rt, "_price_provider", lambda: _MixedProvider())
    # Speed up timeout for the test
    monkeypatch.setattr(rt, "_OHLC_TIMEOUT_SECS", 0.05)

    c = TestClient(app)

    resp = c.get(
        "/trade/ohlc",
        params={"tickers": "AAPL,FAIL,SLOW,@@@", "batch": True, "timeout_s": 0.05},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data and "results" in data
    sm = data["summary"]
    assert sm["requested"] == 4
    # AAPL valid, FAIL valid, SLOW valid, @@@ invalid
    assert sm["valid"] == 3
    assert sm["invalid"] == 1
    # Expect 1 success (AAPL), 2 failed (FAIL provider_error, SLOW timeout/no_data)
    assert sm["succeeded"] == 1
    assert sm["failed"] in (2, 3)  # depending on SLOW path being timeout or no_data

    results = {r["ticker"].upper(): r for r in data["results"]}
    assert results["AAPL"]["ok"] is True and isinstance(
        results["AAPL"].get("records"), list
    )
    assert results["FAIL"]["ok"] is False and str(
        results["FAIL"].get("error", "")
    ).startswith("provider_error")
    # SLOW should either timeout or return no_data
    assert results["SLOW"]["ok"] is False
    assert results["SLOW"]["error"] in ("timeout", "no_data")
    assert (
        results["@@@"]["ok"] is False
        and results["@@@"].get("error") == "invalid_ticker"
    )
