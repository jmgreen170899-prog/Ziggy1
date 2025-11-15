# ZiggyAI Mobile API & Android Application

## Overview

This directory contains the mobile-optimized API layer and Android application development resources for ZiggyAI. The mobile API provides a lightweight, battery-efficient interface optimized for mobile devices, while the Android development guide provides everything needed to build a native Android app.

## Project Structure

```
mobile/
├── api/                          # Mobile-optimized API endpoints
│   ├── routes_mobile.py         # FastAPI routes for mobile
│   └── __init__.py
├── android/                      # Android app (to be created)
│   └── [Android Studio project files]
├── docs/                         # Documentation
│   ├── MOBILE_API_GUIDE.md      # Complete API documentation
│   └── ANDROID_DEVELOPMENT_GUIDE.md  # Android app dev guide
└── README.md                     # This file
```

## Quick Start

### 1. Start the Backend with Mobile API

The mobile API is automatically loaded when you start the ZiggyAI backend:

```bash
# From the backend directory
cd ../backend
python -m uvicorn app.main:app --reload --port 8000
```

The mobile API will be available at: `http://localhost:8000/mobile`

### 2. Test the Mobile API

```bash
# Health check
curl http://localhost:8000/mobile/health

# Test authentication (mock endpoint)
curl -X POST http://localhost:8000/mobile/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "password",
    "device_id": "test_device_123",
    "device_name": "Test Device"
  }'
```

### 3. View API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Mobile API docs: Filter by "mobile" tag in the interactive docs

## Key Features

### Mobile API Optimizations

✅ **Bandwidth Efficient**

- Compact data structures with minimal payload sizes
- Batch endpoints to reduce number of requests
- Efficient sync mechanism for incremental updates

✅ **Battery Friendly**

- Clear cache TTLs for client-side caching
- Efficient polling intervals based on market status
- Background sync with WorkManager support

✅ **Offline-First**

- Structured responses with timestamp metadata
- Cache-friendly data formats
- Graceful degradation when offline

✅ **Mobile Authentication**

- JWT-based token authentication
- Device registration and tracking
- Secure token refresh mechanism

✅ **Push Notifications**

- FCM integration support
- Alert triggers via push
- Signal notifications

### Available Endpoints

#### Authentication

- `POST /mobile/auth/login` - Login and get JWT tokens
- `POST /mobile/auth/refresh` - Refresh access token
- `POST /mobile/auth/logout` - Logout and invalidate tokens

#### Device Management

- `POST /mobile/device/register` - Register device for push notifications
- `DELETE /mobile/device/unregister` - Unregister device

#### Market Data

- `GET /mobile/market/snapshot` - Get batch quotes (efficient)
- `GET /mobile/market/quote/{symbol}` - Get single quote

#### Trading Features

- `GET /mobile/signals` - Get AI trading signals
- `GET /mobile/portfolio` - Get portfolio summary
- `GET /mobile/alerts` - List price alerts
- `POST /mobile/alerts` - Create price alert
- `DELETE /mobile/alerts/{id}` - Delete alert

#### News & Updates

- `GET /mobile/news` - Get news feed with sentiment

#### Efficient Sync

- `GET /mobile/sync` - **Recommended**: Sync all data in one request

## Development Workflow

### Best Practice: Use the Sync Endpoint

Instead of calling multiple endpoints separately, use the efficient sync endpoint:

```bash
# Initial sync - gets all data
curl http://localhost:8000/mobile/sync \
  -H "Authorization: Bearer <token>"

# Incremental sync - gets only updates since timestamp
curl "http://localhost:8000/mobile/sync?since=1699564800&include=quotes,signals" \
  -H "Authorization: Bearer <token>"
```

This single endpoint returns:

- Market quotes
- Trading signals
- Price alerts
- News items
- Portfolio data

All in one response, reducing battery drain and API calls.

### Android App Development

To build the Android application:

1. **Review the Android Development Guide**
   - See: `docs/ANDROID_DEVELOPMENT_GUIDE.md`
   - Complete guide with code examples
   - Modern Kotlin + Jetpack Compose
   - Clean Architecture + MVVM

2. **Follow the Setup Instructions**
   - Dependencies and configuration
   - Project structure
   - Repository pattern implementation
   - UI components with Compose

3. **Implement Key Features**
   - Authentication flow
   - Offline-first data layer
   - Background sync
   - Push notifications
   - Interactive charts and UI

## API Documentation

### Complete API Reference

See: `docs/MOBILE_API_GUIDE.md`

This comprehensive guide includes:

- Authentication flow
- All endpoint details with examples
- Request/response formats
- Error handling
- Rate limiting
- Mobile implementation patterns
- Security best practices
- Testing instructions

### Android Development Guide

See: `docs/ANDROID_DEVELOPMENT_GUIDE.md`

Complete Android development guide with:

- Technology stack recommendations
- Project setup and dependencies
- Full project structure
- Code examples for all layers
- Networking and API integration
- Repository pattern
- Background sync with WorkManager
- Push notifications with FCM
- Compose UI examples
- Security best practices
- Testing strategies

## Data Models

### Mobile-Optimized Structures

All API responses use compact data structures optimized for mobile:

```python
# Compact quote - minimal bandwidth
{
    "symbol": "AAPL",
    "price": 155.50,
    "change": 1.50,
    "change_pct": 0.97,
    "volume": 50000000,
    "timestamp": 1699564800
}

# Trading signal
{
    "id": "sig_abc123",
    "symbol": "AAPL",
    "action": "BUY",  # BUY, SELL, or HOLD
    "confidence": 0.85,  # 0.0 to 1.0
    "reason": "Strong momentum",
    "timestamp": 1699564800,
    "expires_at": 1699568400
}

# Price alert
{
    "id": "alert_123",
    "symbol": "AAPL",
    "condition": "above",  # or "below"
    "price": 160.00,
    "current_price": 155.50,
    "triggered": false,
    "created_at": 1699564800
}
```

## Implementation Roadmap

### Phase 1: API Foundation ✅ COMPLETE

- [x] Mobile API routes
- [x] Authentication endpoints (mock)
- [x] Market data endpoints
- [x] Trading signals endpoint
- [x] Portfolio endpoint
- [x] Alerts management
- [x] News feed
- [x] Efficient sync endpoint
- [x] API documentation
- [x] Android development guide

### Phase 2: Backend Integration (Next Steps)

- [ ] Connect to real ZiggyAI market data sources
- [ ] Implement JWT authentication with database
- [ ] Add push notification service (FCM)
- [ ] Implement real-time WebSocket support
- [ ] Add rate limiting middleware
- [ ] Set up Redis for caching
- [ ] Add API versioning
- [ ] Implement comprehensive logging

### Phase 3: Android Application Development

- [ ] Create Android Studio project
- [ ] Implement authentication flow
- [ ] Build core UI screens
  - [ ] Login/Registration
  - [ ] Dashboard with portfolio
  - [ ] Market watchlist
  - [ ] Trading signals view
  - [ ] Alerts management
  - [ ] News feed
  - [ ] Settings
- [ ] Implement offline-first data layer
- [ ] Add background sync
- [ ] Integrate push notifications
- [ ] Add charts and visualizations
- [ ] Implement search and filters

### Phase 4: Testing & Polish

- [ ] Unit tests for API endpoints
- [ ] Integration tests
- [ ] Android UI tests
- [ ] Performance testing
- [ ] Security audit
- [ ] Beta testing program
- [ ] App store submission

## Testing the Mobile API

### Manual Testing

1. **Start the backend server:**

```bash
cd backend
python -m uvicorn app.main:app --reload
```

2. **Test authentication:**

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/mobile/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass","device_id":"test123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

3. **Test market data:**

```bash
# Get market snapshot
curl http://localhost:8000/mobile/market/snapshot?symbols=AAPL,GOOGL \
  -H "Authorization: Bearer $TOKEN" | jq

# Get single quote
curl http://localhost:8000/mobile/market/quote/AAPL \
  -H "Authorization: Bearer $TOKEN" | jq
```

4. **Test sync endpoint:**

```bash
# Initial sync
curl http://localhost:8000/mobile/sync \
  -H "Authorization: Bearer $TOKEN" | jq

# Incremental sync
curl "http://localhost:8000/mobile/sync?since=1699564800" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Automated Testing

Add tests in `backend/tests/test_mobile_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

def test_mobile_health(client: TestClient):
    response = client.get("/mobile/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_mobile_login(client: TestClient):
    response = client.post("/mobile/auth/login", json={
        "username": "test",
        "password": "pass",
        "device_id": "test_device"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Configuration

### Environment Variables

The mobile API uses the same configuration as the main ZiggyAI backend:

```env
# API Configuration
ENV=development
DEBUG=True
API_BASE_URL=http://localhost:8000

# JWT Configuration (to be implemented)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Push Notifications (to be implemented)
FCM_SERVER_KEY=your-fcm-server-key
```

## Security Considerations

### Current Implementation

- Mock authentication (for development)
- Basic authorization header validation
- No rate limiting (yet)

### Production Requirements

- [ ] Implement proper JWT authentication
- [ ] Add rate limiting per device/user
- [ ] Implement API key rotation
- [ ] Add request signing for sensitive operations
- [ ] Set up HTTPS/TLS
- [ ] Implement certificate pinning
- [ ] Add intrusion detection
- [ ] Regular security audits

## Performance Optimization

### Caching Strategy

```python
# Recommended caching TTLs
CACHE_TTL = {
    "quotes": 60,          # 1 minute during market hours
    "signals": 300,        # 5 minutes
    "portfolio": 30,       # 30 seconds
    "news": 600,          # 10 minutes
    "alerts": 120,        # 2 minutes
}
```

### Rate Limits

```python
# Recommended rate limits
RATE_LIMITS = {
    "auth": "10/minute",
    "market": "60/minute",
    "sync": "120/minute",
    "alerts": "30/minute",
}
```

## Support & Contributing

### Getting Help

- **API Issues**: Check the API documentation first
- **Android Development**: Review the Android guide
- **Bug Reports**: Open an issue on GitHub
- **Feature Requests**: Open an issue with [Feature] prefix

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Resources

### Documentation

- [Mobile API Guide](docs/MOBILE_API_GUIDE.md) - Complete API reference
- [Android Development Guide](docs/ANDROID_DEVELOPMENT_GUIDE.md) - Build the Android app
- [Main ZiggyAI Docs](../implements/) - Backend architecture docs

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Android Developers](https://developer.android.com)
- [Kotlin Documentation](https://kotlinlang.org/docs/home.html)
- [Jetpack Compose](https://developer.android.com/jetpack/compose)

## License

This project is part of ZiggyAI and follows the same license as the main repository.

## Contact

For questions or support:

- GitHub Issues: https://github.com/jmgreen170899-prog/ZiggyAI/issues
- Email: support@ziggyai.com

---

**Ready to build?** Start with the [Android Development Guide](docs/ANDROID_DEVELOPMENT_GUIDE.md) to begin creating your Android application! 🚀
