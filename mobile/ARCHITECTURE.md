# ZiggyAI Mobile Architecture

## System Overview

This document provides a visual guide to understanding the complete ZiggyAI mobile application architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     USER'S ANDROID PHONE                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │                                                       │    │
│  │              ZiggyAI Android App                      │    │
│  │                                                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  Dashboard  │  │   Market    │  │   Signals   │  │    │
│  │  │             │  │   Quotes    │  │   & News    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │                                                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  Portfolio  │  │   Alerts    │  │  Settings   │  │    │
│  │  │  Positions  │  │   & Notif   │  │             │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │                                                       │    │
│  │          ▼ Kotlin + Jetpack Compose ▼                │    │
│  │                                                       │    │
│  │  ┌───────────────────────────────────────────────┐   │    │
│  │  │          ViewModel Layer (MVVM)               │   │    │
│  │  │  • DashboardViewModel                         │   │    │
│  │  │  • MarketViewModel                            │   │    │
│  │  │  • SignalsViewModel                           │   │    │
│  │  │  • PortfolioViewModel                         │   │    │
│  │  └───────────────────────────────────────────────┘   │    │
│  │                       ▼                               │    │
│  │  ┌───────────────────────────────────────────────┐   │    │
│  │  │      Repository Layer (Data Management)       │   │    │
│  │  │  • MarketRepository                           │   │    │
│  │  │  • SignalRepository                           │   │    │
│  │  │  • PortfolioRepository                        │   │    │
│  │  │  • AuthRepository                             │   │    │
│  │  └───────────────────────────────────────────────┘   │    │
│  │              │                    │                   │    │
│  │              ▼                    ▼                   │    │
│  │     ┌──────────────┐    ┌──────────────┐            │    │
│  │     │  Room DB     │    │  API Client  │            │    │
│  │     │  (Cache)     │    │  (Retrofit)  │            │    │
│  │     └──────────────┘    └──────┬───────┘            │    │
│  │                                 │                    │    │
│  │  ┌───────────────────────────────────────────────┐   │    │
│  │  │         Background Services                   │   │    │
│  │  │  • WorkManager (periodic sync)                │   │    │
│  │  │  • FCM (push notifications)                   │   │    │
│  │  └───────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  └───────────────────────────┬───────────────────────────┘    │
│                              │                                │
└──────────────────────────────┼────────────────────────────────┘
                               │
                               │ HTTPS + JWT Authentication
                               │ (Secure encrypted connection)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        CLOUD SERVER                             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │                                                       │    │
│  │            Mobile API Layer (FastAPI)                 │    │
│  │               ✅ COMPLETE & TESTED                    │    │
│  │                                                       │    │
│  │  Authentication Endpoints:                            │    │
│  │  • POST /mobile/auth/login                            │    │
│  │  • POST /mobile/auth/refresh                          │    │
│  │  • POST /mobile/auth/logout                           │    │
│  │                                                       │    │
│  │  Device Management:                                   │    │
│  │  • POST /mobile/device/register                       │    │
│  │  • DELETE /mobile/device/unregister                   │    │
│  │                                                       │    │
│  │  Market Data:                                         │    │
│  │  • GET /mobile/market/snapshot?symbols=AAPL,GOOGL     │    │
│  │  • GET /mobile/market/quote/AAPL                      │    │
│  │                                                       │    │
│  │  Trading:                                             │    │
│  │  • GET /mobile/signals                                │    │
│  │  • GET /mobile/portfolio                              │    │
│  │  • GET /mobile/alerts                                 │    │
│  │  • POST /mobile/alerts                                │    │
│  │  • DELETE /mobile/alerts/{id}                         │    │
│  │                                                       │    │
│  │  News & Content:                                      │    │
│  │  • GET /mobile/news                                   │    │
│  │                                                       │    │
│  │  Efficient Sync (Recommended):                        │    │
│  │  • GET /mobile/sync?include=all                       │    │
│  │    (Returns everything in one call!)                  │    │
│  │                                                       │    │
│  │  Health Check:                                        │    │
│  │  • GET /mobile/health                                 │    │
│  │                                                       │    │
│  └───────────────────────────┬───────────────────────────┘    │
│                              │                                │
│                              ▼                                │
│  ┌───────────────────────────────────────────────────────┐    │
│  │                                                       │    │
│  │         ZiggyAI Backend Services                      │    │
│  │         (Existing Trading Platform)                   │    │
│  │                                                       │    │
│  │  • Market Data Providers (Polygon, Alpaca, etc.)      │    │
│  │  • AI Trading Signals Engine                          │    │
│  │  • Portfolio Management System                        │    │
│  │  • News Aggregation Services                          │    │
│  │  • Real-time WebSocket Streams                        │    │
│  │                                                       │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │              Supporting Services                      │    │
│  │  • PostgreSQL (User data, portfolios)                 │    │
│  │  • Redis (Caching, session management)                │    │
│  │  • Firebase Cloud Messaging (Push notifications)      │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: User Logs In

```
1. User enters credentials on Android
   └─> AuthViewModel.login(username, password)
       └─> AuthRepository.login()
           └─> API Client: POST /mobile/auth/login
               {
                 username: "user@example.com",
                 password: "encrypted_password",
                 device_id: "unique_device_id"
               }
               └─> Mobile API validates credentials
                   └─> Returns JWT tokens
                       {
                         access_token: "eyJhbG...",
                         refresh_token: "eyJhbG...",
                         expires_in: 3600
                       }
                       └─> Android stores tokens securely
                           └─> User sees Dashboard

2. Android registers for push notifications
   └─> DeviceManager.register(fcm_token)
       └─> POST /mobile/device/register
           └─> Server associates FCM token with user
               └─> User will receive alert notifications
```

### Example 2: Viewing Market Data

```
1. User opens Market screen
   └─> MarketViewModel.loadWatchlist()
       └─> Check Room DB for cached quotes
           ├─> Found cached data (< 60 seconds old)
           │   └─> Display immediately (fast!)
           │
           └─> Fetch fresh data in background
               └─> API: GET /mobile/market/snapshot?symbols=AAPL,GOOGL,MSFT
                   └─> Mobile API fetches live prices
                       └─> Returns compact data
                           {
                             quotes: [
                               {symbol: "AAPL", price: 155.50, change: 1.50, ...},
                               {symbol: "GOOGL", price: 140.25, change: -0.75, ...},
                               {symbol: "MSFT", price: 380.00, change: 2.30, ...}
                             ],
                             cache_ttl: 60
                           }
                           └─> Update Room DB cache
                               └─> Update UI with fresh data
```

### Example 3: Efficient Background Sync

```
1. WorkManager triggers periodic sync (every 15 minutes)
   └─> SyncWorker.doWork()
       └─> Check last sync timestamp (e.g., 15 minutes ago)
           └─> API: GET /mobile/sync?since=1699564800&include=all
               └─> Mobile API returns ONLY changes since last sync
                   {
                     quotes: [updated quotes],
                     signals: [new signals],
                     alerts: [triggered alerts],
                     news: [new articles],
                     portfolio: {updated portfolio},
                     sync_token: "1699565400"
                   }
                   └─> Update all local databases
                       ├─> Room DB updated
                       ├─> No duplicate data
                       └─> Minimal battery usage!

2. If alert triggered:
   └─> FCM sends push notification
       └─> User sees: "AAPL reached $160!"
           └─> User taps notification
               └─> App opens to Alert details
```

### Example 4: Creating a Price Alert

```
1. User creates alert: "AAPL above $160"
   └─> AlertViewModel.createAlert("AAPL", "above", 160.0)
       └─> AlertRepository.createAlert()
           └─> API: POST /mobile/alerts
               {
                 symbol: "AAPL",
                 condition: "above",
                 price: 160.0
               }
               └─> Mobile API creates alert
                   └─> Returns confirmation
                       {
                         id: "alert_123",
                         status: "created",
                         push_enabled: true
                       }
                       └─> Alert stored in Room DB
                           └─> User sees confirmation

2. When price triggers:
   └─> Backend monitors price
       └─> Price reaches $160.50
           └─> Alert triggered!
               └─> FCM notification sent
                   └─> Push appears on phone
                       └─> User informed immediately!
```

## Offline-First Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              ONLINE MODE (Internet Available)           │
│                                                         │
│  User Action                                            │
│       ▼                                                 │
│  ViewModel                                              │
│       ▼                                                 │
│  Repository ──────────────┐                             │
│       │                   │                             │
│       ├─────────►  API    │ (Fetch fresh data)          │
│       │              │    │                             │
│       │              ▼    │                             │
│       │           Server  │                             │
│       │              │    │                             │
│       │              ▼    │                             │
│       └────────► Room DB  │ (Cache for offline)         │
│                     │     │                             │
│                     ▼     │                             │
│                    UI     │                             │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
                            │ Network Lost
                            ▼
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              OFFLINE MODE (No Internet)                 │
│                                                         │
│  User Action                                            │
│       ▼                                                 │
│  ViewModel                                              │
│       ▼                                                 │
│  Repository                                             │
│       │                                                 │
│       └─────────► Room DB  (Use cached data)            │
│                     │                                   │
│                     ▼                                   │
│                    UI     (Show with "stale" indicator) │
│                                                         │
│  User sees: "Last updated 5 minutes ago"                │
│                                                         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Network Restored
                            ▼
                    Auto-sync triggered
                    Fresh data fetched
                    UI updated
```

## Mobile API Efficiency: Sync vs Individual Calls

### ❌ Inefficient Approach (Multiple Calls)
```
App makes 5 separate API calls:
1. GET /mobile/market/snapshot?symbols=...    (200ms)
2. GET /mobile/signals                        (150ms)
3. GET /mobile/portfolio                      (180ms)
4. GET /mobile/alerts                         (120ms)
5. GET /mobile/news                           (200ms)

Total time: 850ms
Battery drain: HIGH (5 network calls)
Data usage: 5 separate HTTP overheads
```

### ✅ Efficient Approach (Single Sync Call)
```
App makes 1 sync call:
1. GET /mobile/sync?include=all               (300ms)

Returns everything in one response:
- Market quotes
- Trading signals  
- Portfolio data
- Price alerts
- News items

Total time: 300ms (65% faster!)
Battery drain: LOW (1 network call)
Data usage: Minimal (1 HTTP overhead)

RESULT: 90% fewer API calls, better battery life!
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Android App                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Secure Token Storage                    │   │
│  │  (Android Keystore / EncryptedSharedPreferences)│   │
│  │                                                 │   │
│  │  • Access Token: eyJhbGciOiJI... (encrypted)   │   │
│  │  • Refresh Token: eyJhbGciOiJI... (encrypted)  │   │
│  │  • Device ID: unique_id (encrypted)            │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                             │
│                           ▼                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │         API Client (Retrofit + OkHttp)          │   │
│  │                                                 │   │
│  │  • Adds Authorization header to all requests   │   │
│  │  • Certificate pinning (prevents MITM)         │   │
│  │  • Automatic token refresh when expired        │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ HTTPS (TLS 1.3)
                            │ Authorization: Bearer <token>
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Cloud Server                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Rate Limiting                      │   │
│  │  • 60 requests/minute per user                  │   │
│  │  • Blocks excessive requests                    │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                             │
│                           ▼                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │         JWT Token Validation                    │   │
│  │  • Verify signature                             │   │
│  │  • Check expiration                             │   │
│  │  • Extract user identity                        │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                             │
│                           ▼                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Mobile API Endpoints                    │   │
│  │  • Process authenticated request                │   │
│  │  • Return user-specific data                    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### Android Application
```
┌────────────────────────────────────────┐
│           Presentation Layer           │
│  • Jetpack Compose (UI)                │
│  • Material Design 3                   │
│  • Navigation Compose                  │
│  • Coil (image loading)                │
└────────────────────────────────────────┘
              ▼
┌────────────────────────────────────────┐
│         Business Logic Layer           │
│  • ViewModel (state management)        │
│  • Kotlin Coroutines (async)           │
│  • Flow (reactive streams)             │
└────────────────────────────────────────┘
              ▼
┌────────────────────────────────────────┐
│            Data Layer                  │
│  • Repository Pattern                  │
│  • Room Database (local)               │
│  • Retrofit (networking)               │
│  • Hilt (dependency injection)         │
└────────────────────────────────────────┘
              ▼
┌────────────────────────────────────────┐
│        Infrastructure Layer            │
│  • WorkManager (background jobs)       │
│  • Firebase (push notifications)       │
│  • Encrypted storage (security)        │
└────────────────────────────────────────┘
```

### Backend Services
```
┌────────────────────────────────────────┐
│             Mobile API                 │
│  • FastAPI (Python framework)          │
│  • Pydantic (validation)               │
│  • JWT (authentication)                │
└────────────────────────────────────────┘
              ▼
┌────────────────────────────────────────┐
│          Backend Services              │
│  • Market Data (Polygon, Alpaca)       │
│  • AI Signals (Custom ML models)       │
│  • Portfolio Management                │
└────────────────────────────────────────┘
              ▼
┌────────────────────────────────────────┐
│            Data Storage                │
│  • PostgreSQL (persistent data)        │
│  • Redis (caching)                     │
│  • S3 (file storage)                   │
└────────────────────────────────────────┘
```

## Deployment Architecture

```
                  ┌─────────────────┐
                  │  Google Play    │
                  │     Store       │
                  └────────┬────────┘
                           │
                           │ Downloads APK/AAB
                           ▼
                  ┌─────────────────┐
                  │  User's Phone   │
                  │  Android App    │
                  └────────┬────────┘
                           │
                           │ HTTPS Requests
                           ▼
                  ┌─────────────────┐
                  │   Load Balancer │
                  │   (Nginx/ALB)   │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ API      │   │ API      │   │ API      │
    │ Server 1 │   │ Server 2 │   │ Server 3 │
    └─────┬────┘   └─────┬────┘   └─────┬────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │PostgreSQL│  │  Redis   │  │ Firebase │
    │ (Master) │  │  Cache   │  │   FCM    │
    └──────────┘  └──────────┘  └──────────┘
```

## Summary

This architecture provides:

✅ **Scalable** - Can handle thousands of concurrent users
✅ **Efficient** - Minimizes battery drain and data usage
✅ **Offline-First** - Works without internet connection
✅ **Secure** - JWT authentication, encrypted storage
✅ **Fast** - Local caching, efficient sync
✅ **Reliable** - Error handling, retry logic
✅ **Maintainable** - Clean separation of concerns

The mobile API layer is complete and ready for integration with real backend services. The Android app can be built following the documented architecture and patterns.
