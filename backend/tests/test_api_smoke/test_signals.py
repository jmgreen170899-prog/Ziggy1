"""
Signals Domain Smoke Tests

Tests for market brain signal endpoints:
- Feature computation
- Regime detection
- Signal generation
- Trade planning and execution
- Cognitive signals
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


def test_signals_status(client):
    """Test signal system status endpoint"""
    response = client.get("/api/signals/status")
    
    # Should return success or not implemented
    assert response.status_code in [200, 501, 503], \
        "Status endpoint should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_config_get(client):
    """Test get signal configuration"""
    response = client.get("/api/signals/config")
    
    assert response.status_code in [200, 501, 503], \
        "Config endpoint should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_signals_regime(client):
    """Test current regime detection"""
    response = client.get("/api/signals/regime")
    
    assert response.status_code in [200, 501, 503], \
        "Regime endpoint should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        # Common regime fields
        if "regime" in data:
            assert isinstance(data["regime"], str), "Regime should be a string"


def test_signals_regime_history(client):
    """Test regime history endpoint"""
    response = client.get("/api/signals/regime/history")
    
    assert response.status_code in [200, 501, 503], \
        "Regime history should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_features_single(client):
    """Test single ticker feature computation"""
    response = client.get("/api/signals/features/AAPL")
    
    assert response.status_code in [200, 404, 501, 503], \
        "Features endpoint should return 200, 404, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_signals_features_bulk(client):
    """Test bulk feature computation"""
    payload = {
        "tickers": ["AAPL", "MSFT", "GOOGL"]
    }
    
    response = client.post("/api/signals/features/bulk", json=payload)
    
    assert response.status_code in [200, 422, 501, 503], \
        "Bulk features should return 200, 422, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, (dict, list)), "Response should be dict or list"


def test_signals_signal_single(client):
    """Test signal generation for single ticker"""
    response = client.get("/api/signals/signal/AAPL")
    
    assert response.status_code in [200, 404, 501, 503], \
        "Signal endpoint should return 200, 404, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_signals_watchlist(client):
    """Test watchlist signal generation"""
    payload = {
        "tickers": ["AAPL", "MSFT"]
    }
    
    response = client.post("/api/signals/watchlist", json=payload)
    
    assert response.status_code in [200, 422, 501, 503], \
        "Watchlist endpoint should return 200, 422, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_trade_plan(client):
    """Test trade planning endpoint"""
    payload = {
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 10
    }
    
    response = client.post("/api/signals/trade/plan", json=payload)
    
    assert response.status_code in [200, 422, 501, 503], \
        "Trade plan should return 200, 422, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_execute_history(client):
    """Test execution history endpoint"""
    response = client.get("/api/signals/execute/history")
    
    assert response.status_code in [200, 501, 503], \
        "Execute history should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, (dict, list)), "Response should be dict or list"


def test_signals_execute_stats(client):
    """Test execution statistics endpoint"""
    response = client.get("/api/signals/execute/stats")
    
    assert response.status_code in [200, 501, 503], \
        "Execute stats should return 200, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        assert isinstance(data, dict), "Response should be a dict"


def test_signals_backtest_quick(client):
    """Test quick backtest endpoint"""
    response = client.get("/api/signals/backtest/quick/AAPL")
    
    assert response.status_code in [200, 404, 501, 503], \
        "Quick backtest should return 200, 404, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_backtest_analysis(client):
    """Test backtest analysis endpoint"""
    response = client.get("/api/signals/backtest/analysis/AAPL")
    
    assert response.status_code in [200, 404, 501, 503], \
        "Backtest analysis should return 200, 404, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_cognitive_signal(client):
    """Test cognitive signal generation"""
    payload = {
        "symbol": "AAPL",
        "interval": "1D"
    }
    
    response = client.post("/api/signals/cognitive/signal", json=payload)
    
    assert response.status_code in [200, 422, 501, 503], \
        "Cognitive signal should return 200, 422, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"
        
        # Check for expected fields from CognitiveSignalResponse
        if "symbol" in data:
            assert data["symbol"] == "AAPL", "Symbol should match request"
        if "p_up" in data:
            assert isinstance(data["p_up"], (int, float)), "p_up should be numeric"


def test_signals_cognitive_bulk(client):
    """Test bulk cognitive signal generation"""
    payload = {
        "symbols": ["AAPL", "MSFT"]
    }
    
    response = client.post("/api/signals/cognitive/bulk", json=payload)
    
    assert response.status_code in [200, 422, 501, 503], \
        "Cognitive bulk should return 200, 422, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


def test_signals_cognitive_regime(client):
    """Test cognitive regime detection for symbol"""
    response = client.get("/api/signals/cognitive/regime/AAPL")
    
    assert response.status_code in [200, 404, 501, 503], \
        "Cognitive regime should return 200, 404, 501, or 503"
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be None"


# Error handling tests

def test_signals_features_invalid_ticker(client):
    """Test features endpoint with invalid ticker"""
    response = client.get("/api/signals/features/INVALID12345")
    
    # Should handle gracefully
    assert response.status_code in [200, 404, 422, 503], \
        "Should handle invalid ticker gracefully"


def test_signals_signal_empty_ticker(client):
    """Test signal endpoint with empty ticker"""
    response = client.get("/api/signals/signal/")
    
    # Should return 404 for missing path parameter
    assert response.status_code == 404, \
        "Should return 404 for missing ticker"


def test_signals_watchlist_empty(client):
    """Test watchlist with empty ticker list"""
    payload = {"tickers": []}
    
    response = client.post("/api/signals/watchlist", json=payload)
    
    # Should handle empty list
    assert response.status_code in [200, 422], \
        "Should handle empty ticker list"
