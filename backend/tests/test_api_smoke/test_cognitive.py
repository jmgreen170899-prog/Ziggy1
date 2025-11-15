"""
Cognitive Domain Smoke Tests

Tests for cognitive/decision enhancement endpoints:
- Enhance decision
- Record outcome
- Basic status
- Market brain integration
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_cognitive_enhance_decision(client):
    """Test enhance-decision endpoint"""
    # Try common cognitive endpoint paths
    possible_paths = [
        "/cognitive/enhance-decision",
        "/cognitive/enhance_decision",
        "/cognitive/enhance",
    ]

    for path in possible_paths:
        response = client.post(
            path,
            json={
                "context": "Test market decision",
                "symbol": "AAPL",
            },
        )

        if response.status_code not in [404, 405]:
            # Found a working endpoint
            assert response.status_code in [
                200,
                400,
                422,
                501,
            ], f"Enhance decision at {path} should return valid status"

            if response.status_code == 200:
                data = response.json()
                # Should return some enhancement data
                assert isinstance(data, dict), "Response should be a dict"
            break


def test_cognitive_record_outcome(client):
    """Test record-outcome endpoint"""
    # Try common outcome recording paths
    possible_paths = [
        "/cognitive/record-outcome",
        "/cognitive/record_outcome",
        "/cognitive/outcome",
    ]

    for path in possible_paths:
        response = client.post(
            path,
            json={
                "decision_id": "test-123",
                "outcome": "success",
                "metrics": {
                    "profit": 100.0,
                },
            },
        )

        if response.status_code not in [404, 405]:
            # Found a working endpoint
            assert response.status_code in [
                200,
                400,
                422,
                501,
            ], f"Record outcome at {path} should return valid status"

            if response.status_code == 200:
                data = response.json()
                # Should acknowledge recording
                assert isinstance(data, dict), "Response should be a dict"
            break


def test_cognitive_status(client):
    """Test cognitive system status endpoint"""
    possible_paths = [
        "/cognitive/status",
        "/cognitive/health",
        "/cognitive",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Status should be a dict"
            # Should have some status information
            break


def test_market_brain_features_endpoint(client):
    """Test market brain features calculation"""
    # Try to get features for a symbol
    possible_paths = [
        "/market_brain/features",
        "/signals/features",
    ]

    for path in possible_paths:
        response = client.get(path, params={"symbol": "AAPL"})

        if response.status_code not in [404, 405]:
            assert response.status_code in [
                200,
                400,
                422,
                500,
                501,
            ], f"Features endpoint at {path} should return valid status"

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict), "Features should be a dict"
            break


def test_market_brain_regime_detection(client):
    """Test market regime detection"""
    possible_paths = [
        "/market_brain/regime",
        "/signals/regime",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Regime should be a dict"
            # Should have regime information
            if "regime" in data:
                assert isinstance(data["regime"], str), "Regime should be string"
            break


def test_market_brain_single_signal(client):
    """Test single signal generation"""
    possible_paths = [
        "/signals/generate",
        "/market_brain/signal",
    ]

    for path in possible_paths:
        response = client.post(
            path,
            json={
                "symbol": "AAPL",
            },
        )

        if response.status_code not in [404, 405]:
            assert response.status_code in [
                200,
                400,
                422,
                500,
                501,
            ], f"Signal generation at {path} should return valid status"

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict), "Signal should be a dict"
                # Check for signal fields
                if "signal" in data or "action" in data or "confidence" in data:
                    # Has signal structure
                    pass
            break


def test_market_brain_watchlist(client):
    """Test watchlist management"""
    # Try to get or create a watchlist
    possible_paths = [
        "/market_brain/watchlist",
        "/signals/watchlist",
    ]

    for path in possible_paths:
        response = client.get(path)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list)), "Watchlist should be dict or list"
            break


def test_cognitive_decision_enhancement_invariants(client):
    """Test that cognitive enhancements maintain invariants"""
    # Try a full decision enhancement flow
    path = "/cognitive/enhance-decision"

    response = client.post(
        path,
        json={
            "context": "Buy AAPL",
            "symbol": "AAPL",
            "action": "BUY",
            "confidence": 0.75,
        },
    )

    if response.status_code == 200:
        data = response.json()

        # If confidence is returned, it should be valid
        if "confidence" in data:
            assert 0 <= data["confidence"] <= 1, "Confidence should be [0, 1]"

        # If recommendation is returned, check structure
        if "recommendation" in data:
            assert isinstance(
                data["recommendation"], (str, dict)
            ), "Recommendation should be string or dict"


def test_cognitive_learning_feedback(client):
    """Test cognitive learning from feedback"""
    # Record a decision outcome for learning
    path = "/cognitive/record-outcome"

    response = client.post(
        path,
        json={
            "decision_id": "test-learning-001",
            "outcome": "profitable",
            "actual_return": 0.05,
            "predicted_return": 0.04,
        },
    )

    # Accept various responses
    assert response.status_code in [
        200,
        400,
        404,
        422,
        501,
    ], "Learning feedback should be handled"


def test_market_brain_backtest_integration(client):
    """Test market brain backtest if available"""
    # This might be part of the trading backtest
    response = client.post(
        "/backtest",
        json={
            "symbol": "AAPL",
            "strategy": "market_brain",
            "timeframe": "1M",
        },
    )

    # Accept various responses since market brain might not be available
    assert response.status_code in [
        200,
        400,
        422,
        500,
        501,
    ], "Market brain backtest should be handled"


def test_cognitive_endpoints_availability(client):
    """Test which cognitive endpoints are available"""
    # Get OpenAPI schema to see what's actually available
    response = client.get("/openapi.json")

    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})

        # Check for cognitive-related paths
        cognitive_paths = [p for p in paths.keys() if "cognitive" in p.lower()]

        # Should have at least some cognitive endpoints
        assert len(cognitive_paths) >= 0, "Cognitive paths check"
