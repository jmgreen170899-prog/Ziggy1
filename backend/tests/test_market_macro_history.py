import json
import os
import sys

import pytest
from fastapi.testclient import TestClient


# Ensure backend is importable when tests run from the repo root
ROOT = os.getcwd()
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from app.api import routes_market
from app.main import app


client = TestClient(app)

# Helper: write a temp macro history file used by the endpoint
TEST_DATA_DIR = os.path.join(os.getcwd(), "data", "macro_history")
os.makedirs(TEST_DATA_DIR, exist_ok=True)

SAMPLE_CODE = "TEST"
SAMPLE_PATH = os.path.join(TEST_DATA_DIR, f"{SAMPLE_CODE}.json")
SAMPLE_ROWS = [
    {"date": "2025-01-02", "actual": 100, "consensus": 98, "previous": 95},
    {"date": "2025-02-03", "actual": 200, "consensus": 195, "previous": 190},
]
with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
    json.dump(SAMPLE_ROWS, f)


def test_macro_history_local_only():
    r = client.get(f"/market/macro/history?code={SAMPLE_CODE}&limit=10")
    assert r.status_code == 200
    d = r.json()
    assert d["code"] == SAMPLE_CODE
    assert "history" in d and isinstance(d["history"], list)
    # No SPX enrichment keys necessarily present when no provider configured
    for row in d["history"]:
        assert "date" in row


class DummyProvider:
    def __init__(self, frames_map):
        self._frames = frames_map

    async def fetch_ohlc(self, tickers, period_days=365, adjusted=True):
        return self._frames


def make_spx_frame():
    # Create a minimal pandas DataFrame-like object with index and Close column
    try:
        import pandas as pd
    except Exception:
        return None
    idx = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06"])
    df = pd.DataFrame({"Close": [1000.0, 1005.0, 1010.0]}, index=idx)
    return df


def test_macro_history_with_provider(monkeypatch):
    df = make_spx_frame()
    if df is None:
        pytest.skip("pandas not available in test environment")
    provider = DummyProvider({"^GSPC": df})
    monkeypatch.setattr(routes_market, "get_price_provider", lambda: provider)

    r = client.get(f"/market/macro/history?code={SAMPLE_CODE}&limit=10")
    assert r.status_code == 200
    d = r.json()
    assert "history" in d
    # Ensure history rows present and have dates; enrichment may be provider- or computed-based
    assert any(row.get("date") == "2025-01-02" for row in d["history"]) is True


def test_macro_history_provider_no_pandas(monkeypatch):
    # Simulate provider present but pandas missing: monkeypatch import to raise
    class Prov:
        async def fetch_ohlc(self, tickers, period_days=365, adjusted=True):
            return {"^GSPC": {}}  # empty frames

    monkeypatch.setattr(routes_market, "get_price_provider", lambda: Prov())
    # monkeypatch pandas to None in the routes_market module if present
    monkeypatch.setattr(routes_market, "pd", None, raising=False)
    r = client.get(f"/market/macro/history?code={SAMPLE_CODE}&limit=10")
    assert r.status_code == 200
    d = r.json()
    # enrichment should be skipped; no exception
    assert "history" in d
