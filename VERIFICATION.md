# Route Wiring & E2E Verification

This document describes the verification suite that ensures all backend routes are properly wired and the full application works end-to-end.

## Components

### 1. Static Endpoint Audit
**Location**: `backend/scripts/static_endpoint_audit.py`

Parses all FastAPI endpoints to detect "do-nothing" implementations:
- Empty or pass-only function bodies
- Functions that raise `NotImplementedError`
- Placeholder returns that don't use input parameters

**Usage**:
```bash
cd backend
python scripts/static_endpoint_audit.py
```

**Marking Intentional Placeholders**:
Add `# pragma: placeholder-ok` comment above the function to skip validation.

### 2. Runtime Route Tests
**Location**: `backend/tests/test_routes_wired.py`

Verifies routes work correctly at runtime:
- OpenAPI schema contains 175+ paths
- All GET endpoints return non-500 status codes
- Health endpoints return 200

**Usage**:
```bash
cd backend
pytest tests/test_routes_wired.py -v
```

### 3. Frontend E2E Tests
**Location**: `frontend/tests/e2e/routes-wired.spec.ts`

Full-stack integration tests using Playwright:
- Homepage loads successfully
- Core UI sections render
- Backend API is accessible
- API calls succeed (no 5xx errors)

**Usage**:
```bash
cd frontend
npm run e2e
```

## CI Workflow

**Location**: `.github/workflows/verify.yml`

Automated verification on every PR:

1. **Backend Tests**: Runs static audit and runtime tests
2. **E2E Tests**: Builds frontend, starts both servers, runs Playwright tests
3. **Summary**: Generates report with route counts and test results

## Running Locally

### Backend Only
```bash
cd backend
python scripts/static_endpoint_audit.py
pytest tests/test_routes_wired.py tests/test_do_nothing_endpoints.py -v
```

### Full E2E
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Start frontend  
cd frontend
npm run dev

# Terminal 3: Run e2e tests
cd frontend
npx playwright test tests/e2e/routes-wired.spec.ts
```

## Expected Results

- ✅ Static audit: No do-nothing endpoints (or only those marked with pragma)
- ✅ OpenAPI paths: 175+ registered routes
- ✅ Health endpoints: All return 200
- ✅ GET smoke tests: No 5xx errors (4xx allowed for auth/validation)
- ✅ E2E tests: Frontend loads, API calls succeed

## Troubleshooting

### Static Audit Failures
If the audit finds problematic endpoints:
1. Review the reported file and line number
2. If it's intentional, add `# pragma: placeholder-ok`
3. If it's a real placeholder, implement the logic

### Route Count Below 175
Check `backend/app/main.py` for router registration:
```python
app.include_router(some_router, prefix="/prefix")
```

### E2E Test Failures
1. Ensure both servers are running
2. Check browser console for errors
3. Review Playwright report: `frontend/playwright-report/`

## Maintenance

When adding new endpoints:
1. Implement full logic (no placeholders)
2. Run static audit to verify
3. Tests will automatically include new routes

When adding new features:
1. Add feature-specific e2e tests to `frontend/tests/e2e/`
2. Update this documentation
