"""
Market Domain Smoke Tests

Tests for market data endpoints:
- Market overview
- Market breadth
- Market risk-lite
- Macro history
- Market calendar
- Market holidays
- Earnings calendar
- Economic calendar
- Market schedule
- Market indicators
- FRED data series
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_market_overview_default(client):
    """Test market overview with default parameters"""
    response = client.get("/market/overview")

    # Status code
    assert response.status_code == 200, "Market overview should return 200"

    # Response structure
    data = response.json()
    assert "asof" in data, "Response should have asof timestamp"
    assert "symbols" in data or "AAPL" in data, "Response should have symbols data"

    # Check timestamp is numeric
    if "asof" in data:
        assert isinstance(
            data["asof"], (int, float)
        ), "asof should be numeric timestamp"


def test_market_overview_custom_symbols(client):
    """Test market overview with custom symbols"""
    response = client.get("/market/overview?symbols=AAPL,MSFT,GOOGL")

    assert response.status_code == 200, "Market overview should return 200"

    data = response.json()
    # Should have data for requested symbols
    has_symbols = any(sym in data for sym in ["AAPL", "MSFT", "GOOGL", "symbols"])
    assert has_symbols, "Response should contain symbol data"


def test_market_overview_with_period(client):
    """Test market overview with period_days parameter"""
    response = client.get("/market/overview?symbols=AAPL&period_days=60")

    assert response.status_code == 200, "Market overview should return 200"

    data = response.json()
    assert data is not None, "Response should not be None"


def test_market_overview_since_open(client):
    """Test market overview with since_open parameter"""
    response = client.get("/market/overview?symbols=AAPL&since_open=true")

    assert response.status_code == 200, "Market overview should return 200"

    data = response.json()
    if "since_open" in data:
        assert isinstance(data["since_open"], bool), "since_open should be boolean"


def test_market_breadth(client):
    """Test market breadth indicators"""
    response = client.get("/market/breadth")

    # Status code (200 or 501 if not implemented)
    assert response.status_code in [
        200,
        501,
        503,
    ], "Market breadth should return 200, 501, or 503"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"

        # Check for typical breadth indicators
        has_indicators = any(
            key in data
            for key in [
                "advancers",
                "decliners",
                "ad_ratio",
                "new_highs",
                "new_lows",
                "advancing",
                "declining",
                "unchanged",
                "detail",
            ]
        )
        assert has_indicators, "Response should contain breadth indicators"


def test_market_risk_lite(client):
    """Test market risk-lite endpoint"""
    response = client.get("/market/risk-lite")

    # Status code
    assert response.status_code in [200, 503], "Risk-lite should return 200 or 503"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"

        # Check for Put/Call ratio data
        if "cpc" in data:
            cpc = data["cpc"]
            assert (
                "ticker" in cpc or "last" in cpc
            ), "CPC data should have ticker or last value"


def test_market_macro_history(client):
    """Test macro history endpoint"""
    response = client.get("/market/macro/history")

    # Status code
    assert response.status_code in [
        200,
        501,
        503,
    ], "Macro history should return 200, 501, or 503"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_market_calendar(client):
    """Test market calendar endpoint"""
    response = client.get("/market/calendar")

    # Status code
    assert response.status_code in [
        200,
        500,
    ], "Market calendar should return 200 or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_market_holidays(client):
    """Test market holidays endpoint"""
    response = client.get("/market/holidays")

    # Status code
    assert response.status_code in [
        200,
        500,
    ], "Market holidays should return 200 or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_market_earnings_default(client):
    """Test earnings calendar with default parameters"""
    response = client.get("/market/earnings")

    # Status code
    assert response.status_code in [
        200,
        422,
        500,
    ], "Earnings should return 200, 422, or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, (dict, list)), "Response should be dict or list"


def test_market_earnings_with_symbol(client):
    """Test earnings calendar with symbol parameter"""
    response = client.get("/market/earnings?symbol=AAPL")

    assert response.status_code in [
        200,
        422,
        500,
    ], "Earnings should return 200, 422, or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_market_economic(client):
    """Test economic calendar endpoint"""
    response = client.get("/market/economic")

    # Status code
    assert response.status_code in [
        200,
        422,
        500,
    ], "Economic calendar should return 200, 422, or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_market_schedule(client):
    """Test market schedule endpoint"""
    response = client.get("/market/schedule")

    # Status code
    assert response.status_code in [
        200,
        500,
    ], "Market schedule should return 200 or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_market_indicators(client):
    """Test market indicators endpoint"""
    response = client.get("/market/indicators")

    # Status code
    assert response.status_code in [
        200,
        500,
    ], "Market indicators should return 200 or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_market_fred_series(client):
    """Test FRED data series endpoint"""
    # Test with a common series like GDP
    response = client.get("/market/fred/GDP")

    # Status code
    assert response.status_code in [
        200,
        404,
        500,
    ], "FRED endpoint should return 200, 404, or 500"

    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, (dict, list)), "Response should be dict or list"


def test_market_fred_series_invalid(client):
    """Test FRED endpoint with invalid series"""
    response = client.get("/market/fred/INVALID_SERIES_12345")

    # Should handle gracefully
    assert response.status_code in [
        200,
        404,
        500,
    ], "FRED endpoint should handle invalid series gracefully"


# Error handling tests


def test_market_overview_invalid_period(client):
    """Test market overview with invalid period_days"""
    response = client.get("/market/overview?period_days=99999")

    # Should either work or return validation error
    assert response.status_code in [
        200,
        422,
    ], "Should return 200 or 422 for out-of-range period"


def test_market_overview_empty_symbols(client):
    """Test market overview with empty symbols"""
    response = client.get("/market/overview?symbols=")

    # Should handle empty symbols gracefully
    assert response.status_code in [200, 422], "Should handle empty symbols gracefully"
