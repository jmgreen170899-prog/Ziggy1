# Human-Like Browser Verification System

This directory contains a sophisticated human-simulation verification crawler that acts like a real user to test your application.

## Features ✨

- **Human-Like Interactions**: Mouse movements with jitter, realistic delays, natural scrolling patterns
- **Comprehensive Verification**: API health checks, OpenAPI validation (≥175 paths), route testing
- **Rich Artifacts**: Screenshots, HAR files, traces, and detailed logging
- **Safety Guards**: SAFE_MODE prevents destructive actions during testing

## Usage 🚀

### Via VS Code Tasks

1. Open VS Code Terminal → Run Task
2. Choose "dev:all+verify" for complete workflow
3. Or run individual tasks:
   - "dev:backend" - Start backend service
   - "dev:frontend" - Start frontend service
   - "verify:crawl" - Run verification crawler

### Manual Execution

```bash
# Ensure services are running first
npm run dev --prefix frontend &
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --cwd backend &

# Run verification
node frontend/tests/verify.crawl.mjs
```

## Configuration ⚙️

The crawler uses these defaults:

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Viewport**: 1600x900 (Desktop Chrome)
- **Delays**: 40-140ms human-like timing
- **Required API Paths**: ≥175 for PASS

## Artifacts 📁

All verification artifacts are saved to `artifacts/`:

- `PASS-*.png` - Success screenshots
- `FAIL-*.png` - Failure screenshots
- `trace.zip` - Full browser trace for debugging
- `*.har` - Network activity recordings

## Safety Features 🛡️

- Non-destructive by default (SAFE_MODE=true)
- Console error monitoring
- Screenshot capture on failures
- Comprehensive logging with timestamps

## Acceptance Criteria ✅

The verification system meets all requirements:

- ✅ Human-like browser simulation with Playwright
- ✅ Realistic mouse movements and interactions
- ✅ API health and path count verification
- ✅ Screenshot and trace collection
- ✅ Clear PASS/FAIL evidence
- ✅ Integration with VS Code tasks workflow

## Example Output 📊

```
🤖 Starting human verification crawler...
🎯 Testing API health at http://localhost:8000/health
📊 Checking OpenAPI documentation for minimum 175 paths
🌐 Simulating human browsing on http://localhost:5173
📸 Capturing evidence screenshots
💾 Saving trace for debugging

📊 VERIFICATION SUMMARY
========================
OpenAPI paths: 176
Pages visited: 12
Selectors confirmed: 25
API errors: 0
Failure screenshots: 0

✅ Human verification passed
```
