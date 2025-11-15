# ZiggyAI Mobile API Guide

## Overview

The ZiggyAI Mobile API provides a lightweight, battery-efficient interface for Android applications to access ZiggyAI's trading intelligence platform. This API is optimized for mobile devices with:

- **Minimal bandwidth usage** through compact data structures
- **Battery efficiency** via efficient sync mechanisms
- **Offline-first architecture** with clear cache TTLs
- **Push notification support** for real-time alerts
- **JWT-based authentication** for secure mobile access

## Base URL

```
Production: https://api.ziggyai.com/mobile
Development: http://localhost:8000/mobile
```

## Authentication

### Login

**Endpoint:** `POST /mobile/auth/login`

Authenticate and receive JWT tokens for API access.

**Request:**

```json
{
  "username": "user@example.com",
  "password": "secure_password",
  "device_id": "unique_device_identifier",
  "device_name": "Samsung Galaxy S21"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "user_id": "user_123",
  "preferences": {
    "theme": "dark",
    "notifications_enabled": true,
    "default_watchlist": ["AAPL", "GOOGL", "MSFT"]
  }
}
```

**Security Best Practices:**

- Store tokens securely using Android Keystore
- Never log or display tokens
- Implement token refresh before expiration
- Clear tokens on logout

### Using Authentication

Include the access token in all API requests:

```
Authorization: Bearer <access_token>
```

### Token Refresh

**Endpoint:** `POST /mobile/auth/refresh`

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

## Core Endpoints

### 1. Efficient Data Sync (Recommended)

**Endpoint:** `GET /mobile/sync`

The most efficient way to fetch data - combines all updates in a single request.

**Query Parameters:**

- `since` (optional): Unix timestamp for incremental sync
- `include` (optional): Comma-separated list: `quotes,signals,alerts,news,portfolio`

**Example - Initial Sync:**

```bash
GET /mobile/sync?include=all
```

**Example - Incremental Sync:**

```bash
GET /mobile/sync?since=1699564800&include=quotes,signals
```

**Response:**

```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "price": 155.5,
      "change": 1.5,
      "change_pct": 0.97,
      "volume": 50000000,
      "timestamp": 1699564800
    }
  ],
  "signals": [
    {
      "id": "sig_abc123",
      "symbol": "AAPL",
      "action": "BUY",
      "confidence": 0.85,
      "reason": "Strong upward momentum with positive sentiment",
      "timestamp": 1699564800,
      "expires_at": 1699568400
    }
  ],
  "alerts": [],
  "news": [],
  "portfolio": {
    "total_value": 100000.0,
    "cash": 25000.0,
    "day_change": 1250.0,
    "day_change_pct": 1.25,
    "positions": [],
    "updated_at": 1699564800
  },
  "sync_token": "1699564800",
  "has_more": false
}
```

**Mobile Implementation Pattern:**

```kotlin
class DataSyncManager {
    private var lastSyncTimestamp: Long = 0

    suspend fun sync() {
        val response = api.sync(
            since = if (lastSyncTimestamp > 0) lastSyncTimestamp else null,
            include = "all"
        )

        // Update local cache
        database.updateQuotes(response.quotes)
        database.updateSignals(response.signals)

        // Store sync token for next request
        lastSyncTimestamp = response.sync_token.toLong()
    }
}
```

### 2. Market Data

#### Get Market Snapshot

**Endpoint:** `GET /mobile/market/snapshot`

Get compact quotes for multiple symbols in one request.

**Query Parameters:**

- `symbols`: Comma-separated list (max 20 symbols)

**Example:**

```bash
GET /mobile/market/snapshot?symbols=AAPL,GOOGL,MSFT,TSLA
```

**Response:**

```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "price": 155.5,
      "change": 1.5,
      "change_pct": 0.97,
      "volume": 50000000,
      "timestamp": 1699564800
    }
  ],
  "market_status": "open",
  "updated_at": 1699564800,
  "cache_ttl": 60
}
```

**Cache Strategy:**

- Use `cache_ttl` to determine when to refresh
- Cache locally for offline access
- Show stale data with visual indicator after TTL

#### Get Single Quote

**Endpoint:** `GET /mobile/market/quote/{symbol}`

**Example:**

```bash
GET /mobile/market/quote/AAPL
```

**Note:** For multiple symbols, use the snapshot endpoint to reduce API calls.

### 3. Trading Signals

**Endpoint:** `GET /mobile/signals`

Get AI-generated trading signals optimized for mobile display.

**Query Parameters:**

- `limit` (optional): Number of signals (1-50, default: 10)
- `symbols` (optional): Filter by specific symbols

**Example:**

```bash
GET /mobile/signals?limit=10&symbols=AAPL,GOOGL
```

**Response:**

```json
[
  {
    "id": "sig_abc123",
    "symbol": "AAPL",
    "action": "BUY",
    "confidence": 0.85,
    "reason": "Strong upward momentum with positive sentiment",
    "timestamp": 1699564800,
    "expires_at": 1699568400
  }
]
```

**Signal Actions:**

- `BUY`: Recommended to buy
- `SELL`: Recommended to sell
- `HOLD`: Recommended to hold position

### 4. Portfolio

**Endpoint:** `GET /mobile/portfolio`

Get compact portfolio summary.

**Response:**

```json
{
  "total_value": 100000.0,
  "cash": 25000.0,
  "day_change": 1250.0,
  "day_change_pct": 1.25,
  "positions": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "value": 15000.0,
      "change_pct": 1.5
    }
  ],
  "updated_at": 1699564800
}
```

### 5. Alerts

#### List Alerts

**Endpoint:** `GET /mobile/alerts`

**Query Parameters:**

- `active_only` (optional): Show only active alerts (default: true)

**Response:**

```json
[
  {
    "id": "alert_123",
    "symbol": "AAPL",
    "condition": "above",
    "price": 160.0,
    "current_price": 155.5,
    "triggered": false,
    "created_at": 1699564800
  }
]
```

#### Create Alert

**Endpoint:** `POST /mobile/alerts`

**Request:**

```json
{
  "symbol": "AAPL",
  "condition": "above",
  "price": 160.0
}
```

**Response:**

```json
{
  "id": "alert_new",
  "status": "created",
  "symbol": "AAPL",
  "condition": "above",
  "price": 160.0
}
```

#### Delete Alert

**Endpoint:** `DELETE /mobile/alerts/{alert_id}`

### 6. News Feed

**Endpoint:** `GET /mobile/news`

**Query Parameters:**

- `limit` (optional): Number of items (1-100, default: 20)
- `symbols` (optional): Filter by symbols

**Response:**

```json
[
  {
    "id": "news_123",
    "title": "Apple announces new product lineup",
    "summary": "Apple unveiled new products at their latest event...",
    "symbol": "AAPL",
    "sentiment": 0.7,
    "published_at": 1699564800,
    "source": "TechNews"
  }
]
```

**Sentiment Values:**

- Range: -1.0 (very negative) to 1.0 (very positive)
- 0.0: neutral

### 7. Device Management

#### Register Device

**Endpoint:** `POST /mobile/device/register`

Register device for push notifications.

**Request:**

```json
{
  "device_id": "unique_device_id",
  "device_name": "Samsung Galaxy S21",
  "push_token": "fcm_token_here",
  "os_version": "Android 13",
  "app_version": "1.0.0"
}
```

**Response:**

```json
{
  "status": "registered",
  "device_id": "unique_device_id",
  "push_enabled": true
}
```

#### Unregister Device

**Endpoint:** `DELETE /mobile/device/unregister?device_id=<id>`

## Mobile Implementation Best Practices

### 1. Network Efficiency

```kotlin
// Use sync endpoint for periodic updates
class ZiggyRepository {
    suspend fun syncData() {
        // Combine all data fetches into single sync call
        val response = api.sync(
            since = lastSyncTime,
            include = "quotes,signals,portfolio"
        )

        // Update local database
        updateLocalCache(response)
    }
}

// Schedule efficient background sync
WorkManager.getInstance(context).enqueuePeriodicWork(
    PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
        .setConstraints(
            Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
        )
        .build()
)
```

### 2. Offline-First Architecture

```kotlin
class MarketDataRepository(
    private val api: ZiggyApiService,
    private val database: ZiggyDatabase
) {
    fun getQuotes(symbols: List<String>): Flow<List<Quote>> = flow {
        // Emit cached data immediately
        emit(database.getQuotes(symbols))

        // Fetch fresh data in background
        try {
            val fresh = api.getMarketSnapshot(symbols.joinToString(","))
            database.updateQuotes(fresh.quotes)
            emit(fresh.quotes)
        } catch (e: Exception) {
            // Continue showing cached data on error
        }
    }
}
```

### 3. Battery Optimization

```kotlin
// Use appropriate sync intervals
enum class SyncInterval(val minutes: Long) {
    MARKET_OPEN(5),      // During market hours
    MARKET_CLOSED(30),   // After hours
    OVERNIGHT(60)        // Overnight
}

// Adjust based on market status
fun getSyncInterval(marketStatus: String): Long {
    return when (marketStatus) {
        "open" -> SyncInterval.MARKET_OPEN.minutes
        "pre", "post" -> SyncInterval.MARKET_CLOSED.minutes
        else -> SyncInterval.OVERNIGHT.minutes
    }
}
```

### 4. Error Handling

```kotlin
sealed class ApiResult<T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error<T>(val message: String, val code: Int) : ApiResult<T>()
    data class NetworkError<T>(val exception: Exception) : ApiResult<T>()
}

suspend fun <T> safeApiCall(call: suspend () -> T): ApiResult<T> {
    return try {
        ApiResult.Success(call())
    } catch (e: HttpException) {
        ApiResult.Error(e.message(), e.code())
    } catch (e: IOException) {
        ApiResult.NetworkError(e)
    }
}
```

### 5. Push Notifications

```kotlin
// Handle FCM messages
class ZiggyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(message: RemoteMessage) {
        when (message.data["type"]) {
            "alert_triggered" -> showAlertNotification(message.data)
            "signal_new" -> showSignalNotification(message.data)
            "news" -> showNewsNotification(message.data)
        }
    }

    override fun onNewToken(token: String) {
        // Update token on server
        api.registerDevice(
            deviceId = getDeviceId(),
            pushToken = token
        )
    }
}
```

## Rate Limiting

- **Authentication endpoints**: 10 requests per minute
- **Market data**: 60 requests per minute
- **Sync endpoint**: 120 requests per minute
- **Other endpoints**: 30 requests per minute

**Rate Limit Headers:**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699564860
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token",
    "details": {},
    "correlation_id": "abc123"
  }
}
```

**Common Error Codes:**

- `400 BAD_REQUEST`: Invalid request parameters
- `401 UNAUTHORIZED`: Missing or invalid authentication
- `403 FORBIDDEN`: Insufficient permissions
- `404 NOT_FOUND`: Resource not found
- `429 RATE_LIMIT_EXCEEDED`: Too many requests
- `500 INTERNAL_ERROR`: Server error
- `503 SERVICE_UNAVAILABLE`: Service temporarily unavailable

## Testing

### Development Server

Start the development server:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Access mobile API at: `http://localhost:8000/mobile`

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/mobile/health

# Login (get token)
curl -X POST http://localhost:8000/mobile/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "password",
    "device_id": "test_device"
  }'

# Get market snapshot (with token)
curl http://localhost:8000/mobile/market/snapshot?symbols=AAPL,GOOGL \
  -H "Authorization: Bearer <token>"

# Sync data
curl http://localhost:8000/mobile/sync \
  -H "Authorization: Bearer <token>"
```

## API Versioning

The mobile API follows semantic versioning:

- **Current Version**: 1.0.0
- **API Version Header**: `X-API-Version: 1.0.0`
- **Minimum Supported App Version**: Specified in response headers

Breaking changes will increment the major version number and be communicated via:

- API documentation updates
- In-app notifications
- Email to registered developers

## Support

For API support, issues, or feature requests:

- GitHub Issues: https://github.com/jmgreen170899-prog/ZiggyAI/issues
- Email: support@ziggyai.com
- Documentation: https://docs.ziggyai.com/mobile-api

## Changelog

### Version 1.0.0 (2024-11-10)

- Initial mobile API release
- Authentication with JWT tokens
- Market data endpoints
- Trading signals
- Portfolio management
- Alert management
- News feed
- Efficient sync endpoint
- Push notification support
