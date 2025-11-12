from fastapi.testclient import TestClient

from app.main import app


def test_health_labels_fallback_when_dev_db_sqlite(monkeypatch):
    # Simulate DEV_DB=sqlite env; health should label fallback_sqlite
    monkeypatch.setenv("DEV_DB", "sqlite")
    with TestClient(app) as c:
        r = c.get("/paper/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("db") == "fallback_sqlite"
        assert "using_fallback_sqlite" in (data.get("reasons") or [])
