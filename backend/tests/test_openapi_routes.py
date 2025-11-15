"""Tests for OpenAPI route registration and availability.

This test module validates that:
1. All routers are properly registered in the FastAPI app
2. The OpenAPI schema is available and contains expected routes
3. Critical routes like /health are functional
4. Representative namespaces exist in the API
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_works():
    """Verify the health endpoint is available and returns expected response."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert data["ok"] is True


def test_openapi_json_available():
    """Verify OpenAPI schema endpoint is accessible."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_openapi_has_minimum_routes():
    """Verify OpenAPI schema contains at least 170 route operations."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()

    # Check that paths key exists
    assert "paths" in openapi_schema, "OpenAPI schema should have 'paths' key"

    paths = openapi_schema["paths"]
    path_count = len(paths)

    # Count total operations (method + path combinations)
    operation_count = 0
    for path, methods in paths.items():
        for method in methods:
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                operation_count += 1

    # Verify we have at least 170 operations (reasonable baseline given ~179 discovered statically)
    # Note: The original audit found 179 route definitions, but some may require optional dependencies
    assert operation_count >= 170, (
        f"Expected at least 170 route operations in OpenAPI schema, "
        f"but found only {operation_count} operations across {path_count} paths. "
        f"This suggests routers are not properly registered."
    )


def test_docs_endpoint_available():
    """Verify /docs endpoint is available (Swagger UI)."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/docs")

    # Should return HTML for docs
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_representative_namespaces_exist():
    """Verify that representative API namespaces exist in the OpenAPI schema."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()
    paths = openapi_schema["paths"]

    # Get all path prefixes
    path_list = list(paths.keys())

    # Define expected namespaces that should exist based on discovered routers
    expected_namespaces = [
        "/trade/",  # trading router
        "/signals/",  # signals router
        "/screener/",  # screener router
        "/chat/",  # chat router
        "/feedback/",  # feedback router
        "/integration/",  # integration router
    ]

    for namespace in expected_namespaces:
        matching_paths = [p for p in path_list if p.startswith(namespace)]
        assert len(matching_paths) > 0, (
            f"Expected at least one route under '{namespace}' namespace, "
            f"but none were found. Available routes: {sorted(path_list)[:10]}..."
        )


def test_health_route_in_openapi():
    """Verify /health route appears in OpenAPI schema."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()
    paths = openapi_schema["paths"]

    assert "/health" in paths, "/health route should be in OpenAPI schema"
    assert "get" in paths["/health"], "/health should support GET method"


def test_app_metadata():
    """Verify FastAPI app has correct metadata."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()

    # Check app metadata
    assert "info" in openapi_schema
    info = openapi_schema["info"]

    assert info.get("title") == "ZiggyAI", "App title should be 'ZiggyAI'"
    assert info.get("version") == "0.1.0", "App version should be '0.1.0'"


def test_no_duplicate_route_paths():
    """Verify there are no duplicate route paths with the same HTTP method."""
    from app.main import app
    from collections import defaultdict

    # Collect all route paths with their methods
    route_method_pairs = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            path = route.path
            methods = route.methods or set()
            for method in methods:
                route_method_pairs.append((path, method))

    # Check for duplicates (same path + method combo)
    unique_pairs = set(route_method_pairs)

    if len(route_method_pairs) != len(unique_pairs):
        # Find duplicates
        from collections import Counter

        pair_counts = Counter(route_method_pairs)
        duplicates = [
            (path, method) for (path, method), count in pair_counts.items() if count > 1
        ]

        pytest.fail(
            f"Found {len(duplicates)} duplicate route (path+method) combinations: {duplicates}. "
            f"This suggests routers are being registered multiple times."
        )

    # Also check that different methods on the same path is intentional (e.g., GET/POST on /api/tasks)
    # This is normal REST behavior, not a problem


def test_routes_have_tags():
    """Verify that most routes have appropriate tags for organization."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()
    paths = openapi_schema["paths"]

    routes_with_tags = 0
    total_operations = 0

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                total_operations += 1
                if operation.get("tags"):
                    routes_with_tags += 1

    # At least 40% of routes should have tags for basic organization
    # Note: Not all routes need tags, especially utility/health endpoints
    if total_operations > 0:
        tag_percentage = (routes_with_tags / total_operations) * 100
        assert tag_percentage >= 40, (
            f"Only {tag_percentage:.1f}% of routes have tags. "
            f"Expected at least 40% for basic API organization."
        )
