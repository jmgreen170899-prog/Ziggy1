# API Coverage Report

Date: 2025-11-04

This snapshot summarizes the frontend’s usage of backend endpoints, based on the verification script.

## Summary

- API base used: `NEXT_PUBLIC_API_URL` (default http://127.0.0.1:8000)
- Placeholders: None detected in runtime `src/**`
- Included endpoints covered: 100% (all included routes referenced)
- Exclusions: Maintained in `frontend/scripts/endpoint-coverage.config.json` for backend/admin-only or dev-maintenance routes

## How this report is produced

From `frontend/`:

```powershell
npm run verify:endpoints
```

The script fetches the backend OpenAPI, scans `src/**` for endpoint usage, and writes `frontend/scripts/.endpoint-usage.json`. The dev-only dashboard is available at `/dev/api-coverage`.

## Placeholder cleanup (examples)

Key runtime files refactored away from mock/placeholder usage and wired to live endpoints:

- `src/app/portfolio/page.tsx` — removed inline preview data; combines `/trade/portfolio` + `/trade/orders` and live quotes.
- `src/services/api.ts` — unified client; references market, trade, news, crypto, alerts, and learning routes.
- `src/lib/guardRealData.ts` — dev-only safeguard to warn on obvious placeholder values.

## CI integration

The CI workflow starts a lightweight FastAPI server to expose OpenAPI, runs the verifier in `frontend/`, and fails if coverage regresses or placeholders reappear.

## Exclusion policy

Integration, signals, paper-trading, dev utilities, and admin/maintenance endpoints are excluded from coverage until they’re surfaced in the UI. See `frontend/scripts/endpoint-coverage.config.json` for exact patterns.
