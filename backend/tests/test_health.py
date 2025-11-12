from fastapi.testclient import TestClient

from app.db import db_state
from app.main import app, settings


def test_paper_health_dev_non_fatal():
    # Ensure dev-like behavior
    old_env = settings.ENV
    try:
        settings.ENV = "development"
        with TestClient(app) as client:
            resp = client.get("/paper/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "status" in data
            assert "db" in data
            assert "warmup_ms" in data
            assert isinstance(data.get("reasons", []), list)
    finally:
        settings.ENV = old_env


def test_paper_health_labels_fallback_sqlite():
    # Simulate fallback
    orig = dict(db_state)
    try:
        db_state["connected"] = True
        db_state["dialect"] = "sqlite"
        db_state["fallback"] = True
        with TestClient(app) as client:
            resp = client.get("/paper/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("db") == "fallback_sqlite"
            assert "using_fallback_sqlite" in (data.get("reasons") or [])
    finally:
        # restore
        db_state.clear()
        db_state.update(orig)


def test_paper_health_prod_503_when_unhealthy():
    # Force production behavior and unhealthy DB
    old_env = settings.ENV
    orig = dict(db_state)
    try:
        settings.ENV = "production"
        db_state["connected"] = False
        db_state["dialect"] = "postgres"
        db_state["fallback"] = False
        with TestClient(app) as client:
            resp = client.get("/paper/health")
            assert resp.status_code == 503
            data = resp.json()
            assert data.get("status") in {"error", "degraded"}
            assert "db_unavailable" in (data.get("reasons") or [])
    finally:
        settings.ENV = old_env
        db_state.clear()
        db_state.update(orig)
