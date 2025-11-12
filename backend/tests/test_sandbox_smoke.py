import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient


@contextmanager
def sandbox_mode():
    prev = os.environ.get("PROVIDER_MODE")
    os.environ["PROVIDER_MODE"] = "sandbox"
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("PROVIDER_MODE", None)
        else:
            os.environ["PROVIDER_MODE"] = prev


def _get_app():
    # Import inside function so env var takes effect before module import
    from app.main import app  # type: ignore

    return app


@pytest.mark.smoke
def test_health_endpoints_in_sandbox():
    with sandbox_mode():
        app = _get_app()
        client = TestClient(app)

        r1 = client.get("/paper/health")
        assert r1.status_code == 200
        data1 = r1.json()
        # provider_mode should be present when wired; tolerate absence
        if isinstance(data1, dict) and "provider_mode" in data1:
            assert str(data1["provider_mode"]).lower() == "sandbox"

        r2 = client.get("/trade/health")
        assert r2.status_code == 200
        data2 = r2.json()
        if isinstance(data2, dict) and "provider_mode" in data2:
            assert str(data2["provider_mode"]).lower() == "sandbox"
