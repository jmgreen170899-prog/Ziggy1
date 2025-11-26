# ZiggyAI API Documentation

Complete API reference for the ZiggyAI trading platform.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Trading Endpoints](#trading-endpoints)
- [Market Data Endpoints](#market-data-endpoints)
- [Paper Trading Endpoints](#paper-trading-endpoints)
- [News & Sentiment Endpoints](#news--sentiment-endpoints)
- [Chat & AI Endpoints](#chat--ai-endpoints)
- [WebSocket Endpoints](#websocket-endpoints)
- [Error Handling](#error-handling)

---

## Overview

### Base URL

```
Production: https://api.ziggyai.com/v1
Development: http://localhost:8000
```

### Content Type

All requests and responses use `application/json`.

### OpenAPI Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Authentication

ZiggyAI supports optional authentication via JWT tokens or API keys.

### JWT Authentication

```http
POST /auth/login
Content-Type: application/json

{
  "username": "ziggy",
  "password": "secret"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "ziggy",
    "email": "ziggy@example.com",
    "full_name": "Ziggy Admin",
    "scopes": ["admin", "trading", "read"]
  }
}
```

### Using the Token

```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication

```http
GET /some-endpoint
X-API-Key: your-api-key
```

### Default Credentials (Development)

| Username | Password | Role |
|----------|----------|------|
| `ziggy` | `secret` | Admin |
| `demo` | `secret` | Read-only |
| `user` | `secret` | Standard user |

---

## Core Endpoints

### Health Check

#### Basic Health

```http
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "ok": true,
  "service": "ZiggyAI Backend",
  "version": "0.1.0"
}
```

#### Detailed Health

```http
GET /health/detailed
```

**Response:**

```json
{
  "status": "ok",
  "details": {
    "service": "ZiggyAI Backend",
    "version": "0.1.0",
    "total_routes": 45,
    "routes": [...],
    "has_slowapi": true
  }
}
```

#### Core Dependencies Health

```http
GET /api/core/health
```

**Response:**

```json
{
  "status": "ok",
  "details": {
    "fastapi": "ok",
    "qdrant": "ok",
    "postgres": "ok",
    "redis": "ok",
    "scheduler": "ok"
  }
}
```

---

## Trading Endpoints

### Trading Health

```http
GET /trade/health
```

**Response:**

```json
{
  "ok": true,
  "service": "trade",
  "scan": true,
  "providers": ["polygon", "yfinance"],
  "provider_mode": "live",
  "telegram": {
    "token_set": true,
    "chat_set": true,
    "getme_ok": true
  }
}
```

### Market Screener

```http
GET /trade/screener?market=nyse&notify=false
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `market` | string | `nyse` | Market to scan |
| `notify` | boolean | `false` | Send Telegram alerts |

**Response:**

```json
{
  "ran_at": 1700000000.0,
  "market": "nyse",
  "count": 5,
  "results": [
    {
      "ticker": "AAPL",
      "price": 185.50,
      "sma20": 182.30,
      "sma50": 178.50,
      "rsi14": 62.5,
      "signal": "BUY",
      "confidence": 0.75,
      "reason": "RSI momentum + SMA crossover"
    }
  ]
}
```

### Explain Signal

```http
POST /trade/explain
Content-Type: application/json

{
  "ticker": "AAPL",
  "signal": "BUY",
  "confidence": 0.75,
  "indicators": {
    "rsi14": 62.5,
    "sma20": 182.30,
    "sma50": 178.50
  },
  "price": 185.50,
  "change": 1.23
}
```

**Response:**

```json
{
  "ticker": "AAPL",
  "signal": "BUY",
  "confidence": 0.75,
  "rationale": "Signal BUY (75% confidence). Last price ~ 185.50. RSI14 at 62.5 suggests bullish momentum.",
  "bullets": [
    {
      "label": "RSI14 at 62.5",
      "impact": "positive",
      "weight": 0.625,
      "detail": "Momentum context (70/30 overbought/oversold bands)"
    }
  ],
  "indicators": {
    "rsi14": 62.5,
    "sma20": 182.30,
    "sma50": 178.50,
    "sma_spread_pct": 2.13
  },
  "risk": {
    "stopLossPct": 2.0,
    "takeProfitPct": 4.0,
    "rrr": 2.0,
    "note": "Heuristic levels"
  },
  "meta": {
    "provider": "polygon / yfinance",
    "asOf": "2024-01-15T10:30:00",
    "latencyMs": 45
  }
}
```

### OHLC Data

```http
GET /trade/ohlc?tickers=AAPL,MSFT&period_days=60
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tickers` | string | required | Comma-separated symbols |
| `period_days` | int | `60` | Historical days (1-3650) |
| `debug_source` | boolean | `false` | Include provider info |
| `batch` | boolean | `false` | Return structured batch results |

**Response:**

```json
{
  "AAPL": [
    {
      "date": "2024-01-15",
      "open": 184.50,
      "high": 186.20,
      "low": 183.80,
      "close": 185.50,
      "adj_close": 185.50,
      "volume": 45000000
    }
  ]
}
```

### Backtest

```http
POST /backtest
Content-Type: application/json

{
  "symbol": "AAPL",
  "strategy": "sma50_cross",
  "timeframe": "1Y"
}
```

**Response:**

```json
{
  "ok": true,
  "symbol": "AAPL",
  "strategy": "sma50_cross",
  "period": "1Y",
  "summary": "CAGR 12.5% | Win% 65.0% | Trades 24",
  "metrics": {
    "total_return": 0.125,
    "cagr": 0.125,
    "win_rate": 0.65,
    "trades": 24,
    "max_drawdown": -0.08,
    "sharpe": 1.45
  },
  "trades": [
    {
      "entry": "2023-02-15",
      "exit": "2023-03-20",
      "ret": 0.045
    }
  ]
}
```

### Paper Trade

```http
POST /trade/market
Content-Type: application/json

{
  "symbol": "AAPL",
  "side": "BUY",
  "qty": 10,
  "sizing": {
    "method": "atr",
    "atrMult": 1.5,
    "riskAmount": 500,
    "rMultiple": 2.0
  }
}
```

**Response:**

```json
{
  "ok": true,
  "symbol": "AAPL",
  "side": "BUY",
  "qty": 10,
  "entry": 185.50,
  "stop": 182.75,
  "target": 191.00,
  "sizing": {
    "method": "atr",
    "atr": 2.75,
    "atrMult": 1.5
  },
  "risk": {
    "stopDistance": 2.75,
    "rMultiple": 2.0
  },
  "message": "paper buy 10 AAPL @ ~185.5000 (ATR sizing)"
}
```

---

## Market Data Endpoints

### Market Overview

```http
GET /market/overview?symbols=AAPL,MSFT&period_days=30
```

**Response:**

```json
{
  "asof": 1700000000.0,
  "since_open": false,
  "symbols": {
    "AAPL": {
      "last": 185.50,
      "chg1d": 1.23,
      "chg5d": 2.45,
      "chg20d": 5.67,
      "ref": 183.25
    }
  }
}
```

### Market Breadth

```http
GET /market/breadth?period_days=260
```

**Response:**

```json
{
  "asof": 1700000000.0,
  "universe": {
    "count": 50,
    "symbols": ["AAPL", "MSFT", "..."]
  },
  "ad": {
    "adv": 35,
    "dec": 12,
    "unch": 3
  },
  "pct_above": {
    "dma50": 0.72,
    "dma200": 0.64
  },
  "nh_nl": {
    "highs": 8,
    "lows": 2
  },
  "trin": 0.95,
  "period_days": 260
}
```

### Risk Lite (Put/Call Ratio)

```http
GET /market/risk-lite
```

**Response:**

```json
{
  "cpc": {
    "ticker": "^CPC",
    "last": 0.92,
    "ma20": 0.88,
    "z20": 0.45,
    "date": "2024-01-15",
    "std20": 0.08,
    "n": 20,
    "bands": [-2, -1, 0, 1, 2]
  }
}
```

### Market Calendar

```http
GET /market/calendar?days=14
```

**Response:**

```json
{
  "asof": 1700000000.0,
  "macro": [
    {
      "code": "CPI",
      "label": "CPI",
      "date": "2024-01-17",
      "time": "08:30",
      "tz": "ET",
      "note": "Monthly CPI"
    }
  ],
  "earnings": {
    "AAPL": {
      "date": "2024-01-18",
      "time": "AMC"
    }
  }
}
```

---

## Paper Trading Endpoints

### Create Paper Run

```http
POST /api/paper/runs
Content-Type: application/json

{
  "name": "SMA50 Strategy Test",
  "description": "Testing SMA crossover strategy",
  "initial_balance": 100000,
  "max_trades_per_minute": 100,
  "config": {
    "strategy": "sma50_cross"
  }
}
```

**Response:**

```json
{
  "id": 1,
  "name": "SMA50 Strategy Test",
  "status": "ACTIVE",
  "started_at": "2024-01-15T10:00:00Z",
  "total_trades": 0,
  "total_pnl": 0.0,
  "current_balance": 100000.0,
  "win_rate": null,
  "avg_fill_latency_ms": null
}
```

### List Paper Runs

```http
GET /api/paper/runs?status=ACTIVE&limit=20
```

### Get Paper Run

```http
GET /api/paper/runs/{run_id}
```

### Stop Paper Run

```http
POST /api/paper/runs/{run_id}/stop
```

### Get Trades

```http
GET /api/paper/runs/{run_id}/trades?status=FILLED&limit=100
```

**Response:**

```json
[
  {
    "id": 1,
    "trade_id": "trade_123456",
    "ticker": "AAPL",
    "direction": "BUY",
    "quantity": 10.0,
    "theory_name": "sma50_cross",
    "status": "FILLED",
    "signal_time": "2024-01-15T10:30:00Z",
    "fill_price": 185.50,
    "realized_pnl": 25.50
  }
]
```

### Get Run Statistics

```http
GET /api/paper/runs/{run_id}/stats
```

**Response:**

```json
{
  "run_id": 1,
  "status": "ACTIVE",
  "uptime_minutes": 120.5,
  "total_trades": 45,
  "trades_last_hour": 12,
  "current_balance": 102500.50,
  "total_pnl": 2500.50,
  "win_rate": 0.65,
  "error_rate": 0.02,
  "avg_fill_latency_ms": 45.2,
  "theory_distribution": {
    "sma50_cross": 30,
    "rsi_mean_reversion": 15
  }
}
```

### Paper Health

```http
GET /api/paper/health
```

**Response:**

```json
{
  "status": "healthy",
  "paper_enabled": true,
  "strict_isolation": true,
  "broker": "paper",
  "signals_5m": 25,
  "orders_5m": 25,
  "fills_5m": 24,
  "recent_trades_5m": 24,
  "total_trades_today": 450,
  "last_trade_at": "2024-01-15T12:30:00Z",
  "open_trades": 5,
  "queue_depth": 0,
  "learner_batches_5m": 3,
  "db_ok": true,
  "gateway_running": true,
  "timestamp": "2024-01-15T12:35:00Z"
}
```

### Emergency Stop

```http
POST /api/paper/emergency/stop_all
```

**Response:**

```json
{
  "status": "emergency_stop_complete",
  "runs_stopped": 3,
  "timestamp": "2024-01-15T12:35:00Z"
}
```

---

## News & Sentiment Endpoints

### News Headlines

```http
GET /news/headlines?symbols=AAPL,MSFT&limit=30
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | string | - | Single ticker filter |
| `symbols` | string | - | Comma-separated tickers |
| `q` | string | - | Keyword filter |
| `sources` | string | - | Source IDs or URLs |
| `lookback_days` | int | `3` | Days to look back |
| `limit` | int | `30` | Max results |

**Response:**

```json
{
  "asof": 1700000000.0,
  "count": 10,
  "items": [
    {
      "id": "https://...",
      "source": "Reuters Markets",
      "site": "reuters.com",
      "title": "Apple Reports Strong Q4 Earnings",
      "url": "https://...",
      "published": "2024-01-15T10:00:00Z",
      "date": "2024-01-15T10:00:00Z",
      "summary": "Apple Inc reported...",
      "tickers": ["AAPL"],
      "symbols": ["AAPL"],
      "favicon": "https://reuters.com/favicon.ico",
      "score": 0.45,
      "label": "positive"
    }
  ]
}
```

### News Sentiment

```http
GET /news/sentiment?ticker=AAPL&lookback_days=3
```

**Response:**

```json
{
  "ticker": "AAPL",
  "score": 0.35,
  "label": "positive",
  "confidence": 0.72,
  "sample_count": 15,
  "updated_at": "2024-01-15T12:00:00Z",
  "samples": [
    {
      "source": "Reuters",
      "title": "Apple Reports Strong Earnings",
      "url": "https://...",
      "published": "2024-01-15T08:00:00Z",
      "score": 0.65,
      "label": "positive"
    }
  ]
}
```

### News Sources

```http
GET /news/sources
```

**Response:**

```json
{
  "asof": 1700000000.0,
  "sources": [
    {
      "id": "reuters-markets",
      "label": "Reuters Markets",
      "url": "https://www.reuters.com/markets/rss"
    }
  ]
}
```

### SEC Filings

```http
GET /news/filings?symbols=AAPL&forms=10-K,10-Q,8-K&limit=30
```

---

## Chat & AI Endpoints

### Chat Completion

```http
POST /chat/complete
Content-Type: application/json

{
  "messages": [
    {"role": "system", "content": "You are a helpful trading assistant."},
    {"role": "user", "content": "What's the outlook for AAPL?"}
  ],
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

**Response:**

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on recent analysis..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

### Chat Health

```http
GET /chat/health
```

**Response:**

```json
{
  "provider": "openai",
  "base": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "ok": true,
  "status_code": 200
}
```

### RAG Query

```http
POST /api/query
Content-Type: application/json

{
  "query": "What is mean reversion trading?",
  "top_k": 5
}
```

**Response:**

```json
{
  "answer": "Mean reversion is a trading strategy...",
  "citations": [
    {
      "url": "https://...",
      "title": "Mean Reversion Strategies",
      "score": 0.92,
      "snippet": "..."
    }
  ],
  "contexts": ["..."]
}
```

### AI Agent

```http
POST /api/agent
Content-Type: application/json

{
  "query": "Research the latest news on AAPL and summarize",
  "max_steps": 5,
  "approvals": false
}
```

---

## WebSocket Endpoints

### Market Data Stream

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/market');

// Subscribe to symbols
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['AAPL', 'MSFT']
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Message Format:**

```json
{
  "type": "quote",
  "symbol": "AAPL",
  "price": 185.50,
  "change": 1.23,
  "volume": 45000000,
  "timestamp": 1700000000
}
```

### News Stream

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/news');
```

---

## Error Handling

### Error Response Format

All errors follow a standardized format:

```json
{
  "detail": "Human-readable error message",
  "code": "error_code",
  "meta": {
    "additional": "context"
  }
}
```

### Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `bad_request` | Invalid request parameters |
| 401 | `unauthorized` | Authentication required |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 422 | `validation_error` | Request validation failed |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_server_error` | Server error |
| 501 | `not_implemented` | Feature not available |
| 503 | `service_unavailable` | Service temporarily down |

### Rate Limiting

When rate limited, you'll receive:

```json
{
  "detail": "Rate limit exceeded",
  "code": "rate_limit_exceeded",
  "meta": {}
}
```

**Headers:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000060
```

---

## SDK Examples

### Python

```python
import httpx

BASE_URL = "http://localhost:8000"

# Health check
response = httpx.get(f"{BASE_URL}/health")
print(response.json())

# Get screener results
response = httpx.get(f"{BASE_URL}/trade/screener")
signals = response.json()

for result in signals["results"]:
    if result["signal"] == "BUY":
        print(f"{result['ticker']}: {result['confidence']*100:.0f}% confidence")
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000';

// Health check
const health = await fetch(`${BASE_URL}/health`).then(r => r.json());

// Get screener results
const signals = await fetch(`${BASE_URL}/trade/screener`).then(r => r.json());

signals.results
  .filter(r => r.signal === 'BUY')
  .forEach(r => console.log(`${r.ticker}: ${r.confidence * 100}% confidence`));
```

---

## Additional Resources

- [OpenAPI Specification](http://localhost:8000/openapi.json)
- [Architecture Documentation](architecture.md)
- [Setup Guide](SetupGuide.md)
