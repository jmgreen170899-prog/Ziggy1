"""
Runtime Route Wiring Tests

Verifies that:
1. OpenAPI schema is available and contains 175+ paths
2. All GET endpoints return non-500 status codes (smoke test)
3. Well-known health endpoints return 200
"""

import pytest
from fastapi.testclient import TestClient


def test_openapi_available():
    """Verify OpenAPI schema is available"""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    assert response.status_code == 200, "OpenAPI schema should be available"
    assert response.headers["content-type"] == "application/json"


def test_openapi_has_minimum_paths():
    """Verify OpenAPI schema contains at least 175 paths"""
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    openapi_schema = response.json()
    
    paths = openapi_schema.get("paths", {})
    path_count = len(paths)
    
    assert path_count >= 175, (
        f"Expected at least 175 paths in OpenAPI schema, "
        f"but found only {path_count}. Routes may not be properly wired."
    )


def test_smoke_get_endpoints():
    """Smoke test all GET endpoints without path parameters"""
    from app.main import app
    
    client = TestClient(app)
    
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_schema = response.json()
    
    paths = openapi_schema.get("paths", {})
    
    # Track results
    tested = []
    skipped = []
    errors = []
    
    for path, methods in paths.items():
        # Only test GET methods
        if "get" not in methods:
            continue
        
        # Skip paths with path parameters (unless they're simple)
        if "{" in path:
            # Could potentially test with sample values, but skip for now
            skipped.append({
                "path": path,
                "reason": "Has path parameters"
            })
            continue
        
        # Skip paths that require authentication (we can tell from certain patterns)
        if any(keyword in path.lower() for keyword in ["/admin", "/private"]):
            skipped.append({
                "path": path,
                "reason": "Appears to require authentication"
            })
            continue
        
        # Test the endpoint
        try:
            response = client.get(path)
            
            # We allow 401 (unauthorized), 403 (forbidden), 404 (not found), 429 (rate limit)
            # But never 500 (server error)
            if response.status_code >= 500:
                errors.append({
                    "path": path,
                    "status_code": response.status_code,
                    "error": f"Returned {response.status_code} (server error)"
                })
            else:
                tested.append({
                    "path": path,
                    "status_code": response.status_code
                })
        
        except Exception as e:
            errors.append({
                "path": path,
                "status_code": None,
                "error": str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"Smoke Test Summary:")
    print(f"  Tested: {len(tested)}")
    print(f"  Skipped: {len(skipped)}")
    print(f"  Errors: {len(errors)}")
    print(f"{'='*80}")
    
    if skipped:
        print(f"\nSkipped endpoints ({len(skipped)}):")
        for item in skipped[:10]:  # Show first 10
            print(f"  {item['path']}: {item['reason']}")
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more")
    
    if errors:
        print(f"\n❌ Endpoints with errors ({len(errors)}):")
        for item in errors:
            status = item['status_code'] if item['status_code'] else 'N/A'
            print(f"  {item['path']}: {status} - {item['error']}")
    
    # Assert no server errors
    assert len(errors) == 0, (
        f"Found {len(errors)} endpoints with 5xx errors or exceptions. "
        f"All endpoints should return 2xx, 4xx, but never 5xx."
    )


def test_health_endpoints():
    """Test well-known health endpoints return 200"""
    from app.main import app
    
    client = TestClient(app)
    
    # Get OpenAPI schema to see what's available
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # Well-known health endpoints
    health_endpoints = [
        "/health",
        "/trade/health",
        "/signals/status",
        "/chat/health",
        "/cognitive/health",
        "/feedback/health",
        "/screener/health",
    ]
    
    tested = []
    failed = []
    
    for endpoint in health_endpoints:
        # Check if endpoint exists
        if endpoint not in paths:
            continue
        
        # Test it
        response = client.get(endpoint)
        
        if response.status_code == 200:
            tested.append(endpoint)
        else:
            failed.append({
                "endpoint": endpoint,
                "status_code": response.status_code
            })
    
    print(f"\n{'='*80}")
    print(f"Health Endpoints:")
    print(f"  Passed: {len(tested)}")
    print(f"  Failed: {len(failed)}")
    print(f"{'='*80}")
    
    if tested:
        print(f"\n✅ Working health endpoints:")
        for endpoint in tested:
            print(f"  {endpoint}")
    
    if failed:
        print(f"\n❌ Failed health endpoints:")
        for item in failed:
            print(f"  {item['endpoint']}: {item['status_code']}")
    
    # At least /health should work
    assert "/health" in tested, "The main /health endpoint should return 200"


def test_representative_routes_no_500():
    """Test that representative routes from different namespaces don't 500"""
    from app.main import app
    
    client = TestClient(app)
    
    # Representative routes to test (ones that are likely to exist and not require auth)
    test_routes = [
        ("/openapi.json", "GET"),
        ("/docs", "GET"),
        ("/health", "GET"),
    ]
    
    errors = []
    
    for path, method in test_routes:
        try:
            if method == "GET":
                response = client.get(path)
            else:
                continue  # Skip non-GET for now
            
            if response.status_code >= 500:
                errors.append({
                    "path": path,
                    "method": method,
                    "status_code": response.status_code
                })
        except Exception as e:
            errors.append({
                "path": path,
                "method": method,
                "error": str(e)
            })
    
    assert len(errors) == 0, (
        f"Found {len(errors)} representative routes returning 5xx: {errors}"
    )
