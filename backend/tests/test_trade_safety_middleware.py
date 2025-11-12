import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_trade_post_blocked_in_dev(client):
    # POST under /trade should be blocked by middleware in non-production (paper-only) mode
    resp = client.post("/trade/explain", json={"ticker": "AAPL"})
    assert resp.status_code == 403
    body = resp.json()
    assert body.get("ok") is False
    assert body.get("mode") == "paper-only"
    assert "/trade" in body.get("blocked", "")


def test_trade_health_allowed(client):
    # /trade/health should always be allowed
    resp = client.get("/trade/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
