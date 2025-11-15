# ZiggyAI Backend - Start Here

## Quick Start

### Running Tests Locally

To run tests locally with the same configuration as CI:

```bash
cd backend
PYTHONPATH=backend pytest -q -m "not slow"
```

### Environment Variables for Testing

The test suite uses several environment variables to control behavior:

```bash
# Required for test execution
PYTHONPATH=backend                    # Ensures imports work correctly

# Test database and file outputs
EVENTS_STORE_PATH=/tmp/events.jsonl  # Isolate event logs
LEARN_REPORT_PATH=/tmp/learn.json    # Isolate learning reports

# Feature flags
FEEDBACK_ENABLED=false                # Disable feedback in tests
PAPER_HEALTH_DEV_MODE=true           # Enable dev mode for paper trading
VECDB_BACKEND=memory                 # Use in-memory vector DB (no Redis/Qdrant)
RUN_LEGACY_TESTS=0                   # Skip legacy tests by default
ZIGGY_TEST_MODE=1                    # Enable test mode behaviors
```

### Running Legacy Tests

Legacy tests are marked with `@pytest.mark.legacy` and skipped by default. To run them:

```bash
cd backend
PYTHONPATH=backend RUN_LEGACY_TESTS=1 pytest -q tests/legacy/
```

## CI Stabilization Changes

### What Changed

**BOM Removal**: Removed UTF-8 BOM (Byte Order Mark) from:

- `.github/workflows/ci.yml`
- `backend/pytest.ini`
- `backend/requirements.lock`

**Dependency Cleanup**: Cleaned `backend/requirements.lock`:

- Removed duplicate entries: `slowapi==0.1.9`, `python-jose==3.5.0`
- Removed Windows-specific packages: `pywin32`, `pywin32-ctypes`, `win32_setctime`
- Maintained 186 unique, properly pinned packages

**Added Missing Types**: Tests expect these classes to be importable:

- `RegimeDetector` in `app.services.regime` - OO wrapper for regime detection
- `SignalFusionEnsemble` in `app.services.fusion.ensemble` - signal fusion with ML models
- `FeatureSet` and `FeatureComputer` in `app.services.market_brain.features` - feature computation

All classes are deterministic with no I/O operations on import or initialization.

### Import Path Consistency

**CI Configuration**: The CI workflow sets `PYTHONPATH=backend` before running tests.

**Local Development**: To match CI behavior, either:

1. **Set PYTHONPATH** (recommended):

   ```bash
   export PYTHONPATH=backend
   cd backend && pytest
   ```

2. **Or run from repository root**:
   ```bash
   cd backend
   PYTHONPATH=backend pytest -q -m "not slow"
   ```

**Note**: The `pytest.ini` currently has `pythonpath = .` which works when running from the backend directory. The CI uses `PYTHONPATH=backend` which is equivalent. Both approaches ensure imports like `from app.services.regime import RegimeDetector` work correctly.

## Project Structure

```
backend/
├── app/                      # Main application code
│   ├── services/             # Business logic services
│   │   ├── regime.py         # Regime detection
│   │   ├── fusion/           # Signal fusion
│   │   │   └── ensemble.py   # Ensemble models
│   │   └── market_brain/     # Market intelligence
│   │       └── features.py   # Feature computation
│   ├── api/                  # FastAPI routes
│   ├── models/               # Database models
│   └── core/                 # Core configuration
├── tests/                    # Test suite
│   ├── api/                  # API tests
│   ├── legacy/               # Legacy tests (skipped by default)
│   └── ...                   # Other test modules
├── pytest.ini                # Pytest configuration
├── requirements.lock         # Pinned dependencies
└── START_HERE.md            # This file
```

## Testing Guidelines

### Test Organization

- All tests must be under `backend/tests/` directory
- No root-level `test_*.py` files in backend directory
- Legacy tests go in `backend/tests/legacy/` with `@pytest.mark.legacy`

### Running Specific Test Categories

```bash
# Run all tests except slow ones (default for CI)
pytest -q -m "not slow"

# Run only fast tests
pytest -q -m "not slow and not legacy"

# Run a specific test file
pytest -q tests/test_cognitive_core.py

# Run with verbose output
pytest -v -m "not slow"
```

### Adding New Tests

1. Place test files in appropriate subdirectory under `tests/`
2. Use existing fixtures and helpers where possible
3. Mark slow tests with `@pytest.mark.slow`
4. Mark legacy tests with `@pytest.mark.legacy`
5. Ensure tests work with `PYTHONPATH=backend`

## Development Workflow

1. **Make changes** to code in `app/`
2. **Run tests locally**:
   ```bash
   cd backend
   PYTHONPATH=backend pytest -q -m "not slow"
   ```
3. **Check integrity** (after setting up the script):
   ```bash
   python scripts/check_repo_integrity.py
   ```
4. **Commit and push** - CI will run the same tests

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'app'`:

- Ensure `PYTHONPATH=backend` is set
- Or run pytest from backend directory with pytest.ini

### Tests Discovering Duplicate Files

If pytest finds duplicate test files:

- Ensure no `test_*.py` files exist in `backend/` root
- Only keep tests under `backend/tests/`

### Windows-Specific Package Errors

If you see errors about `pywin32` or similar:

- These packages were removed from `requirements.lock`
- They are Windows-only and not needed for Linux CI
- Re-run `pip install -r backend/requirements.lock`

## Additional Resources

- **CI Workflow**: `.github/workflows/ci.yml`
- **Pytest Config**: `backend/pytest.ini`
- **Dependencies**: `backend/requirements.lock`
- **Integrity Checks**: `scripts/check_repo_integrity.py` (when added)
