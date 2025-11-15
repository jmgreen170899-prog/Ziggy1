# ENDPOINTS_AUDIT.md - Backend Route ↔ Frontend Caller Mapping

## Summary

This document maps all backend API routes to their frontend callers, ensuring no endpoint is orphaned during cleanup. Routes with no callers may be candidates for removal, while heavily used routes must be preserved.

---

## 🔍 Route Usage Analysis

### ✅ Actively Used Routes

#### Core Health & Discovery

| Route     | Method | Frontend Callers                                                             | Usage Pattern                          |
| --------- | ------ | ---------------------------------------------------------------------------- | -------------------------------------- |
| `/health` | GET    | `App.jsx`, `main.working.jsx`, `main.full.jsx`, `ziggyAPI.js`, API discovery | Critical - app startup & health checks |
| `/`       | GET    | Root endpoint                                                                | Basic connectivity test                |

#### Trading & Market Data (Heavy Usage)

| Route                      | Method | Frontend Callers                     | Usage Pattern                |
| -------------------------- | ------ | ------------------------------------ | ---------------------------- |
| `/trade/health`            | GET    | `App.jsx`                            | Trading service health check |
| `/trade/screener`          | GET    | Market hooks, `api.js` via `r.get()` | Primary market data source   |
| `/trade/ohlc`              | GET    | Chart components via `api.get()`     | OHLC chart data              |
| `/trade/portfolio`         | GET    | `TradingTab.jsx`                     | Portfolio overview           |
| `/trade/positions`         | GET    | `TradingTab.jsx`                     | Position data                |
| `/trade/orders`            | GET    | `TradingTab.jsx`                     | Order management             |
| `/trade/market`            | POST   | `TradingTab.jsx`                     | Trade execution              |
| `/trade/orders/{order_id}` | DELETE | `TradingTab.jsx`                     | Cancel orders                |

#### Market Overview & Analysis

| Route               | Method | Frontend Callers             | Usage Pattern             |
| ------------------- | ------ | ---------------------------- | ------------------------- |
| `/market/overview`  | GET    | `ziggyAPI.js`, market hooks  | Market overview data      |
| `/market/breadth`   | GET    | `ziggyAPI.js`, market hooks  | Market breadth indicators |
| `/market/risk-lite` | GET    | Market hooks via `api.get()` | Risk assessment (primary) |
| `/market-risk-lite` | GET    | Fallback/alias route         | Risk assessment (backup)  |
| `/market/calendar`  | GET    | Market hooks                 | Calendar events           |

#### News & Information

| Route                  | Method | Frontend Callers               | Usage Pattern    |
| ---------------------- | ------ | ------------------------------ | ---------------- |
| `/news/headlines`      | GET    | `RightRail.jsx`, `ziggyAPI.js` | News feed        |
| `/news/filings/recent` | GET    | `RightRail.jsx`                | SEC filings      |
| `/news/sentiment`      | GET    | Various components             | Market sentiment |

#### Signals & Analysis

| Route                      | Method | Frontend Callers | Usage Pattern          |
| -------------------------- | ------ | ---------------- | ---------------------- |
| `/signals/signal/{symbol}` | GET    | `ziggyAPI.js`    | Individual signal data |
| `/signals/regime`          | GET    | `ziggyAPI.js`    | Market regime          |

#### Cryptocurrency

| Route            | Method | Frontend Callers | Usage Pattern      |
| ---------------- | ------ | ---------------- | ------------------ |
| `/crypto/quotes` | GET    | `ziggyAPI.js`    | Crypto market data |

#### Explanation System

| Route                        | Method | Frontend Callers                 | Usage Pattern      |
| ---------------------------- | ------ | -------------------------------- | ------------------ |
| `/explain/events`            | GET    | `InnerThoughtsTab.jsx`, `api.js` | Event listing      |
| `/explain/events/{event_id}` | GET    | `api.js` helper function         | Event details      |
| `/explain/stats/summary`     | GET    | `InnerThoughtsTab.jsx`, `api.js` | Statistics summary |
| `/explain/status`            | GET    | `api.js` helper                  | Service status     |
| `/explain/test/signal`       | POST   | `api.js` helper                  | Signal testing     |
| `/explain/test/regime`       | POST   | `api.js` helper                  | Regime testing     |

#### Scanning & Notifications

| Route                | Method | Frontend Callers | Usage Pattern            |
| -------------------- | ------ | ---------------- | ------------------------ |
| `/trade/scan/status` | GET    | Market hooks     | Scan status check        |
| `/trade/scan/enable` | POST   | Market hooks     | Enable/disable scanning  |
| `/trade/notify/test` | POST   | Market hooks     | Test notifications       |
| `/trade/notify/diag` | GET    | Market hooks     | Notification diagnostics |

### ⚠️ Routes with Limited/Unknown Frontend Usage

#### Chat System

| Route          | Method | Notes                           |
| -------------- | ------ | ------------------------------- |
| `/complete`    | POST   | Chat completion - usage unclear |
| `/chat/health` | GET    | Chat service health             |
| `/chat/config` | GET    | Chat configuration              |

#### Advanced Trading Features

| Route                 | Method | Notes                     |
| --------------------- | ------ | ------------------------- |
| `/trade/explain`      | POST   | Trade explanation service |
| `/trade/notify`       | POST   | General notifications     |
| `/trade/notify/probe` | GET    | Notification probe        |
| `/trade/execute`      | POST   | Advanced execution        |
| `/trade/mode/{mode}`  | POST   | Trading mode changes      |

#### Signal Generation & Analysis

| Route                          | Method  | Notes                    |
| ------------------------------ | ------- | ------------------------ |
| `/features/{ticker}`           | GET     | Signal features          |
| `/features/bulk`               | POST    | Bulk signal processing   |
| `/regime`                      | GET     | Current market regime    |
| `/regime/history`              | GET     | Regime history           |
| `/signal/{ticker}`             | GET     | Individual signals       |
| `/signals/watchlist`           | POST    | Watchlist signals        |
| `/trade/plan`                  | POST    | Trading plan generation  |
| `/status`                      | GET     | General status           |
| `/config`                      | GET/PUT | Configuration management |
| `/execute/trade`               | POST    | Trade execution          |
| `/execute/status/{request_id}` | GET     | Execution tracking       |
| `/execute/history`             | GET     | Execution history        |
| `/execute/stats`               | GET     | Execution statistics     |

#### Backtesting

| Route                         | Method | Notes                |
| ----------------------------- | ------ | -------------------- |
| `/backtest/quick/{ticker}`    | GET    | Quick backtests      |
| `/backtest/analysis/{ticker}` | GET    | Backtest analysis    |
| `/trading/backtest`           | POST   | Trading backtests    |
| `/backtest`                   | POST   | General backtesting  |
| `/strategy/backtest`          | POST   | Strategy backtesting |

#### Market Calendar & Economics

| Route               | Method | Notes               |
| ------------------- | ------ | ------------------- |
| `/calendar`         | GET    | Market calendar     |
| `/holidays`         | GET    | Market holidays     |
| `/earnings`         | GET    | Earnings calendar   |
| `/economic`         | GET    | Economic events     |
| `/schedule`         | GET    | Market schedule     |
| `/indicators`       | GET    | Economic indicators |
| `/fred/{series_id}` | GET    | FRED economic data  |

#### News (Extended Features)

| Route            | Method | Notes               |
| ---------------- | ------ | ------------------- |
| `/news/sources`  | GET    | News sources        |
| `/news/filings`  | GET    | General SEC filings |
| `/news/headwind` | GET    | Market headwinds    |
| `/news/ping`     | GET    | News service ping   |

#### Crypto (Extended)

| Route          | Method | Notes            |
| -------------- | ------ | ---------------- |
| `/crypto/ohlc` | GET    | Crypto OHLC data |

#### Alert System

| Route                        | Method | Notes                   |
| ---------------------------- | ------ | ----------------------- |
| `/alerts/status`             | GET    | Alert service status    |
| `/alerts/start`              | POST   | Start alert service     |
| `/alerts/stop`               | POST   | Stop alert service      |
| `/alerts/ping/test`          | POST   | Test alert ping         |
| `/alerts/create`             | POST   | Create alerts           |
| `/alerts/sma50`              | POST   | SMA50 alerts            |
| `/alerts/moving-average/50`  | POST   | Moving average alerts   |
| `/alerts/list`               | GET    | List alerts             |
| `/alerts/production/status`  | GET    | Production alert status |
| `/alerts/history`            | GET    | Alert history           |
| `/alerts/{alert_id}`         | DELETE | Delete alerts           |
| `/alerts/{alert_id}/enable`  | PUT    | Enable alerts           |
| `/alerts/{alert_id}/disable` | PUT    | Disable alerts          |

#### Learning System

| Route                          | Method  | Notes                  |
| ------------------------------ | ------- | ---------------------- |
| `/learning/status`             | GET     | Learning system status |
| `/learning/data/summary`       | GET     | Learning data          |
| `/learning/rules/current`      | GET     | Current rules          |
| `/learning/rules/history`      | GET     | Rules history          |
| `/learning/run`                | POST    | Run learning           |
| `/learning/results/latest`     | GET     | Latest results         |
| `/learning/results/history`    | GET     | Results history        |
| `/learning/evaluate/current`   | GET     | Current evaluation     |
| `/learning/gates`              | GET/PUT | Learning gates         |
| `/learning/calibration/status` | GET     | Calibration status     |
| `/learning/calibration/build`  | POST    | Build calibration      |
| `/learning/health`             | GET     | Learning health        |

#### Integration System

| Route                 | Method | Notes              |
| --------------------- | ------ | ------------------ |
| `/integration/health` | GET    | Integration health |
| `/decision`           | POST   | Decision endpoints |
| `/enhance`            | POST   | Enhancement        |
| `/context/market`     | GET    | Market context     |
| `/rules/active`       | GET    | Active rules       |
| `/calibration/apply`  | POST   | Apply calibration  |
| `/outcome/update`     | POST   | Update outcomes    |
| `/integration/status` | GET    | Integration status |
| `/test/decision`      | POST   | Test decisions     |

#### Web Browsing

| Route                | Method | Notes        |
| -------------------- | ------ | ------------ |
| `/web/browse/search` | GET    | Web search   |
| `/web/browse`        | GET    | Web browsing |

#### Debug Endpoints (Dev Only)

| Route                    | Method | Notes              |
| ------------------------ | ------ | ------------------ |
| `/__debug/routes`        | GET    | Route debugging    |
| `/__debug/env/providers` | GET    | Provider debugging |
| `/__debug/env/telegram`  | GET    | Telegram debugging |

#### Telegram Integration

| Route                | Method | Notes            |
| -------------------- | ------ | ---------------- |
| `/telegram/callback` | POST   | Webhook callback |

---

## 📊 Usage Statistics Summary

### High-Traffic Routes (Called Frequently)

- `/health` - App startup, periodic health checks
- `/trade/screener` - Market data refresh
- `/trade/ohlc` - Chart data updates
- `/market/overview` - Dashboard updates
- `/market/breadth` - Market analysis
- `/market/risk-lite` - Risk monitoring
- `/news/headlines` - News feed updates

### Medium-Traffic Routes (Feature-Specific)

- `/trade/portfolio`, `/trade/positions`, `/trade/orders` - Trading interface
- `/explain/events`, `/explain/stats/summary` - Explanation interface
- `/trade/scan/status`, `/trade/scan/enable` - Scanning features
- `/news/filings/recent` - SEC filings

### Low-Traffic Routes (Advanced Features)

- Most learning system routes
- Advanced trading routes (explain, execute, modes)
- Backtesting routes
- Alert system routes
- Integration system routes

### Unknown/Unused Routes (Candidates for Investigation)

- Chat system routes (may be unused)
- Web browsing routes
- Some signal processing routes
- Calendar system routes (partial usage)

---

## 🎯 Frontend API Client Architecture

### Primary API Clients

1. **`api()` function** (`services/api.js`) - Main client with auto-discovery
2. **`ziggyAPI` class** (`services/ziggyAPI.js`) - Legacy wrapper with specific methods
3. **Market hooks** - Custom hooks for market data
4. **Direct fetch calls** - Simple health checks and tests

### API Call Patterns

- **Auto-discovery**: Frontend discovers backend URL dynamically
- **Retry logic**: Built-in retry with exponential backoff
- **Caching**: API base URL cached in localStorage
- **Error handling**: Comprehensive error handling with user feedback

### Critical Dependencies

- **Backend URL discovery** - Must not break auto-discovery logic
- **Response schemas** - Frontend expects specific JSON structures
- **Error response format** - Error handling depends on consistent format
- **CORS configuration** - Cross-origin requests must be properly configured

---

## ⚡ Performance Considerations

### High-Frequency Endpoints

- `/trade/screener` - Called every few seconds during active trading
- `/market/risk-lite` - Frequent risk updates
- `/trade/scan/status` - Periodic scan status checks

### Bulk Data Endpoints

- `/trade/ohlc` - Returns large datasets for charting
- `/market/overview` - Multiple symbol data
- `/news/headlines` - News article lists

### Real-time Features

- `/explain/stream` - Server-sent events for explanations
- WebSocket connections (if any) for live data

---

## 🔧 Cleanup Recommendations

### Safe to Remove (If Confirmed Unused)

- Unused chat routes (if chat system not deployed)
- Unused calendar routes (if calendar not implemented in frontend)
- Unused learning routes (if learning system not active)
- Debug routes in production

### Consolidation Opportunities

- `/market/risk-lite` and `/market-risk-lite` (keep primary, alias secondary)
- Multiple backtest routes (consolidate similar functionality)
- Duplicate health check routes

### Critical to Preserve

- All actively used routes listed in "✅ Actively Used Routes" section
- Health check endpoints (critical for discovery)
- Primary trading routes (core functionality)
- Market data routes (dashboard depends on these)

---

_This endpoint audit was generated during cleanup analysis on 2025-10-18_
