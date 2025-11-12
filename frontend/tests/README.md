# Human E2E Verification System

This directory contains the human-simulation E2E verification crawler for the Ziggy1 application.

## Overview

The verification system provides automated, human-like testing of the full application stack:
- **Backend**: FastAPI server on port 8000
- **Frontend**: Next.js application on port 5173
- **Playwright**: Chromium-based browser automation with human-like interactions

## Components

### `verify.crawl.mjs`
The main crawler script that performs human-simulation testing:
- **API Verification**: Checks `/health` endpoint and validates OpenAPI specification
- **Endpoint Probing**: Tests all GET endpoints without parameters for 5xx errors
- **UI Navigation**: Visits key application routes with realistic user behavior
- **Human Interactions**: Mouse movements, clicks, typing, scrolling with random pauses
- **Error Detection**: Monitors console errors and network failures
- **Safety Mode**: Prevents destructive actions (delete, trade, buy, sell) when enabled

### Configuration

Environment variables control the crawler behavior:

```bash
# Required URLs
UI_URL=http://localhost:5173          # Frontend URL
API_URL=http://localhost:8000         # Backend API URL

# Verification thresholds
MIN_OPENAPI_PATHS=175                 # Minimum OpenAPI paths required
SAFE_MODE=true                        # Enable/disable safety checks

# Routes to visit
# Hardcoded: ["/", "/markets", "/signals", "/news", "/chat", "/admin"]
```

### Scripts

From `frontend/package.json`:

```bash
# Install Playwright browsers
npm run playwright:install

# Run standard Playwright tests
npm run test:e2e

# Run human simulation crawler
npm run verify:crawl
```

## Usage

### Local Testing

1. **Start Backend**:
   ```bash
   cd backend
   DOCS_ENABLED=true python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   PORT=5173 npm run dev
   ```

3. **Run Crawler**:
   ```bash
   cd frontend
   npm run verify:crawl
   ```

### CI/CD Integration

The workflow `.github/workflows/verify-e2e.yml` automatically:
1. Sets up Python and Node.js environments
2. Installs backend and frontend dependencies
3. Starts both servers in background
4. Installs Playwright browsers
5. Runs the human crawler
6. Generates a summary report
7. Uploads artifacts (trace, screenshots, reports)

**Triggers**:
- `pull_request`: Runs on every PR
- `workflow_dispatch`: Manual trigger from GitHub Actions UI

### Artifacts

After each run, artifacts are saved to `frontend/tests/artifacts/`:

- **`trace.zip`**: Playwright trace file (open with `npx playwright show-trace trace.zip`)
- **`report.json`**: JSON report with metrics and errors
- **`FAIL-*.png`**: Screenshots captured on failures

## Human Simulation Features

The crawler mimics realistic user behavior:

### Mouse Movement
- Multi-step jittered movements to elements
- Random micro-adjustments along the path
- Natural acceleration/deceleration

### Timing
- Random pauses between actions (40-140ms default)
- Variable typing speeds (50-150ms per character)
- Smooth scrolling with delays

### Safety Checks
When `SAFE_MODE=true`, the crawler:
- Skips buttons matching destructive patterns:
  - `delete`, `remove`, `drop`, `panic`
  - `trade`, `order`, `sell`, `buy`
- Logs skipped actions for transparency

### Navigation Strategy
1. Attempts to click visible navigation elements (buttons/links)
2. Falls back to direct URL navigation if elements not found
3. Handles modals and toasts automatically
4. Tests search/input fields when available

## Success Criteria

The verification passes when:
- ✅ Backend health check returns `{ok: true}`
- ✅ OpenAPI spec contains ≥ MIN_OPENAPI_PATHS paths
- ✅ No GET endpoints return 5xx status codes
- ✅ No console errors detected (after filtering benign errors)
- ✅ All specified routes are accessible

## Failure Scenarios

The crawler fails if:
- ❌ OpenAPI paths < MIN_OPENAPI_PATHS
- ❌ Any GET endpoint returns 500, 501, 502, 503, 504
- ❌ JavaScript errors logged to console
- ❌ Required page elements missing (header, main, nav)

## Console Error Filtering

To reduce false positives, the following errors are ignored:
- Stream/connection errors (expected in dev mode)
- 404 resource errors (missing assets)
- CORS policy blocks (browser security)
- Stack trace lines (noise after main error)

## Debugging

### View Playwright Trace
```bash
npx playwright show-trace frontend/tests/artifacts/trace.zip
```

### Examine Report
```bash
cat frontend/tests/artifacts/report.json | jq
```

### Check Screenshots
Failed pages automatically save screenshots to `frontend/tests/artifacts/FAIL-*.png`

### Verbose Output
The crawler logs progress to stdout:
```
[CRAWLER] Starting human E2E verification...
[CRAWLER] UI_URL: http://localhost:5173
[CRAWLER] API_URL: http://localhost:8000
[CRAWLER] ✓ API health check passed
[CRAWLER] OpenAPI paths count: 123
[CRAWLER] ✓ Visited /markets
```

## Extending the Crawler

### Add New Routes
Edit `verify.crawl.mjs` line 20:
```javascript
const ROUTES = ["/", "/markets", "/signals", "/news", "/chat", "/admin", "/your-route"];
```

### Customize Interactions
Modify the `runUIFlow()` function to add:
- Form submissions
- Filter selections
- Modal interactions
- Complex workflows

### Adjust Timing
Change pause durations:
```javascript
await humanPause(min, max);  // milliseconds
```

### Add Custom Checks
Extend `visitPage()` to verify:
- Specific text content
- Data visualizations
- Real-time updates

## Known Limitations

1. **Build Issues**: Google Fonts fetch may fail in restricted environments
2. **CORS**: Local testing may encounter CORS issues (filtered by default)
3. **Dependencies**: Full backend functionality requires all Python dependencies
4. **Timing**: Slow networks may cause timeouts (increase timeout values)
5. **State**: No authentication/session management (stateless crawling)

## Maintenance

### Updating Playwright
```bash
cd frontend
npm install @playwright/test@latest
npm run playwright:install
```

### Modifying Thresholds
Update MIN_OPENAPI_PATHS in:
1. Local: Environment variable
2. CI: `.github/workflows/verify-e2e.yml` (line 99)

### Adding Safety Patterns
Edit line 85 in `verify.crawl.mjs`:
```javascript
const destructivePattern = /delete|remove|your-pattern/i;
```

## Contributing

When adding new features or pages:
1. Add routes to `ROUTES` array
2. Update navigation labels in `routeLabels`
3. Test locally before committing
4. Verify CI workflow passes
5. Check artifacts for unexpected errors

## Support

For issues or questions:
1. Check GitHub Actions logs for detailed error messages
2. Download and examine trace files
3. Review console errors in report.json
4. Verify backend/frontend are accessible manually
