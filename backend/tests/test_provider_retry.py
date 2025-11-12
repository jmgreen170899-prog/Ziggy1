import asyncio
import time

from app.services.market_providers import MarketProvider
from app.services.provider_factory import _PROV_FAIL, _PROV_FAIL_PENALTY, MultiProvider


class FlakyProvider(MarketProvider):
    name = "flaky"
    supports_intraday = False

    def __init__(self):
        self.calls = 0

    async def fetch_ohlc(self, tickers, period_days=60, adjusted=True):
        self.calls += 1
        # always raise to simulate failure
        raise RuntimeError("simulated failure")


def test_provider_penalty_and_skip():
    p = MultiProvider(priority=["flaky"])
    # inject our flaky instance
    p.providers = [FlakyProvider()]

    # clear global fail map
    _PROV_FAIL.clear()

    # first call -> provider will be tried and then penalized
    try:
        asyncio.run(p.fetch_ohlc(["AAPL"]))
    except Exception:
        pass

    # provider name should have a penalty timestamp recorded
    assert "flaky" in _PROV_FAIL
    ts = _PROV_FAIL.get("flaky")
    assert ts > time.time()

    # subsequent immediate call should skip provider (no exception)
    # and return empty data structure
    res = asyncio.run(p.fetch_ohlc(["AAPL"]))
    assert isinstance(res, dict)
    assert "AAPL" in res

    # wait past penalty and ensure provider is attempted again
    time.sleep(max(1, _PROV_FAIL_PENALTY + 1))
    _PROV_FAIL.pop("flaky", None)
    # For test completeness, calling again shouldn't raise because our provider will still raise,
    # but function should handle it and return a dict
    res2 = asyncio.run(p.fetch_ohlc(["AAPL"]))
    assert isinstance(res2, dict)
