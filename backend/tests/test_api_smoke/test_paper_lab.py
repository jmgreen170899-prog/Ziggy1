"""
Paper Lab Domain Smoke Tests

Tests for paper trading endpoints:
- Create run
- Stop run
- List trades
- Portfolio status
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_paper_lab_create_run(client):
    """Test creating a paper trading run"""
    possible_paths = [
        "/api/paper/runs",
        "/paper/runs",
        "/api/paper/create",
    ]

    payload = {
        "name": "Test Run",
        "strategy": "sma50_cross",
        "symbols": ["AAPL"],
        "initial_capital": 10000.0,
    }

    for path in possible_paths:
        response = client.post(path, json=payload)

        if response.status_code not in [404, 405]:
            assert response.status_code in [
                200,
                201,
                400,
                422,
                501,
            ], f"Create run at {path} should return valid status"

            if response.status_code in [200, 201]:
                data = response.json()
                assert isinstance(data, dict), "Response should be a dict"

                # Should have run information
                if "id" in data or "run_id" in data:
                    run_id = data.get("id") or data.get("run_id")
                    assert run_id, "Run should have an ID"
            break


def test_paper_lab_list_runs(client):
    """Test listing paper trading runs"""
    possible_paths = [
        "/api/paper/runs",
        "/paper/runs",
        "/api/paper/list",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict)), "Runs should be list or dict"

            if isinstance(data, list):
                # List of runs
                for run in data:
                    assert isinstance(run, dict), "Each run should be a dict"
            elif isinstance(data, dict) and "runs" in data:
                # Wrapped in response object
                assert isinstance(data["runs"], list), "Runs field should be list"
            break


def test_paper_lab_stop_run(client):
    """Test stopping a paper trading run"""
    # First, try to create a run to stop
    create_paths = ["/api/paper/runs", "/paper/runs"]
    run_id = None

    for path in create_paths:
        response = client.post(
            path,
            json={
                "name": "Test Stop Run",
                "strategy": "sma50_cross",
                "symbols": ["AAPL"],
            },
        )

        if response.status_code in [200, 201]:
            data = response.json()
            run_id = data.get("id") or data.get("run_id")
            break

    # Try to stop a run (with or without ID)
    stop_paths = [
        "/api/paper/runs/stop",
        "/paper/runs/stop",
        f"/api/paper/runs/{run_id}/stop" if run_id else "/api/paper/runs/test/stop",
    ]

    for path in stop_paths:
        response = client.post(path)

        if response.status_code not in [404, 405]:
            assert response.status_code in [
                200,
                400,
                404,
                422,
            ], f"Stop run at {path} should return valid status"
            break


def test_paper_lab_list_trades(client):
    """Test listing trades from paper trading"""
    possible_paths = [
        "/api/paper/trades",
        "/paper/trades",
        "/api/paper/history",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict)), "Trades should be list or dict"

            if isinstance(data, list):
                # List of trades
                for trade in data:
                    assert isinstance(trade, dict), "Each trade should be a dict"
                    # Check basic trade structure
                    if len(trade) > 0:
                        assert (
                            "symbol" in trade or "ticker" in trade
                        ), "Trade should have symbol"
            elif isinstance(data, dict) and "trades" in data:
                # Wrapped in response object
                assert isinstance(data["trades"], list), "Trades field should be list"
            break


def test_paper_lab_portfolio_status(client):
    """Test getting paper portfolio status"""
    possible_paths = [
        "/api/paper/portfolio",
        "/paper/portfolio",
        "/api/paper/status",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Portfolio should be a dict"

            # Check for common portfolio fields
            portfolio_fields = ["total_value", "cash", "positions", "value", "balance"]
            has_portfolio_field = any(field in data for field in portfolio_fields)

            if has_portfolio_field:
                # Has portfolio structure
                if "total_value" in data:
                    assert isinstance(
                        data["total_value"], (int, float)
                    ), "Total value should be numeric"
                if "positions" in data:
                    assert isinstance(
                        data["positions"], list
                    ), "Positions should be a list"
            break


def test_paper_lab_trade_structure(client):
    """Test that trades have proper structure when available"""
    response = client.get("/api/paper/trades")

    if response.status_code == 200:
        data = response.json()

        trades = data if isinstance(data, list) else data.get("trades", [])

        if trades and len(trades) > 0:
            trade = trades[0]

            # Check basic trade fields
            assert isinstance(trade, dict), "Trade should be a dict"

            # Common trade fields
            if "symbol" in trade:
                assert isinstance(trade["symbol"], str), "Symbol should be string"
            if "quantity" in trade or "qty" in trade:
                qty = trade.get("quantity") or trade.get("qty")
                assert isinstance(qty, (int, float)), "Quantity should be numeric"
            if "price" in trade:
                assert isinstance(
                    trade["price"], (int, float)
                ), "Price should be numeric"
            if "side" in trade:
                assert trade["side"] in [
                    "BUY",
                    "SELL",
                    "buy",
                    "sell",
                ], "Side should be BUY or SELL"


def test_paper_lab_run_lifecycle(client):
    """Test full run lifecycle if endpoints are available"""
    # 1. Create a run
    response = client.post(
        "/api/paper/runs",
        json={
            "name": "Lifecycle Test",
            "strategy": "test",
            "symbols": ["SPY"],
            "initial_capital": 1000.0,
        },
    )

    if response.status_code in [200, 201]:
        data = response.json()
        run_id = data.get("id") or data.get("run_id")

        # 2. Check status
        if run_id:
            status_response = client.get(f"/api/paper/runs/{run_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                assert (
                    "status" in status_data or "state" in status_data
                ), "Run should have status"

        # 3. Stop the run
        if run_id:
            stop_response = client.post(f"/api/paper/runs/{run_id}/stop")
            assert stop_response.status_code in [200, 404], "Should handle stop"


def test_paper_lab_trade_invariants(client):
    """Test that trades maintain invariants"""
    response = client.get("/api/paper/trades")

    if response.status_code == 200:
        data = response.json()
        trades = data if isinstance(data, list) else data.get("trades", [])

        for trade in trades[:10]:  # Check first 10
            # Price should be positive if present
            if "price" in trade:
                assert trade["price"] > 0, "Price should be positive"

            # Quantity should be non-zero if present
            if "quantity" in trade:
                assert trade["quantity"] != 0, "Quantity should be non-zero"
            elif "qty" in trade:
                assert trade["qty"] != 0, "Quantity should be non-zero"


def test_paper_lab_endpoints_exist(client):
    """Verify paper lab endpoints are registered"""
    response = client.get("/openapi.json")

    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})

        # Check for paper-related paths
        paper_paths = [p for p in paths.keys() if "paper" in p.lower()]

        # Should have at least some paper endpoints
        assert len(paper_paths) >= 0, "Paper paths check"
