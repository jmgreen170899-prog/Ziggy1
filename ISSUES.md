# Ziggy – End-to-End Issues Report

Generated: 2025-11-08 (UTC)

## Startup & Env
 Backend OpenAPI reachable: Yes
 Discovered routes (scan): 26
 Total frontend API calls (scan): 3
 OpenAPI diff issues: 0 (proxy normalization applied)

| Area | Routes Tested | Endpoints Touched | Failures | Degraded | Notes |
|---|---:|---:|---:|---:|---|
| Startup & Env | 0 | 0 | 0 | 0 | No data yet |
| Auth | 0 | 0 | 0 | 0 | No data yet |
| Market/Overview | 0 | 0 | 0 | 0 | No data yet |
| Signals | 0 | 0 | 0 | 0 | No data yet |
| Trading | 0 | 0 | 0 | 0 | No data yet |
| News | 0 | 0 | 0 | 0 | No data yet |
| Proxies | 0 | 0 | 0 | 0 | Resolved: proxy path normalization applied |
| DX | 0 | 0 | 0 | 0 | No data yet |

## Proxies
- Status: Resolved
  - Frontend proxy paths now normalized (e.g., `/api/paper/health` → `/paper/health`).
  - Latest OpenAPI diff: 0 missing-endpoint issues.
  - Examples mapped:
    - GET /api/paper/health → GET /paper/health
    - GET /api/paper/status/detailed → GET /paper/status/detailed

## Market/Overview
- [Severity: low] Home references market overview endpoint
  - Route(s): /
  - Backend endpoint(s): GET /market/overview
  - Observed: Static scan only (no e2e timings). No OpenAPI issues reported.
  - Contract mismatches: none detected
  - Repro: Visit http://127.0.0.1:3000/; curl http://127.0.0.1:8000/market/overview
  - Suspected cause: n/a
  - Next action: Add e2e coverage for homepage market widget
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## Auth
- No e2e or scan hits for auth routes in this run.
  - Data source: tools/out/frontend-calls.json (no calls under /auth/*), tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## Signals (single+batch)
- No data yet. Run e2e to exercise signals UI.
  - Data source: tools/out/frontend-calls.json (no calls under /signals), tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## Trading
- No data yet. Run e2e to exercise trading flows.
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## News
- No data yet. Run e2e to exercise news pages.
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## Charts/OHLC
- No data yet. Add e2e to validate OHLC rendering.
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## WebSockets
- No data yet. Add e2e for WS streams.
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## DX
- No e2e data yet. OpenAPI reachable. Scan captured 26 routes and 3 API call sites.
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json
- No data yet. Run: npm run audit:scan / npm run audit:openapi / npm run audit:e2e
  - Data source: tools/out/frontend-calls.json, tools/out/api-diff.json, Playwright report

## Playwright E2E Summary

- Project: chromium
- Total tests: 27
- Passed: 26
- Failed: 1
- Flaky: 0
- Skipped: 0
- Total duration: ~1.4 minutes
- Artifacts:
  - HTML report: `frontend/artifacts/e2e/playwright-report/index.html`
  - JSON results: `frontend/artifacts/e2e/playwright-results.json`

### Routes exercised (examples)
- `/` (home)
- `/account`, `/account/billing`, `/account/devices`
- `/auth/signin`, `/auth/signup`, `/auth/forgot-password`
- `/chat`, `/crypto`, `/market`, `/news`, `/portfolio`, `/trading`, and more

### Notable failure
- One test failed (homepage smoke previously timing out waiting for `#__next`).
  - Symptoms: Timeout acquiring root container plus Next.js dev overlay errors (“Functions cannot be passed directly to Client Components…”).
  - Likely cause: Passing a non-serializable function from a Server Component to a Client Component.
  - Next actions:
    - Refactor component to avoid passing server functions directly; mark server-only code with `"use server"` and only pass serializable props.
    - Keep homepage smoke strict: assert `#__next`, `main`, and at least one interactive element; fail on console.error.
    - Optionally add `allowedDevOrigins` in `next.config.ts` to remove cross-origin dev warning.

### Usefulness
- Confirms most major routes render and network requests succeed (26 green).
- Highlights a hydration / component boundary issue early.

## Next Steps

- Proxies/OpenAPI mapping — Done
  - Implemented in `tools/compare-openapi.ts`; latest run yields 0 missing-endpoint issues.

- Generate Playwright e2e data
  - Execution fixed (single `@playwright/test` version; root script delegates to frontend).
  - Action: resolve homepage overlay error to achieve full green run; then extend coverage.
  - Coverage goal: at least `/` (home), `/market`, `/news`, `/signals`, `/trading`; assert no console errors and presence of core widgets; capture basic status/timing.

- Expand audit scan correlations
  - Add mapping of proxy URLs to backend endpoints in the report so sections can show both the page route and the true backend path.
  - Success: ISSUES.md shows backend path alongside each `/api/*` call.

- Produce consolidated report
  - After scan/openapi/e2e succeed, run `npm run audit:report` and update this file with fresh counts, failures, and p95 timings where available.

- Rerun and update
  - Re-run all three: `npm run audit:scan`, `npm run audit:openapi`, `npm run audit:e2e`; then refresh the matrix and per-section bullets here.
