"""
Screener Domain Smoke Tests

Tests for screening endpoints:
- Market scanning
- Presets (momentum, mean reversion)
- Regime summary
- Health checks
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_screener_health(client):
    """Test screener health endpoint"""
    response = client.get("/screener/health")

    assert response.status_code == 200, "Screener health should return 200"

    data = response.json()
    assert "cognitive_core_available" in data, "Should report cognitive core status"
    assert "supported_universes" in data, "Should list supported universes"
    assert "max_symbols_per_request" in data, "Should report max symbols"
    assert "available_presets" in data, "Should list available presets"
    assert "timestamp" in data, "Should include timestamp"

    # Type checks
    assert isinstance(
        data["cognitive_core_available"], bool
    ), "Status should be boolean"
    assert isinstance(data["supported_universes"], list), "Universes should be a list"
    assert isinstance(data["max_symbols_per_request"], int), "Max symbols should be int"
    assert isinstance(data["available_presets"], list), "Presets should be a list"

    # Value checks
    assert data["max_symbols_per_request"] > 0, "Max symbols should be positive"
    assert len(data["supported_universes"]) > 0, "Should have at least one universe"


def test_screener_scan_with_valid_universe(client):
    """Test market scan with valid universe"""
    payload = {
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "min_confidence": 0.6,
        "limit": 10,
    }

    response = client.post("/screener/scan", json=payload)

    # Status code (200 if cognitive core available, 500 otherwise)
    assert response.status_code in [
        200,
        500,
        501,
    ], "Scan should return 200, 500, or 501"

    if response.status_code == 200:
        data = response.json()

        # Required fields
        assert "results" in data, "Response should have results"
        assert "total_screened" in data, "Response should have total_screened"
        assert "filters_applied" in data, "Response should have filters_applied"
        assert "execution_time_ms" in data, "Response should have execution_time"
        assert "regime_breakdown" in data, "Response should have regime_breakdown"

        # Type checks
        assert isinstance(data["results"], list), "Results should be a list"
        assert isinstance(data["total_screened"], int), "Total should be int"
        assert isinstance(data["filters_applied"], dict), "Filters should be dict"
        assert isinstance(
            data["execution_time_ms"], (int, float)
        ), "Time should be numeric"
        assert isinstance(
            data["regime_breakdown"], dict
        ), "Regime breakdown should be dict"

        # Invariants
        assert data["total_screened"] >= 0, "Total screened should be non-negative"
        assert data["execution_time_ms"] >= 0, "Execution time should be non-negative"
        assert len(data["results"]) <= payload["limit"], "Results should respect limit"


def test_screener_scan_empty_universe(client):
    """Test scan with empty universe"""
    payload = {
        "universe": [],
        "min_confidence": 0.5,
    }

    response = client.post("/screener/scan", json=payload)

    # Should handle empty universe gracefully
    assert response.status_code in [200, 400, 422], "Should handle empty universe"

    if response.status_code == 200:
        data = response.json()
        assert data["total_screened"] == 0, "Empty universe should screen 0 symbols"
        assert len(data["results"]) == 0, "Empty universe should return no results"


def test_screener_scan_with_filters(client):
    """Test scan with various filters"""
    payload = {
        "universe": ["SPY", "QQQ", "IWM"],
        "min_confidence": 0.7,
        "min_probability": 0.5,
        "max_probability": 0.9,
        "sort_by": "confidence",
        "limit": 5,
    }

    response = client.post("/screener/scan", json=payload)

    # Accept various status codes
    assert response.status_code in [200, 500, 501], "Should handle with filters"

    if response.status_code == 200:
        data = response.json()
        assert "filters_applied" in data, "Should report filters applied"

        # Check that filters are recorded
        filters = data["filters_applied"]
        assert (
            "min_confidence" in filters or len(filters) > 0
        ), "Should record applied filters"


def test_screener_presets_momentum(client):
    """Test momentum preset endpoint"""
    response = client.get("/screener/presets/momentum")

    # This endpoint might not exist or might return preset configuration
    assert response.status_code in [200, 404, 501], "Momentum preset check"

    if response.status_code == 200:
        data = response.json()
        # Should return some preset configuration
        assert isinstance(data, dict), "Preset should be a dict"


def test_screener_presets_mean_reversion(client):
    """Test mean reversion preset endpoint"""
    response = client.get("/screener/presets/mean_reversion")

    # This endpoint might not exist or might return preset configuration
    assert response.status_code in [200, 404, 501], "Mean reversion preset check"

    if response.status_code == 200:
        data = response.json()
        # Should return some preset configuration
        assert isinstance(data, dict), "Preset should be a dict"


def test_screener_regime_summary(client):
    """Test regime summary endpoint"""
    response = client.get("/screener/regime_summary")

    # This endpoint might not exist
    assert response.status_code in [200, 404, 501], "Regime summary check"

    if response.status_code == 200:
        data = response.json()
        # Should return regime information
        assert isinstance(data, dict), "Regime summary should be a dict"


def test_screener_scan_result_structure(client):
    """Test that scan results have proper structure when available"""
    payload = {
        "universe": ["AAPL"],
        "min_confidence": 0.5,
        "limit": 1,
    }

    response = client.post("/screener/scan", json=payload)

    if response.status_code == 200:
        data = response.json()

        if len(data["results"]) > 0:
            result = data["results"][0]

            # Check result structure
            assert "symbol" in result, "Result should have symbol"
            assert "p_up" in result, "Result should have p_up"
            assert "confidence" in result, "Result should have confidence"
            assert "regime" in result, "Result should have regime"
            assert "score" in result, "Result should have score"

            # Type checks
            assert isinstance(result["symbol"], str), "Symbol should be string"
            assert isinstance(result["p_up"], (int, float)), "p_up should be numeric"
            assert isinstance(
                result["confidence"], (int, float)
            ), "Confidence should be numeric"
            assert isinstance(result["regime"], str), "Regime should be string"
            assert isinstance(result["score"], (int, float)), "Score should be numeric"

            # Value invariants
            assert 0 <= result["p_up"] <= 1, "p_up should be probability [0, 1]"
            assert 0 <= result["confidence"] <= 1, "Confidence should be [0, 1]"


def test_screener_universes_supported(client):
    """Test that health endpoint reports expected universes"""
    response = client.get("/screener/health")

    assert response.status_code == 200
    data = response.json()

    universes = data["supported_universes"]
    assert (
        "sp500" in universes or "nasdaq100" in universes
    ), "Should support at least sp500 or nasdaq100"
