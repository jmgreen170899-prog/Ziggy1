# API Smoke Test Suite

## Overview

Feature-level smoke tests for each API domain in the ZiggyAI backend. These tests verify that endpoints return proper status codes, response structures, and maintain key invariants.

## Test Organization

Tests are organized by domain/feature area:

- **`test_trading.py`** - Trading endpoints (market risk, backtesting)
- **`test_screener.py`** - Market screening and regime detection
- **`test_cognitive.py`** - Cognitive/decision enhancement, market brain
- **`test_paper_lab.py`** - Paper trading runs and portfolio management
- **`test_chat.py`** - Chat/LLM completion and configuration
- **`test_core.py`** - Core endpoints (health, RAG, tasks)
- **`test_news_alerts.py`** - News sentiment and alert management

## Test Philosophy

These tests follow the Phase 3 guidelines:

1. **Realistic Payloads**: Use example data from Pydantic schemas
2. **Status Code Checking**: Assert on specific codes, not just 200
3. **Response Invariants**: Verify key fields and value constraints
4. **Fast & Independent**: No external dependencies, suitable for CI
5. **Contract Testing**: Act as contracts for UI and future refactors

## Running Tests

### Run All Smoke Tests

```bash
cd backend
pytest tests/test_api_smoke/ -v
```

### Run Specific Domain

```bash
# Trading tests only
pytest tests/test_api_smoke/test_trading.py -v

# Screener tests only
pytest tests/test_api_smoke/test_screener.py -v

# Chat tests only
pytest tests/test_api_smoke/test_chat.py -v
```

### Run with Coverage

```bash
pytest tests/test_api_smoke/ --cov=app.api --cov-report=term-missing
```

## Test Structure

Each test module follows this pattern:

```python
@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


def test_endpoint_name(client):
    """Test description"""
    response = client.get("/endpoint")
    
    # Status code check
    assert response.status_code == 200
    
    # Response structure check
    data = response.json()
    assert "key_field" in data
    
    # Type checks
    assert isinstance(data["key_field"], str)
    
    # Value invariants
    assert data["some_value"] > 0
```

## What We Test

### 1. Status Codes
- Not just 200 OK
- Expected error codes (400, 422, 500, 501)
- Proper HTTP method support

### 2. Response Structure
- Required fields present
- Correct types (from Phase 1 models)
- Nested structure validation

### 3. Value Invariants
- Numeric ranges (e.g., scores in [-1, 1])
- Required enumerations
- Non-negative values where applicable

### 4. Error Handling
- Standardized error format (detail, code, meta)
- Graceful handling of invalid inputs
- Proper validation errors

### 5. Backward Compatibility
- Deprecated endpoints still work
- Marked as deprecated in OpenAPI

## Integration with Phase 1 & 2

These tests validate the work from previous phases:

### Phase 1 Validation
- Response models are properly used
- Deprecated endpoints are marked
- Error responses follow standardized format
- All endpoints have concrete schemas

### Phase 2 Validation
- Generated TypeScript types match responses
- API client methods work correctly
- Contract alignment between backend/frontend

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Run API Smoke Tests
  run: |
    cd backend
    pytest tests/test_api_smoke/ -v --tb=short
```

## Expected Behavior

### When Services Are Available
- Tests pass with 200 status codes
- Response structures are validated
- Invariants are checked

### When Services Are Unavailable
- Tests accept 501 (Not Implemented)
- Tests accept 500 (Service Unavailable)
- Tests remain fast (no timeouts)

## Test Coverage by Domain

| Domain | Endpoints Tested | Key Features |
|--------|-----------------|--------------|
| Trading | 7 | Risk metrics, backtesting, health |
| Screener | 8 | Scanning, presets, regime summary |
| Cognitive | 6 | Decision enhancement, learning |
| Paper Lab | 7 | Run lifecycle, trades, portfolio |
| Chat | 10 | Completion, health, config |
| Core | 11 | Health, RAG, tasks, ingest |
| News/Alerts | 12 | Sentiment, alerts lifecycle |

**Total: 61 smoke tests across 7 domains**

## Maintenance

### Adding New Tests

1. Create test in appropriate domain file
2. Follow naming convention: `test_<feature>_<aspect>`
3. Include docstring explaining what's tested
4. Check status codes, types, and invariants
5. Use realistic example data

### Updating for New Endpoints

When adding new endpoints:

1. Add test to appropriate domain file
2. Use Phase 1 response models
3. Verify OpenAPI schema registration
4. Test both success and error cases

## Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/test_api_smoke/test_trading.py -vv

# Run specific test
pytest tests/test_api_smoke/test_trading.py::test_market_risk_lite -v

# Show full error output
pytest tests/test_api_smoke/ -v --tb=long

# Stop on first failure
pytest tests/test_api_smoke/ -x
```

## Related Documentation

- [Phase 1 & 2 Complete Summary](../../../PHASE_1_AND_2_COMPLETE.md)
- [API Client README](../../../frontend/API_CLIENT_README.md)
- [Backend Models](../../app/models/)
- [Route Definitions](../../app/api/)

## Success Criteria

✅ All tests pass with services available  
✅ Tests handle unavailable services gracefully  
✅ Fast execution (< 5 seconds total)  
✅ No flaky tests  
✅ Clear failure messages  
✅ Independent test execution  

---

**Phase 3 - Feature-level tests per domain** ✅  
**Tests act as contracts for UI and future refactors**
