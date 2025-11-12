"""
Standalone test script for the Mobile API

This script tests the mobile API endpoints without requiring a full backend setup.
It creates a minimal FastAPI application with just the mobile router.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add mobile directory to path
mobile_path = Path(__file__).parent
if str(mobile_path) not in sys.path:
    sys.path.insert(0, str(mobile_path))

# Import the mobile router
from api.routes_mobile import router

# Create minimal FastAPI app
app = FastAPI(title="ZiggyAI Mobile API Test")
app.include_router(router)

# Create test client
client = TestClient(app)


def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    response = client.get("/mobile/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "api_version" in data
    print(f"✓ Health check passed: {data}")


def test_login():
    """Test login endpoint"""
    print("\nTesting login endpoint...")
    response = client.post("/mobile/auth/login", json={
        "username": "test@example.com",
        "password": "password123",
        "device_id": "test_device_123",
        "device_name": "Test Device"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user_id"] == "test@example.com"
    print(f"✓ Login passed: Got access token")
    return data["access_token"]


def test_market_snapshot(token):
    """Test market snapshot endpoint"""
    print("\nTesting market snapshot endpoint...")
    response = client.get(
        "/mobile/market/snapshot?symbols=AAPL,GOOGL,MSFT",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "quotes" in data
    assert len(data["quotes"]) == 3
    assert data["market_status"] in ["open", "closed", "pre", "post"]
    print(f"✓ Market snapshot passed: Got {len(data['quotes'])} quotes")
    print(f"  Sample quote: {data['quotes'][0]}")


def test_single_quote(token):
    """Test single quote endpoint"""
    print("\nTesting single quote endpoint...")
    response = client.get(
        "/mobile/market/quote/AAPL",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "price" in data
    assert "change" in data
    print(f"✓ Single quote passed: AAPL at ${data['price']}")


def test_signals(token):
    """Test signals endpoint"""
    print("\nTesting signals endpoint...")
    response = client.get(
        "/mobile/signals?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        signal = data[0]
        assert "symbol" in signal
        assert signal["action"] in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= signal["confidence"] <= 1.0
        print(f"✓ Signals passed: Got {len(data)} signals")
        print(f"  Sample: {signal['action']} {signal['symbol']} (confidence: {signal['confidence']})")
    else:
        print(f"✓ Signals passed: Got empty list (expected for mock)")


def test_portfolio(token):
    """Test portfolio endpoint"""
    print("\nTesting portfolio endpoint...")
    response = client.get(
        "/mobile/portfolio",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_value" in data
    assert "cash" in data
    assert "positions" in data
    print(f"✓ Portfolio passed: Total value ${data['total_value']:,.2f}")


def test_alerts(token):
    """Test alerts endpoints"""
    print("\nTesting alerts endpoints...")
    
    # List alerts
    response = client.get(
        "/mobile/alerts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    print(f"✓ List alerts passed: Got {len(alerts)} alerts")
    
    # Create alert
    response = client.post(
        "/mobile/alerts?symbol=AAPL&condition=above&price=160.0",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    print(f"✓ Create alert passed: Created alert for AAPL")


def test_news(token):
    """Test news endpoint"""
    print("\nTesting news endpoint...")
    response = client.get(
        "/mobile/news?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        news = data[0]
        assert "title" in news
        assert "id" in news
        print(f"✓ News passed: Got {len(data)} news items")
    else:
        print(f"✓ News passed: Got empty list (expected for mock)")


def test_sync(token):
    """Test sync endpoint"""
    print("\nTesting sync endpoint...")
    response = client.get(
        "/mobile/sync?include=all",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "quotes" in data
    assert "signals" in data
    assert "alerts" in data
    assert "news" in data
    assert "portfolio" in data
    assert "sync_token" in data
    print(f"✓ Sync passed: Got complete data snapshot")
    print(f"  - Quotes: {len(data['quotes'])}")
    print(f"  - Signals: {len(data['signals'])}")
    print(f"  - Portfolio value: ${data['portfolio']['total_value']:,.2f}")


def test_unauthorized_access():
    """Test that endpoints require authentication"""
    print("\nTesting unauthorized access...")
    response = client.get("/mobile/market/snapshot?symbols=AAPL")
    assert response.status_code == 401
    print("✓ Unauthorized access properly rejected")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ZiggyAI Mobile API Test Suite")
    print("=" * 60)
    
    try:
        # Test health (no auth required)
        test_health()
        
        # Test login and get token
        token = test_login()
        
        # Test authenticated endpoints
        test_market_snapshot(token)
        test_single_quote(token)
        test_signals(token)
        test_portfolio(token)
        test_alerts(token)
        test_news(token)
        test_sync(token)
        
        # Test security
        test_unauthorized_access()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nMobile API is working correctly.")
        print("Next steps:")
        print("1. Integrate with real ZiggyAI backend services")
        print("2. Implement JWT authentication")
        print("3. Add push notification support")
        print("4. Start building the Android app")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
