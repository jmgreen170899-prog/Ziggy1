# FastAPI Route Audit Report

Generated: January 2025

## Summary

- **Static Routes Found**: 179 routes defined in code
- **Runtime Routes Available**: 1 route actually registered
- **Missing Routes**: 178 routes (99.4% unavailable)

## Analysis

### Available Routes (Runtime)

These routes are properly registered and available:

| Method | Path      | Source           |
| ------ | --------- | ---------------- |
| GET    | `/health` | `app\main.py:43` |

### Unavailable Routes (Static Definitions Only)

The following routes are defined in code but **NOT registered at runtime**:

#### Core API Routes (`app\api\routes.py`)

- `GET /core/health` (line 90) - **UNAVAILABLE**
- `POST /query` (line 153) - **UNAVAILABLE**
- `POST /ingest/web` (line 185) - **UNAVAILABLE**
- `POST /ingest/pdf` (line 196) - **UNAVAILABLE**
- `POST /reset` (line 221) - **UNAVAILABLE**
- `POST /agent` (line 236) - **UNAVAILABLE**
- `POST /tasks/watch` (line 260) - **UNAVAILABLE**
- `GET /tasks` (line 279) - **UNAVAILABLE**
- `DELETE /tasks` (line 291) - **UNAVAILABLE**
- `GET /browse/search` (line 325) - **UNAVAILABLE**
- `GET /browse` (line 445) - **UNAVAILABLE**

#### Alert Routes (`app\api\routes_alerts.py`)

- `GET /alerts/status` (line 174) - **UNAVAILABLE**
- `POST /alerts/start` (line 206) - **UNAVAILABLE**
- `POST /alerts/stop` (line 236) - **UNAVAILABLE**
- `POST /alerts/ping/test` (line 267) - **UNAVAILABLE**
- `POST /alerts/create` (line 332) - **UNAVAILABLE**
- `POST /alerts/sma50` (line 403) - **UNAVAILABLE**
- `POST /alerts/moving-average/50` (line 422) - **UNAVAILABLE**
- `GET /alerts/list` (line 431) - **UNAVAILABLE**
- `GET /alerts/production/status` (line 482) - **UNAVAILABLE**
- `GET /alerts/history` (line 492) - **UNAVAILABLE**
- `DELETE /alerts/{alert_id}` (line 523) - **UNAVAILABLE**
- `PUT /alerts/{alert_id}/enable` (line 546) - **UNAVAILABLE**
- `PUT /alerts/{alert_id}/disable` (line 569) - **UNAVAILABLE**

#### Chat Routes (`app\api\routes_chat.py`)

- `POST /complete` (line 109) - **UNAVAILABLE**
- `GET /health` (line 176) - **UNAVAILABLE**
- `GET /config` (line 213) - **UNAVAILABLE**

#### Cognitive Routes (`app\api\routes_cognitive.py`)

- `GET /status` (line 75) - **UNAVAILABLE**
- `POST /enhance-decision` (line 93) - **UNAVAILABLE**
- `POST /record-outcome` (line 125) - **UNAVAILABLE**
- `GET /meta-learning/strategies` (line 164) - **UNAVAILABLE**
- `GET /counterfactual/insights` (line 186) - **UNAVAILABLE**
- `GET /episodic-memory/stats` (line 207) - **UNAVAILABLE**
- `GET /health` (line 228) - **UNAVAILABLE**

#### Crypto Routes (`app\api\routes_crypto.py`)

- `GET /crypto/quotes` (line 63) - **UNAVAILABLE**
- `GET /crypto/ohlc` (line 165) - **UNAVAILABLE**

#### Development Routes (`app\api\routes_dev.py`)

- `GET /user` (line 40) - **UNAVAILABLE**
- `POST /portfolio/setup` (line 71) - **UNAVAILABLE**
- `GET /portfolio/status` (line 97) - **UNAVAILABLE**
- `POST /portfolio/fund` (line 123) - **UNAVAILABLE**
- `POST /trading/enable` (line 152) - **UNAVAILABLE**
- `GET /db/status` (line 192) - **UNAVAILABLE**
- `POST /db/init` (line 211) - **UNAVAILABLE**
- `POST /snapshot/now` (line 226) - **UNAVAILABLE**
- `GET /state/summary` (line 237) - **UNAVAILABLE**

#### Explain Routes (`app\api\routes_explain.py`)

- `GET /explain` (line 372) - **UNAVAILABLE**
- `POST /explain/feedback` (line 394) - **UNAVAILABLE**
- `GET /explain/health` (line 422) - **UNAVAILABLE**

#### Feedback Routes (`app\api\routes_feedback.py`)

- `POST /decision` (line 66) - **UNAVAILABLE**
- `GET /event/{event_id}` (line 125) - **UNAVAILABLE**
- `GET /stats` (line 195) - **UNAVAILABLE**
- `POST /bulk` (line 313) - **UNAVAILABLE**
- `GET /health` (line 375) - **UNAVAILABLE**

#### Integration Routes (`app\api\routes_integration.py`)

- `GET /health` (line 110) - **UNAVAILABLE**
- `POST /decision` (line 129) - **UNAVAILABLE**
- `POST /enhance` (line 156) - **UNAVAILABLE**
- `GET /context/market` (line 187) - **UNAVAILABLE**
- `GET /rules/active` (line 209) - **UNAVAILABLE**
- `POST /calibration/apply` (line 231) - **UNAVAILABLE**
- `POST /outcome/update` (line 260) - **UNAVAILABLE**
- `GET /status` (line 299) - **UNAVAILABLE**
- `POST /test/decision` (line 352) - **UNAVAILABLE**

#### Learning Routes (`app\api\routes_learning.py`)

- `GET /learning/status` (line 79) - **UNAVAILABLE**
- `GET /learning/data/summary` (line 111) - **UNAVAILABLE**
- `GET /learning/rules/current` (line 155) - **UNAVAILABLE**
- `GET /learning/rules/history` (line 184) - **UNAVAILABLE**
- `POST /learning/run` (line 212) - **UNAVAILABLE**
- `GET /learning/results/latest` (line 237) - **UNAVAILABLE**
- `GET /learning/results/history` (line 261) - **UNAVAILABLE**
- `GET /learning/evaluate/current` (line 295) - **UNAVAILABLE**
- `GET /learning/gates` (line 315) - **UNAVAILABLE**
- `PUT /learning/gates` (line 322) - **UNAVAILABLE**
- `GET /learning/calibration/status` (line 341) - **UNAVAILABLE**
- `POST /learning/calibration/build` (line 358) - **UNAVAILABLE**
- `GET /learning/health` (line 394) - **UNAVAILABLE**

#### Market Routes (`app\api\routes_market.py`)

- `GET /market/overview` (line 86) - **UNAVAILABLE**
- `GET /market/breadth` (line 235) - **UNAVAILABLE**
- `GET /market/risk-lite` (line 506) - **UNAVAILABLE**
- `GET /market/macro/history` (line 704) - **UNAVAILABLE**

#### Market Calendar Routes (`app\api\routes_market_calendar.py`)

- `GET /calendar` (line 31) - **UNAVAILABLE**
- `GET /holidays` (line 51) - **UNAVAILABLE**
- `GET /earnings` (line 64) - **UNAVAILABLE**
- `GET /economic` (line 81) - **UNAVAILABLE**
- `GET /schedule` (line 108) - **UNAVAILABLE**
- `GET /indicators` (line 121) - **UNAVAILABLE**
- `GET /fred/{series_id}` (line 132) - **UNAVAILABLE**

#### News Routes (`app\api\routes_news.py`)

- `GET /news/sources` (line 324) - **UNAVAILABLE**
- `GET /news/headlines` (line 354) - **UNAVAILABLE**
- `GET /news/filings` (line 647) - **UNAVAILABLE**
- `GET /news/filings/recent` (line 713) - **UNAVAILABLE**
- `GET /news/sentiment` (line 913) - **UNAVAILABLE**
- `GET /news/headwind` (line 1010) - **UNAVAILABLE**
- `GET /news/ping` (line 1028) - **UNAVAILABLE**

#### Paper Trading Routes (`app\api\routes_paper.py`)

- `POST /runs` (line 187) - **UNAVAILABLE**
- `GET /runs` (line 221) - **UNAVAILABLE**
- `GET /runs/{run_id}` (line 245) - **UNAVAILABLE**
- `POST /runs/{run_id}/stop` (line 264) - **UNAVAILABLE**
- `GET /runs/{run_id}/trades` (line 294) - **UNAVAILABLE**
- `GET /runs/{run_id}/theories` (line 341) - **UNAVAILABLE**
- `POST /runs/{run_id}/theories/{theory_name}/pause` (line 377) - **UNAVAILABLE**
- `GET /runs/{run_id}/stats` (line 410) - **UNAVAILABLE**
- `GET /runs/{run_id}/models` (line 467) - **UNAVAILABLE**
- `POST /emergency/stop_all` (line 510) - **UNAVAILABLE**
- `GET /health` (line 540) - **UNAVAILABLE**

#### Performance Routes (`app\api\routes_performance.py`)

- `GET /metrics` (line 26) - **UNAVAILABLE**
- `GET /metrics/summary` (line 54) - **UNAVAILABLE**
- `POST /metrics/clear` (line 76) - **UNAVAILABLE**
- `GET /benchmarks` (line 98) - **UNAVAILABLE**
- `POST /benchmarks/feature-computation` (line 121) - **UNAVAILABLE**
- `POST /benchmarks/signal-generation` (line 149) - **UNAVAILABLE**
- `POST /benchmarks/clear` (line 177) - **UNAVAILABLE**
- `GET /health` (line 199) - **UNAVAILABLE**

#### Risk Routes (`app\api\routes_risk_lite.py`)

- `GET /market-risk-lite` (line 51) - **UNAVAILABLE**
- `GET /market/risk-lite` (line 90) - **UNAVAILABLE**

#### Screener Routes (`app\api\routes_screener.py`)

- `POST /scan` (line 65) - **UNAVAILABLE**
- `GET /universe/sp500` (line 191) - **UNAVAILABLE**
- `GET /universe/nasdaq100` (line 256) - **UNAVAILABLE**
- `GET /presets/momentum` (line 321) - **UNAVAILABLE**
- `GET /presets/mean_reversion` (line 351) - **UNAVAILABLE**
- `GET /regime_summary` (line 382) - **UNAVAILABLE**
- `GET /health` (line 448) - **UNAVAILABLE**

#### Signals Routes (`app\api\routes_signals.py`)

- `GET /features/{ticker}` (line 195) - **UNAVAILABLE**
- `POST /features/bulk` (line 216) - **UNAVAILABLE**
- `GET /regime` (line 254) - **UNAVAILABLE**
- `GET /regime/history` (line 269) - **UNAVAILABLE**
- `GET /signal/{ticker}` (line 287) - **UNAVAILABLE**
- `POST /watchlist` (line 340) - **UNAVAILABLE**
- `POST /trade/plan` (line 406) - **UNAVAILABLE**
- `POST /trade/execute` (line 468) - **UNAVAILABLE**
- `GET /status` (line 510) - **UNAVAILABLE**
- `GET /config` (line 545) - **UNAVAILABLE**
- `PUT /config` (line 556) - **UNAVAILABLE**
- `POST /execute/trade` (line 605) - **UNAVAILABLE**
- `GET /execute/status/{request_id}` (line 672) - **UNAVAILABLE**
- `GET /execute/history` (line 708) - **UNAVAILABLE**
- `GET /execute/stats` (line 738) - **UNAVAILABLE**
- `GET /backtest/quick/{ticker}` (line 767) - **UNAVAILABLE**
- `GET /backtest/analysis/{ticker}` (line 832) - **UNAVAILABLE**
- `POST /cognitive/signal` (line 915) - **UNAVAILABLE**
- `GET /cognitive/regime/{symbol}` (line 1079) - **UNAVAILABLE**
- `POST /cognitive/bulk` (line 1115) - **UNAVAILABLE**
- `GET /cognitive/health` (line 1211) - **UNAVAILABLE**

#### Trace Routes (`app\api\routes_trace.py`)

- `GET /trace` (line 230) - **UNAVAILABLE**
- `GET /trace/list` (line 253) - **UNAVAILABLE**
- `GET /trace/health` (line 296) - **UNAVAILABLE**

#### Trading Routes (`app\api\routes_trading.py`)

- `GET /trade/health` (line 196) - **UNAVAILABLE**
- `GET /trade/screener` (line 243) - **UNAVAILABLE**
- `POST /trade/explain` (line 275) - **UNAVAILABLE**
- `POST /trade/notify` (line 633) - **UNAVAILABLE**
- `GET /trade/notify/diag` (line 657) - **UNAVAILABLE**
- `GET /trade/notify/probe` (line 662) - **UNAVAILABLE**
- `POST /trade/notify/test` (line 667) - **UNAVAILABLE**
- `GET /trade/scan/status` (line 685) - **UNAVAILABLE**
- `POST /trade/scan/enable` (line 690) - **UNAVAILABLE**
- `GET /market/calendar` (line 699) - **UNAVAILABLE**
- `GET /trade/ohlc` (line 769) - **UNAVAILABLE**
- `GET /market/breadth` (line 1057) - **UNAVAILABLE**
- `GET /market/risk-lite` (line 1174) - **UNAVAILABLE**
- `GET /market-risk-lite` (line 1223) - **UNAVAILABLE**
- `GET /market/risk` (line 1228) - **UNAVAILABLE**
- `POST /trading/backtest` (line 1497) - **UNAVAILABLE**
- `POST /backtest` (line 1681) - **UNAVAILABLE**
- `POST /strategy/backtest` (line 1686) - **UNAVAILABLE**
- `POST /trade/market` (line 1772) - **UNAVAILABLE**
- `GET /trade/orders` (line 1984) - **UNAVAILABLE**
- `GET /trade/positions` (line 1996) - **UNAVAILABLE**
- `GET /trade/portfolio` (line 2008) - **UNAVAILABLE**
- `DELETE /trade/orders/{order_id}` (line 2020) - **UNAVAILABLE**
- `POST /trade/execute` (line 2042) - **UNAVAILABLE**
- `POST /trade/mode/{mode}` (line 2071) - **UNAVAILABLE**

#### Trading Module Routes (`app\trading\router.py`)

- `POST /market` (line 219) - **UNAVAILABLE**
- `POST /bracket` (line 367) - **UNAVAILABLE**
- `GET /health` (line 415) - **UNAVAILABLE**
- `POST /panic` (line 458) - **UNAVAILABLE**
- `GET /quality` (line 564) - **UNAVAILABLE**
- `POST /resume` (line 584) - **UNAVAILABLE**

#### Web Browse Routes (`app\web\browse_router.py`)

- `GET /web/browse/search` (line 19) - **UNAVAILABLE**
- `GET /web/browse` (line 88) - **UNAVAILABLE**

## Root Cause Analysis

The critical issue is that **NO router modules are being included** in the main FastAPI application. Looking at `main.py`, only the basic `/health` endpoint is defined directly on the app instance.

### Missing Router Registrations

The application should include routers like:

```python
app.include_router(routes.router, prefix="/api")
app.include_router(routes_alerts.router, prefix="/api")
app.include_router(routes_chat.router, prefix="/api")
# ... etc for all route modules
```

### Impact Assessment

- **Severity**: CRITICAL - 99.4% of intended functionality unavailable
- **User Impact**: Only health check works, all business logic endpoints missing
- **Development Impact**: Extensive route definitions exist but are unused

## Recommendations

1. **Immediate Action**: Add router registration in `main.py`
2. **Verification**: Test key endpoints after router inclusion
3. **Documentation**: Update API documentation to reflect actual available routes
4. **Testing**: Implement automated tests to catch router registration issues

## Files Requiring Router Registration

The following router modules need to be included in `main.py`:

- `app.api.routes`
- `app.api.routes_alerts`
- `app.api.routes_chat`
- `app.api.routes_cognitive`
- `app.api.routes_crypto`
- `app.api.routes_dev`
- `app.api.routes_explain`
- `app.api.routes_feedback`
- `app.api.routes_integration`
- `app.api.routes_learning`
- `app.api.routes_market`
- `app.api.routes_market_calendar`
- `app.api.routes_news`
- `app.api.routes_paper`
- `app.api.routes_performance`
- `app.api.routes_risk_lite`
- `app.api.routes_screener`
- `app.api.routes_signals`
- `app.api.routes_trace`
- `app.api.routes_trading`
- `app.trading.router`
- `app.web.browse_router`
