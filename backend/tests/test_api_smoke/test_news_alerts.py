"""
News & Alerts Domain Smoke Tests

Tests for news and alert endpoints:
- News sentiment
- Alert management
- News sources
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


def test_news_sentiment(client):
    """Test news sentiment analysis"""
    response = client.get("/news/sentiment", params={
        "ticker": "AAPL",
        "lookback_days": 3,
        "limit": 10,
    })
    
    assert response.status_code == 200, "Sentiment should return 200"
    
    data = response.json()
    
    # Check SentimentResponse structure from Phase 1
    assert "ticker" in data, "Should have ticker"
    assert "score" in data, "Should have score"
    assert "label" in data, "Should have label"
    assert "confidence" in data, "Should have confidence"
    assert "sample_count" in data, "Should have sample_count"
    assert "updated_at" in data, "Should have updated_at"
    assert "samples" in data, "Should have samples"
    
    # Type checks
    assert isinstance(data["ticker"], str), "Ticker should be string"
    assert isinstance(data["score"], (int, float)), "Score should be numeric"
    assert isinstance(data["label"], str), "Label should be string"
    assert isinstance(data["confidence"], (int, float)), "Confidence should be numeric"
    assert isinstance(data["sample_count"], int), "Sample count should be int"
    assert isinstance(data["samples"], list), "Samples should be list"
    
    # Value invariants
    assert -1 <= data["score"] <= 1, "Score should be in [-1, 1]"
    assert 0 <= data["confidence"] <= 1, "Confidence should be in [0, 1]"
    assert data["label"] in ["negative", "neutral", "positive"], \
        "Label should be negative/neutral/positive"
    assert data["ticker"] == "AAPL", "Ticker should match request"


def test_news_sentiment_samples_structure(client):
    """Test sentiment samples have proper structure"""
    response = client.get("/news/sentiment", params={
        "ticker": "MSFT",
        "limit": 5,
    })
    
    if response.status_code == 200:
        data = response.json()
        samples = data.get("samples", [])
        
        if len(samples) > 0:
            sample = samples[0]
            
            # Check SentimentSample structure from Phase 1
            assert "source" in sample, "Sample should have source"
            assert "title" in sample, "Sample should have title"
            assert "url" in sample, "Sample should have url"
            assert "published" in sample, "Sample should have published"
            assert "score" in sample, "Sample should have score"
            assert "label" in sample, "Sample should have label"
            
            # Type checks
            assert isinstance(sample["source"], str), "Source should be string"
            assert isinstance(sample["title"], str), "Title should be string"
            assert isinstance(sample["score"], (int, float)), "Score should be numeric"
            
            # Value checks
            assert -1 <= sample["score"] <= 1, "Sample score should be in [-1, 1]"


def test_news_ping(client):
    """Test news service ping"""
    response = client.get("/news/ping")
    
    assert response.status_code == 200, "News ping should return 200"
    
    data = response.json()
    
    # Check NewsPingResponse structure from Phase 1
    assert "status" in data, "Should have status"
    assert "asof" in data, "Should have asof timestamp"
    
    # Type checks
    assert isinstance(data["status"], str), "Status should be string"
    assert isinstance(data["asof"], (int, float)), "Timestamp should be numeric"


def test_alerts_status(client):
    """Test alert system status"""
    response = client.get("/alerts/status")
    
    assert response.status_code == 200, "Alerts status should return 200"
    
    data = response.json()
    
    # Check AlertStatusResponse structure from Phase 1
    assert "ok" in data, "Should have ok"
    assert "enabled" in data, "Should have enabled"
    assert "asof" in data, "Should have asof"
    
    # Type checks
    assert isinstance(data["ok"], bool), "ok should be boolean"
    assert isinstance(data["enabled"], bool), "enabled should be boolean"
    assert isinstance(data["asof"], (int, float)), "asof should be numeric"


def test_alerts_start(client):
    """Test starting alert scanning"""
    response = client.post("/alerts/start")
    
    assert response.status_code == 200, "Alerts start should return 200"
    
    data = response.json()
    
    # Check AlertStatusResponse structure
    assert "ok" in data, "Should have ok"
    assert "enabled" in data, "Should have enabled"
    assert isinstance(data["enabled"], bool), "enabled should be boolean"
    
    # After starting, should be enabled
    assert data["enabled"] == True, "Should be enabled after start"


def test_alerts_stop(client):
    """Test stopping alert scanning"""
    response = client.post("/alerts/stop")
    
    assert response.status_code == 200, "Alerts stop should return 200"
    
    data = response.json()
    
    # Check AlertStatusResponse structure
    assert "ok" in data, "Should have ok"
    assert "enabled" in data, "Should have enabled"
    assert isinstance(data["enabled"], bool), "enabled should be boolean"
    
    # After stopping, should be disabled
    assert data["enabled"] == False, "Should be disabled after stop"


def test_alerts_create_sma50(client):
    """Test creating a 50-day SMA alert"""
    payload = {
        "symbol": "AAPL",
        "rule": "cross",
    }
    
    response = client.post("/alerts/sma50", json=payload)
    
    assert response.status_code == 200, "SMA50 alert creation should return 200"
    
    data = response.json()
    
    # Check AlertResponse structure from Phase 1
    assert "ok" in data, "Should have ok"
    assert "message" in data, "Should have message"
    assert "asof" in data, "Should have asof"
    
    # Type checks
    assert isinstance(data["ok"], bool), "ok should be boolean"
    assert isinstance(data["message"], str), "message should be string"
    
    # If alert created successfully
    if data["ok"] and "alert" in data and data["alert"]:
        alert = data["alert"]
        assert isinstance(alert, dict), "Alert should be dict"
        
        # Check AlertRecord structure
        if "id" in alert:
            assert isinstance(alert["id"], str), "Alert ID should be string"
        if "symbol" in alert:
            assert alert["symbol"] == "AAPL", "Symbol should match"


def test_alerts_deprecated_alias(client):
    """Test deprecated alert alias endpoint"""
    payload = {
        "symbol": "MSFT",
    }
    
    # This is the deprecated alias from Phase 1
    response = client.post("/alerts/moving-average/50", json=payload)
    
    # Should still work (backward compatibility) or return 404 if removed
    assert response.status_code in [200, 404], \
        "Deprecated alias should work or return 404"


def test_news_deprecated_headwind_alias(client):
    """Test deprecated news sentiment alias"""
    # /headwind was marked as deprecated in Phase 1
    response = client.get("/news/headwind", params={
        "ticker": "TSLA",
    })
    
    # Should still work for backward compatibility
    assert response.status_code in [200, 404], \
        "Deprecated headwind alias should work or return 404"
    
    if response.status_code == 200:
        data = response.json()
        # Should have same structure as /sentiment
        assert "ticker" in data or "score" in data, \
            "Should have sentiment structure"


def test_news_sentiment_without_ticker(client):
    """Test sentiment without ticker parameter"""
    response = client.get("/news/sentiment")
    
    # Should require ticker
    assert response.status_code in [400, 422], \
        "Sentiment without ticker should return 400 or 422"


def test_alerts_lifecycle(client):
    """Test full alert lifecycle"""
    # 1. Check initial status
    status1 = client.get("/alerts/status")
    assert status1.status_code == 200
    
    # 2. Stop alerts
    stop = client.post("/alerts/stop")
    assert stop.status_code == 200
    assert stop.json()["enabled"] == False
    
    # 3. Start alerts
    start = client.post("/alerts/start")
    assert start.status_code == 200
    assert start.json()["enabled"] == True
    
    # 4. Create an alert
    create = client.post("/alerts/sma50", json={"symbol": "SPY"})
    assert create.status_code == 200
    assert create.json()["ok"] == True


def test_news_sentiment_caching(client):
    """Test that sentiment responses are cached"""
    # Make same request twice
    response1 = client.get("/news/sentiment", params={
        "ticker": "AAPL",
        "lookback_days": 3,
    })
    
    response2 = client.get("/news/sentiment", params={
        "ticker": "AAPL",
        "lookback_days": 3,
    })
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        # Should return same timestamp (cached)
        assert data1["updated_at"] == data2["updated_at"], \
            "Cached responses should have same timestamp"


def test_news_sentiment_multiple_tickers(client):
    """Test sentiment for multiple tickers"""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    for ticker in tickers:
        response = client.get("/news/sentiment", params={"ticker": ticker})
        
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == ticker, f"Ticker should be {ticker}"
            assert "score" in data, f"Should have score for {ticker}"


def test_alerts_endpoints_availability(client):
    """Verify alerts and news endpoints are registered"""
    response = client.get("/openapi.json")
    
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})
        
        # Check for alerts endpoints
        assert any("/alerts/status" in p for p in paths), \
            "Should have alerts/status"
        assert any("/alerts/start" in p for p in paths), \
            "Should have alerts/start"
        assert any("/alerts/stop" in p for p in paths), \
            "Should have alerts/stop"
        
        # Check for news endpoints
        assert any("/news/sentiment" in p for p in paths), \
            "Should have news/sentiment"
