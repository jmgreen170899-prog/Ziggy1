# Copilot Task — ZiggyAI Code Health (UI-First, then API)

**Primary Goal:** Fix user-facing issues first. Audit and improve the **frontend UI** (rendering, data integrity, performance, a11y), then verify and harden the **backend API**.

## Phase 1 — Frontend UI (React/Vite/Tailwind) ✅ PRIORITY

**Targets:** syntax/type errors, broken renders, stale/missing data, duplications, unused code, perf/a11y.

1. **Strict Type & Lint**

* Add/ensure `tsconfig.strict.json` (noImplicitAny, strictNullChecks).
* Run `tsc --noEmit -p tsconfig.strict.json`.
* ESLint on `src/**/*.{ts,tsx}` with zero warnings.

2. **Route & Render Audit**

* Enumerate all routes/tabs (Chat, Market, Alerts, Paper/Status, Settings, etc.).
* Add Playwright test `scripts/ui_audit.spec.ts`:

  * Start dev server, visit each route, wait for "data loaded" selectors.
  * Capture full-page screenshots to `artifacts/ui/<route>.png`.
  * Collect JSON per route: card/table counts, NaN/∞ cells, missing fields, stale timestamps (TTL), console errors, network errors.
  * Fail test on unhandled exceptions or empty critical views.

3. **Perf & A11y Pass**

* Run Lighthouse per route; save `artifacts/ui/lh_<route>.json`.
* Flag: layout shift > 0.1, large JS bundles, images without `width/height`, low contrast.

4. **Duplication & Unused**

* `jscpd` across `frontend/src` → `artifacts/frontend/jscpd.json`.
* `knip`, `ts-prune`, `depcheck` → list unused files/exports/deps.

5. **UI Fix Kit (apply where needed)**

* Add loading skeletons, empty states, and error boundaries to each data view.
* Replace polling with `stale-while-revalidate` patterns where appropriate.
* Clamp/truncate overflowing text; add tooltips for long tickers/IDs.
* Standardise `timeago`/TTL badges; highlight "stale > TTL".
* Debounce inputs & network calls; memoise heavy lists; virtualise long tables.

6. **Output**

* Generate `UI_HEALTH_REPORT.md` with per-route findings (P0 broken, P1 UX, P2 polish), linked screenshots, and a checkbox fix list.

**Frontend scripts (add to package.json):**

```json
{
  "scripts": {
    "audit:fe:types": "tsc -p tsconfig.strict.json --noEmit",
    "audit:fe:lint": "eslint \"src/**/*.{ts,tsx}\" --max-warnings=0",
    "audit:fe:dup": "jscpd -c jscpd.config.json",
    "audit:fe:unused": "knip && ts-prune && depcheck",
    "audit:fe:ui": "playwright test scripts/ui_audit.spec.ts"
  }
}
```

---

## Phase 2 — Backend API (FastAPI/SQLAlchemy) 🔧 SECOND

**Targets:** syntax/type errors, failed endpoints, duplications, unnecessary code, security basics.

1. **Smoke Test All Routes**

* `tests/test_endpoints_smoke.py`: introspect `app.routes`, GET/HEAD known-safe paths.
* Record 4xx/5xx to `artifacts/backend/endpoints_failures.json`.

2. **OpenAPI Fuzz**

* Schemathesis against `app.openapi()` (GET/POST with small example cap).
* Save `artifacts/backend/schemathesis_report.json`.

3. **Syntax/Type/Sec**

* `ruff check`, `mypy backend`, `bandit -r backend` → artifacts text logs.

4. **Dead Code & Duplication**

* `vulture` (with whitelist) → `artifacts/backend/vulture.json`.
* `jscpd` → `artifacts/backend/jscpd.json`.

5. **Health Endpoint Sanity**

* Ensure `/paper/health` returns: `paper_enabled`, `strict_isolation`, `broker`, `recent_trades_5m`, `total_trades_today`, `last_trade_at`, `db_ok`, `last_error`.
* Return **503** if engine running but no trades in 15m; **500** if strict isolation fails.

6. **Output**

* Generate `API_HEALTH_REPORT.md` summarising failing endpoints, stack traces, type errors, dead code, and dup blocks with fix suggestions.

---

## Consolidated Report

* Script `scripts/generate_code_health_report.py` merges all artifacts into **`CODE_HEALTH_REPORT.md`** with:

  * P0: Frontend broken renders / Backend failing endpoints
  * P1: Type/lint errors, security warnings
  * P2: Duplications, unused code/deps
  * Actionable checklist (file:line → fix)

---

## Acceptance Criteria

* **Frontend:** `audit:fe:*` + `audit:fe:ui` pass; `UI_HEALTH_REPORT.md` lists zero P0 issues; screenshots show fully rendered data for every tab with TTL badges.
* **Backend:** Smoke + Schemathesis show zero P0 failures; `/paper/health` returns 200 with valid metrics when engine active (or 503/500 with clear reasons).
* **Repo:** `CODE_HEALTH_REPORT.md` present with linked artifacts and next steps.

**Do not refactor business logic;** focus on detection, clear diagnostics, and minimal, targeted fixes to get the UI pristine first, then the API green.