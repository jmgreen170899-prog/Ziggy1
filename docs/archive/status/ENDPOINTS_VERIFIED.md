# ZiggyAI Backend Endpoints - Verification Report

**Date:** 2025-11-12  
**Status:** ✅ All routes verified and fixed

## Summary

This document provides a comprehensive overview of all ZiggyAI backend API endpoints after verification and fixes.

### Issues Found and Fixed

**40 routing issues were identified and fixed** where route decorators included prefixes that were already added in `main.py`, causing duplicate prefixes in the final endpoint paths.

#### Files Fixed:

1. **routes_alerts.py** - 13 endpoints
2. **routes_crypto.py** - 2 endpoints
3. **routes_learning.py** - 13 endpoints
4. **routes_market.py** - 4 endpoints
5. **routes_news.py** - 7 endpoints
6. **routes_trading.py** - 1 endpoint

#### Examples of Fixes:

- `/alerts/alerts/status` → `/alerts/status` ✓
- `/news/news/sources` → `/news/sources` ✓
- `/market/market/overview` → `/market/overview` ✓
- `/crypto/crypto/quotes` → `/crypto/quotes` ✓
- `/learning/learning/status` → `/learning/status` ✓

## Current Endpoint Structure

### Total Endpoints: 170

The backend now has **170 properly configured endpoints** across **15 route groups**.

### Route Groups

#### 1. `/alerts` (13 endpoints)

Manages alerts and monitoring for market conditions.

**Endpoints:**

- `POST /alerts/create` - Create a new alert
- `GET /alerts/history` - Get alert trigger history
- `GET /alerts/list` - List all alerts
- `POST /alerts/moving-average/50` - Create MA50 alert
- `POST /alerts/ping/test` - Test alert system
- `GET /alerts/production/status` - Check production alert status
- `POST /alerts/sma50` - Create SMA50 alert
- `POST /alerts/start` - Start alert scanning
- `GET /alerts/status` - Get alert system status
- `POST /alerts/stop` - Stop alert scanning
- `DELETE /alerts/{alert_id}` - Delete specific alert
- `PUT /alerts/{alert_id}/disable` - Disable specific alert
- `PUT /alerts/{alert_id}/enable` - Enable specific alert

#### 2. `/api` (19 endpoints)

Core API functionality including RAG, browsing, and task management.

**Key Endpoints:**

- `GET /api/core/health` - Core system health check
- `POST /api/query` - RAG query endpoint
- `POST /api/agent` - Agent interaction
- `GET /api/browse/search` - Web search functionality
- `POST /api/ingest/web` - Ingest web content
- `POST /api/ingest/pdf` - Ingest PDF documents
- `GET /api/tasks` - List scheduled tasks
- `GET /api/performance/metrics` - Performance metrics

#### 3. `/chat` (3 endpoints)

Chat and completion endpoints.

**Endpoints:**

- `POST /chat/complete` - Chat completion
- `GET /chat/config` - Chat configuration
- `GET /chat/health` - Chat system health

#### 4. `/cognitive` (7 endpoints)

Cognitive system for decision enhancement and meta-learning.

**Endpoints:**

- `POST /cognitive/enhance-decision` - Enhance trading decisions
- `POST /cognitive/record-outcome` - Record decision outcomes
- `GET /cognitive/health` - Cognitive system health
- `GET /cognitive/status` - Current cognitive status
- `GET /cognitive/episodic-memory/stats` - Memory statistics
- `GET /cognitive/meta-learning/strategies` - Learning strategies
- `GET /cognitive/counterfactual/insights` - Counterfactual analysis

#### 5. `/crypto` (2 endpoints)

Cryptocurrency market data.

**Endpoints:**

- `GET /crypto/quotes` - Get crypto quotes (e.g., BTC-USD, ETH-USD)
- `GET /crypto/ohlc` - Get OHLC data for crypto

#### 6. `/dev` (9 endpoints)

Development and debugging endpoints.

**Endpoints:**

- `GET /dev/db/status` - Database status
- `POST /dev/db/init` - Initialize database
- `GET /dev/portfolio/status` - Portfolio status
- `POST /dev/portfolio/setup` - Setup portfolio
- `POST /dev/portfolio/fund` - Fund portfolio
- `POST /dev/trading/enable` - Enable trading
- `GET /dev/user` - Get dev user
- `POST /dev/snapshot/now` - Create snapshot
- `GET /dev/state/summary` - State summary

#### 7. `/feedback` (5 endpoints)

System feedback and decision tracking.

**Endpoints:**

- `POST /feedback/decision` - Submit decision feedback
- `POST /feedback/bulk` - Bulk feedback submission
- `GET /feedback/health` - Feedback system health
- `GET /feedback/stats` - Feedback statistics
- `GET /feedback/event/{event_id}` - Get specific event

#### 8. `/integration` (9 endpoints)

System integration and decision enhancement.

**Endpoints:**

- `POST /integration/decision` - Integration decision
- `POST /integration/enhance` - Enhance with integration
- `GET /integration/health` - Integration health
- `GET /integration/status` - Integration status
- `GET /integration/context/market` - Market context
- `POST /integration/calibration/apply` - Apply calibration
- `POST /integration/outcome/update` - Update outcome
- `GET /integration/rules/active` - Active rules
- `POST /integration/test/decision` - Test decision

#### 9. `/learning` (13 endpoints)

Machine learning and adaptive systems.

**Endpoints:**

- `GET /learning/status` - Learning system status
- `GET /learning/health` - Learning system health
- `GET /learning/data/summary` - Data summary
- `GET /learning/rules/current` - Current rules
- `GET /learning/rules/history` - Rules history
- `POST /learning/run` - Run learning
- `GET /learning/results/latest` - Latest results
- `GET /learning/results/history` - Results history
- `GET /learning/evaluate/current` - Current evaluation
- `GET /learning/gates` - Learning gates
- `PUT /learning/gates` - Update learning gates
- `GET /learning/calibration/status` - Calibration status
- `POST /learning/calibration/build` - Build calibration

#### 10. `/market` (11 endpoints)

Market data, calendar, and macroeconomic indicators.

**Endpoints:**

- `GET /market/overview` - Market overview
- `GET /market/breadth` - Market breadth indicators
- `GET /market/risk-lite` - Risk-lite assessment
- `GET /market/macro/history` - Macro history
- `GET /market/calendar` - Market calendar
- `GET /market/schedule` - Market schedule
- `GET /market/holidays` - Market holidays
- `GET /market/earnings` - Earnings calendar
- `GET /market/economic` - Economic calendar
- `GET /market/indicators` - Market indicators
- `GET /market/fred/{series_id}` - FRED data series

#### 11. `/news` (7 endpoints)

News, filings, and sentiment analysis.

**Endpoints:**

- `GET /news/sources` - News sources
- `GET /news/headlines` - Latest headlines
- `GET /news/filings` - SEC filings
- `GET /news/filings/recent` - Recent filings
- `GET /news/sentiment` - News sentiment analysis
- `GET /news/headwind` - Market headwinds
- `GET /news/ping` - News system health check

#### 12. `/paper` (11 endpoints)

Paper trading laboratory.

**Endpoints:**

- `GET /paper/health` - Paper trading health
- `POST /paper/runs` - Create new paper trading run
- `GET /paper/runs` - List all runs
- `GET /paper/runs/{run_id}` - Get specific run
- `POST /paper/runs/{run_id}/stop` - Stop a run
- `GET /paper/runs/{run_id}/trades` - Get trades for run
- `GET /paper/runs/{run_id}/theories` - Get theories
- `GET /paper/runs/{run_id}/stats` - Get statistics
- `GET /paper/runs/{run_id}/models` - Get models
- `POST /paper/runs/{run_id}/theories/{theory_name}/pause` - Pause theory
- `POST /paper/emergency/stop_all` - Emergency stop all

#### 13. `/screener` (7 endpoints)

Stock screening and universe management.

**Endpoints:**

- `GET /screener/health` - Screener health
- `POST /screener/scan` - Run screen
- `GET /screener/regime_summary` - Regime summary
- `GET /screener/universe/sp500` - S&P 500 universe
- `GET /screener/universe/nasdaq100` - NASDAQ 100 universe
- `GET /screener/presets/momentum` - Momentum preset
- `GET /screener/presets/mean_reversion` - Mean reversion preset

#### 14. `/signals` (21 endpoints)

Market brain signals and trading signals.

**Endpoints:**

- `GET /signals/status` - Signal system status
- `GET /signals/config` - Signal configuration
- `PUT /signals/config` - Update configuration
- `GET /signals/regime` - Current regime
- `GET /signals/regime/history` - Regime history
- `GET /signals/signal/{ticker}` - Get signal for ticker
- `POST /signals/watchlist` - Batch signals for watchlist
- `GET /signals/features/{ticker}` - Get features
- `POST /signals/features/bulk` - Bulk features
- `POST /signals/trade/plan` - Plan trade
- `POST /signals/trade/execute` - Execute trade
- `GET /signals/execute/status/{request_id}` - Execution status
- `GET /signals/execute/history` - Execution history
- `GET /signals/execute/stats` - Execution statistics
- `GET /signals/backtest/quick/{ticker}` - Quick backtest
- `GET /signals/backtest/analysis/{ticker}` - Backtest analysis
- `POST /signals/cognitive/signal` - Cognitive signal
- `POST /signals/cognitive/bulk` - Bulk cognitive
- `GET /signals/cognitive/health` - Cognitive health
- `GET /signals/cognitive/regime/{symbol}` - Cognitive regime

#### 15. `/trading` (25 endpoints)

Trading operations, backtesting, and portfolio management.

**Key Endpoints:**

- `POST /trading/backtest` - Run backtest
- `POST /trading/strategy/backtest` - Strategy backtest
- `GET /trading/trade/health` - Trading system health
- `POST /trading/trade/market` - Market order
- `POST /trading/trade/execute` - Execute trade
- `GET /trading/trade/portfolio` - Get portfolio
- `GET /trading/trade/positions` - Get positions
- `GET /trading/trade/orders` - Get orders
- `DELETE /trading/trade/orders/{order_id}` - Cancel order
- `GET /trading/trade/ohlc` - Get OHLC data
- `POST /trading/trade/scan/enable` - Enable scanning
- `GET /trading/trade/scan/status` - Scan status
- `GET /trading/market/breadth` - Market breadth
- `GET /trading/market/risk-lite` - Risk assessment

## Router Configuration

### How Routes are Registered

Routes are registered in `/backend/app/main.py` with specific prefixes:

```python
# Routes with main.py prefix
app.include_router(core_router, prefix="/api")
app.include_router(alerts_router, prefix="/alerts")
app.include_router(crypto_router, prefix="/crypto")
# ... etc

# Routes with their own prefix (no additional prefix in main.py)
app.include_router(signals_router)  # has prefix="/signals"
app.include_router(chat_router)     # has prefix="/chat"
# ... etc
```

### Prefix Rules

1. **Single prefix only**: Each route should have only ONE prefix, either:
   - Defined in the router itself (`APIRouter(prefix="/signals")`)
   - Added when including in main.py (`app.include_router(router, prefix="/market")`)

2. **No duplicate prefixes**: Route decorators should NOT include the prefix that's already set at the router level.
   - ✓ Correct: `@router.get("/overview")` when router has `prefix="/market"`
   - ✗ Wrong: `@router.get("/market/overview")` when router has `prefix="/market"`

## Testing Endpoints

### Using the Verification Script

```bash
cd /home/runner/work/Ziggy1/Ziggy1
python3 scripts/verify_endpoints.py
```

### Using the Route Analysis Tool

```bash
cd /home/runner/work/Ziggy1/Ziggy1
python3 /tmp/analyze_routes.py
```

### Using the Endpoint Lister

```bash
cd /home/runner/work/Ziggy1/Ziggy1/backend
python3 scripts/list_all_endpoints.py
```

This will generate:

- `backend/scripts/endpoints.json` - All endpoints
- `backend/scripts/test_endpoints.json` - GET endpoints for testing

## Frontend Integration

Frontend Next.js API routes proxy to these backend endpoints. The frontend expects single-prefix paths:

- Frontend: `/api/news/sources` → Backend: `/news/sources`
- Frontend: `/api/market/overview` → Backend: `/market/overview`
- Frontend: `/api/signals/watchlist` → Backend: `/signals/watchlist`

All proxy paths have been verified to match the corrected backend endpoints.

## Health Checks

Key health check endpoints:

- `/health` - Root health check
- `/api/core/health` - Core API health
- `/paper/health` - Paper trading health
- `/trading/trade/health` - Trading system health
- `/learning/health` - Learning system health
- `/cognitive/health` - Cognitive system health
- `/screener/health` - Screener health
- `/feedback/health` - Feedback system health
- `/integration/health` - Integration health

## Documentation

- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Verification Status

✅ **All endpoints verified**
✅ **All duplicate prefixes fixed**
✅ **Frontend/backend alignment confirmed**
✅ **170 endpoints properly configured**

---

**Last Updated:** 2025-11-12  
**Verified By:** GitHub Copilot Agent
