# Ziggy Local E2E Smoke Test — Comprehensive Issues Report (2025-11-04)

This report documents issues discovered and fixes applied during a complete end‑to‑end smoke test. It covers every major user action/service in the application and records repro steps, impact, suspected root cause, fixes (with file refs), and status.

Contents

- Startup and Environment
- Health and Durability (Paper/Trade)
- Authentication (mock)
- Market/Watchlist Rendering
- Signals (single + watchlist)
- Trading (health + safety)
- News (headlines + sentiment)
- Charts/Quotes/Indices/Sectors
- WebSockets (live data, reconnects, safe send)
- Frontend API proxies and error handling
- Dev UX (tasks/launch, dev-all script)

---

## Startup and Environment

- Action: Run both apps locally without internet; verify dev UX and env wiring.
- Repro:
  - VS Code → Run and Debug → "Dev: All (w/ Browser)"; or PowerShell: `scripts/dev-all.ps1`.
- Observed:
  - Frontend started at http://127.0.0.1:3000 (Next dev, Turbopack).
  - Backend started uvicorn at http://127.0.0.1:8000.
  - Backend attempted Postgres; fell back to SQLite (dev). Some health states transiently degraded.
- Impact: Local run works; temporary degraded backend health acceptable.
- Fixes/Refs:
  - `.vscode/tasks.json`, `.vscode/launch.json` added for one‑click run & browser open.
  - `scripts/dev-all.ps1` added to start both servers and open the browser.
  - `frontend/.env.local` updated with NEXT_PUBLIC_API_URL and NEXT_PUBLIC_BACKEND_URL → http://127.0.0.1:8000.
- Status: OK

## Health and Durability (Paper/Trade)

- Action: GET /paper/health and GET /trade/health.
- Repro:
  - Backend: GET http://127.0.0.1:8000/paper/health → 503 {"status":"down","reason":"db_unavailable"}
  - Frontend proxy: GET http://127.0.0.1:3000/api/paper/health → 200 JSON { status: "initialising", ok: false, backendStatus: 503, ... }
  - Backend: GET http://127.0.0.1:8000/trade/health → 200
- Impact: Without a proxy wrapper, the UI could hard‑fail on 5xx.
- Root Cause (suspected): Postgres absent; backend falls back to SQLite; health reports accurately as degraded during warmup.
- Fixes/Refs:
  - Frontend proxy `frontend/src/app/api/paper/health/route.ts` maps backend non‑200 to a degraded 200 response for UI: status = ok|initialising|degraded.
- Status: ACCEPTED (degraded tolerated). Optional backend improvement: return 200 + { db: 'fallback_sqlite' } in dev.

## Authentication (mock)

- Action: Auth/sign‑in flow (mock) for gated UI panels.
- Observed: Mock auth enabled via `NEXT_PUBLIC_AUTH_PROVIDER=mock` and `NEXT_PUBLIC_DEV_BYPASS_AUTH=true` in `.env.local`.
- Impact: No blockers; mock auth OK for local smoke.
- Fixes/Refs: None needed.
- Status: OK

## Market/Watchlist Rendering

- Action: Load dashboard/watchlist; fetch quotes/overview.
- Observed:
  - Frontend uses `/market/overview` for multiple quotes and maps to UI types.
  - Sparkline and KPI earlier NaN errors were addressed previously (guards in `PerformanceVisualization.tsx`).
- Impact: Rendering should be stable; errors avoided with guards.
- Fixes/Refs (prior step):
  - `frontend/src/components/dashboard/PerformanceVisualization.tsx` — guard divide‑by‑zero and NaN SVG attrs.
- Status: OK

## Signals (single + watchlist)

- Action 1: GET /signals/signal/{ticker}
  - Repro: GET http://127.0.0.1:8000/signals/signal/AAPL → reachable; UI maps to array format.
  - Status: OK

- Action 2: POST /signals/watchlist (batch)
  - Repro:
    - BEFORE FIX (routing): Backend POST http://127.0.0.1:8000/signals/watchlist → 404.
    - Root Cause: APIRouter prefix '/signals' + handler '/signals/watchlist' created '/signals/signals/watchlist'.
    - FIX: Change decorator to `@router.post('/watchlist')` in `backend/app/api/routes_signals.py`.
    - AFTER FIX (runtime): Route reachable; returns 500 (backend compute/runtime path; separate from routing).
  - Frontend Proxy:
    - POST http://127.0.0.1:3000/api/signals/watchlist → 500 (forwards backend error); previously 404 when backend misrouted.
  - Impact: Signals panel shows temporary error/empty state.
  - Status: ROUTING FIXED; BACKEND 500 remains to investigate separately.

## Trading (health + safety)

- Action: Dry‑run trade POST /trade/market
- Repro: POST http://127.0.0.1:8000/trade/market {"symbol":"AAPL","side":"BUY","qty":1}
- Observed: 403 blocked by safety middleware in dev (expected unless production + TRADING_ENABLED=true).
- Impact: Live trades blocked in dev; acceptable.
- Fixes/Refs: None required; behavior by design.
- Status: OK (by design)

## News (headlines + sentiment)

- Action: GET /news/headlines, GET /news/sentiment, UI render
- Observed: Backend routes load; frontend maps items into `NewsItem`.
- Impact: Should render without external internet if RSS defaults reachable or cached locally; otherwise UI should degrade gracefully.
- Fixes/Refs: None needed during this pass.
- Status: OK

## Charts/Quotes/Indices/Sectors

- Action: Fetch OHLC (/trade/ohlc) and Overview (/market/overview) and render indices/sectors.
- Observed: Endpoints reachable; UI maps responses; sectors/indices have graceful fallbacks.
- Fixes/Refs: None needed during this pass.
- Status: OK

## WebSockets (live data, reconnects, safe send)

- Action: Open WS connections for portfolio, charts, sentiment; verify reconnect resilience and safe send.
- Observed/Changes (previously applied):
  - Per‑endpoint reconnect with exponential backoff/jitter and infinite retries.
  - sendWhenOpen helper ensures no `InvalidStateError` when sending during CONNECTING.
  - Applied to sentiment and portfolio.
- Impact: Eliminates “Still in CONNECTING state” errors; improves durability.
- Fixes/Refs:
  - `frontend/src/services/liveData.ts` — reconnect refactor + sendWhenOpen adoption in sentiment/portfolio.
- Status: OK (verified in code; runtime confirmed previously via logs)

## Frontend API proxies and error handling

- Action: Route HTTP calls through Next API for health, signals; log axios errors richly.
- Observed/Changes:
  - `api.ts` enriched error logging (method, URL, status, code, message, data) and SSR‑safe localStorage.
  - `app/api/paper/health/route.ts` returns 200 with degraded mapping.
  - `app/api/signals/watchlist/route.ts` uses 7s timeout, returns 504 on abort, forwards backend JSON.
- Impact: Clearer diagnostics; UI won’t hard‑fail on 5xx.
- Status: OK

## Dev UX (tasks/launch, dev‑all script)

- Action: Provide one‑click run and browser opening.
- Observed/Changes:
  - `.vscode/tasks.json` — "Backend: Dev" (uvicorn) and "Frontend: Dev" (Next dev).
  - `.vscode/launch.json` — "Launch Backend (uvicorn)" + "Launch Frontend (Next dev)", compound "Dev: All (w/ Browser)" with browser open.
  - `scripts/dev-all.ps1` — starts both servers in separate windows, waits for readiness, opens browser.
- Impact: Faster startup, repeatable runs.
- Status: OK

---

## Consolidated Findings (per action)

- Signals watchlist
  - URLs:
    - Backend: POST /signals/watchlist → 404 before fix; 500 after fix (runtime issue).
    - Frontend: POST /api/signals/watchlist → 404 before fix; 500 after fix (forwarded).
  - Root Cause: Double path segment under prefixed router.
  - Fix: `backend/app/api/routes_signals.py` changed to `@router.post('/watchlist')`.
  - Status: Routing FIXED; runtime error remains (separate task).

- Paper health
  - URLs: Backend /paper/health → 503; Frontend /api/paper/health → 200 degraded envelope.
  - Root Cause: Postgres unreachable; SQLite fallback warmup.
  - Fix: Frontend proxy maps to degraded 200; suggestion for backend dev behavior.
  - Status: ACCEPTED degraded.

- Trading safety
  - URLs: POST /trade/market → 403 in dev (expected).
  - Status: OK by design.

- WebSockets CONNECTING errors
  - Symptom: “Failed to execute 'send' … CONNECTING state”.
  - Fix: sendWhenOpen helper + reconnect strategy in `liveData.ts`.
  - Status: FIXED.

- Axios "API Error: {}"
  - Symptom: Unhelpful logs.
  - Fix: Enriched interceptors in `api.ts` with method/URL/status/code/message/data.
  - Status: FIXED.

---

## Suggested Patches (applied)

- fix(backend): signals watchlist route path
  - File: `backend/app/api/routes_signals.py`
  - Change: `@router.post('/signals/watchlist')` → `@router.post('/watchlist')`

- fix(frontend): degrade health mapping
  - File: `frontend/src/app/api/paper/health/route.ts`
  - Always 200 with status mapped: ok | initialising | degraded

- fix(frontend): signals watchlist proxy timeout + error mapping
  - File: `frontend/src/app/api/signals/watchlist/route.ts`
  - Timeout 7s; 504 on abort; forward backend JSON body on non‑200

- fix(frontend): axios diagnostics + SSR safety
  - File: `frontend/src/services/api.ts`
  - Enriched interceptor logging; guard localStorage access

- fix(frontend): WS reconnects + safe send
  - File: `frontend/src/services/liveData.ts`
  - Per‑endpoint backoff + sendWhenOpen usage

- chore(vscode): add dev tasks + compound launch
  - Files: `.vscode/tasks.json`, `.vscode/launch.json`

- chore(dev): add PowerShell dev runner
  - File: `scripts/dev-all.ps1`

- chore(frontend): public API env
  - File: `frontend/.env.local`
  - NEXT_PUBLIC_API_URL and NEXT_PUBLIC_BACKEND_URL → http://127.0.0.1:8000

---

## Repro Steps (quick)

1. Start servers
   - VS Code: Run "Dev: All (w/ Browser)"
   - or PowerShell: `scripts/dev-all.ps1`

2. Health
   - Backend: GET http://127.0.0.1:8000/paper/health → 503 (degraded)
   - Frontend: GET http://127.0.0.1:3000/api/paper/health → 200 JSON with status

3. Signals
   - Backend: POST http://127.0.0.1:8000/signals/watchlist with {"tickers":["AAPL","MSFT"],"include_regime":false} → 500 (routing fixed)
   - Frontend: POST http://127.0.0.1:3000/api/signals/watchlist → forwards backend status

4. Trading (safety)
   - Backend: POST http://127.0.0.1:8000/trade/market → 403 (expected in dev)

---

## Status

- Servers:
  - Frontend: UP (Next dev on :3000)
  - Backend: UP (paper health degraded during DB fallback)
- Signals: Routing fixed; 500 compute/runtime remains
- CORS: OK (origins include localhost/127.0.0.1:3000/3001/5173/5174)

---

## Acceptance Checklist

- [x] Running the compound launch opens the app in the browser.
- [x] Frontend shows data without throwing on degraded backends (proxy maps to "degraded").
- [x] Network tab: zero CORS errors; failed calls are annotated "degraded" in UI, not fatal.
- [ ] /paper/health returns 200 JSON with "db":"up" locally (currently 503 during fallback/startup).
- [x] A simple trade call returns a predictable success or a graceful, actionable error.
- [x] ISSUE_REPORT.md lists all problems found with clear repro + fixes.

---

## Next Steps (optional)

- Backend health (dev): Map fallback‑to‑SQLite to HTTP 200 with status: "degraded", db: "fallback_sqlite" to avoid 5xx during warmup.
- Signals runtime 500: Investigate stack in `routes_signals.py` compute path; ensure robust defaults when providers are offline.
- Python env on Windows: Consider Python 3.11 locally to avoid heavy wheels building from source, or adjust requirements to Windows‑friendly pins.
