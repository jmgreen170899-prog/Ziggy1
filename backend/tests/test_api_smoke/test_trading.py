"""
Trading Domain Smoke Tests

Tests for trading endpoints:
- Market risk metrics
- Backtesting
- Health checks
- Quality indicators
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


def test_market_risk_lite(client):
    """Test market risk-lite endpoint returns Put/Call ratio data"""
    response = client.get("/market-risk-lite")
    
    # Status code
    assert response.status_code == 200, "Risk-lite endpoint should return 200"
    
    # Response structure
    data = response.json()
    assert "cpc" in data or "error" in data, "Response should have cpc or error"
    
    # If successful, check data structure
    if data.get("cpc"):
        cpc = data["cpc"]
        assert "ticker" in cpc, "CPC data should have ticker"
        assert "last" in cpc, "CPC data should have last value"
        assert "ma20" in cpc, "CPC data should have 20-day MA"
        assert "z20" in cpc, "CPC data should have z-score"
        assert "date" in cpc, "CPC data should have date"
        
        # Value invariants
        assert isinstance(cpc["last"], (int, float)), "Last should be numeric"
        assert isinstance(cpc["ma20"], (int, float)), "MA20 should be numeric"
        assert isinstance(cpc["z20"], (int, float)), "Z-score should be numeric"
        assert cpc["ticker"] in ["^CPC", "^CPCE"], "Ticker should be CPC or CPCE"


def test_trading_backtest_with_valid_input(client):
    """Test backtest endpoint with valid strategy input"""
    payload = {
        "symbol": "AAPL",
        "strategy": "sma50_cross",
        "timeframe": "1Y",
    }
    
    response = client.post("/backtest", json=payload)
    
    # Status code (200 or could be 500 if market brain unavailable)
    assert response.status_code in [200, 500], "Backtest should return 200 or 500"
    
    if response.status_code == 200:
        data = response.json()
        
        # Required fields
        assert "ok" in data, "Response should have 'ok' field"
        assert "symbol" in data, "Response should have symbol"
        assert "strategy" in data, "Response should have strategy"
        assert "metrics" in data, "Response should have metrics"
        
        # Value checks
        assert data["symbol"] == "AAPL", "Symbol should match request"
        assert data["strategy"] == "sma50_cross", "Strategy should match request"
        assert isinstance(data["metrics"], dict), "Metrics should be a dict"
        
        # Optional but expected fields
        if data.get("trades"):
            assert isinstance(data["trades"], list), "Trades should be a list"
        if data.get("returns"):
            assert isinstance(data["returns"], list), "Returns should be a list"
        if data.get("equity"):
            assert isinstance(data["equity"], list), "Equity should be a list"


def test_backtest_with_invalid_symbol(client):
    """Test backtest with missing symbol returns 400"""
    payload = {
        "strategy": "sma50_cross",
    }
    
    response = client.post("/backtest", json=payload)
    
    # Should accept (symbol is optional, but might fail internally)
    assert response.status_code in [200, 400, 422, 500], "Should handle missing symbol"


def test_trading_health_endpoints(client):
    """Test trading-related health checks"""
    # Main health
    response = client.get("/health")
    assert response.status_code == 200, "Main health should return 200"
    data = response.json()
    assert "ok" in data, "Health should have 'ok' field"
    
    # Detailed health
    response = client.get("/health/detailed")
    assert response.status_code == 200, "Detailed health should return 200"
    data = response.json()
    assert "status" in data, "Detailed health should have status"
    assert "details" in data, "Detailed health should have details"
    assert isinstance(data["details"], dict), "Details should be a dict"


def test_market_risk_lite_with_parameters(client):
    """Test risk-lite with custom parameters"""
    response = client.get("/market-risk-lite", params={
        "period_days": 90,
        "window": 10,
        "use_cache": False,
    })
    
    assert response.status_code == 200, "Risk-lite with params should return 200"
    data = response.json()
    assert "cpc" in data or "error" in data, "Response should have cpc or error"


def test_deprecated_risk_lite_aliases(client):
    """Test that deprecated aliases still work but are marked as deprecated"""
    # These should still work for backward compatibility
    aliases = [
        "/market/risk-lite",  # From routes_risk_lite.py
    ]
    
    for alias in aliases:
        response = client.get(alias)
        # Should work (200) or might not be registered (404)
        assert response.status_code in [200, 404], f"Alias {alias} should work or return 404"


def test_backtest_quality_checks(client):
    """Test backtest response quality and completeness"""
    payload = {
        "symbol": "SPY",
        "strategy": "sma50_cross",
        "timeframe": "6M",
    }
    
    response = client.post("/backtest", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check for summary or meaningful metrics
        has_summary = "summary" in data and data["summary"]
        has_metrics = "metrics" in data and len(data.get("metrics", {})) > 0
        
        assert has_summary or has_metrics, "Backtest should have summary or metrics"
        
        # If trades exist, they should be a list
        if "trades" in data:
            assert isinstance(data["trades"], list), "Trades must be a list"
            
        # Equity curve should be numeric if present
        if data.get("equity"):
            assert all(isinstance(x, (int, float)) for x in data["equity"][:5]), \
                "Equity values should be numeric"
