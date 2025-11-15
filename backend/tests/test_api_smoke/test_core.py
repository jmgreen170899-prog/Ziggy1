"""
Core Domain Smoke Tests

Tests for core/RAG endpoints:
- Health checks
- RAG query
- Ingest (web, PDF)
- Task management
- Vector store operations
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_core_health_basic(client):
    """Test basic health endpoint"""
    response = client.get("/health")

    assert response.status_code == 200, "Health endpoint should return 200"

    data = response.json()
    assert "ok" in data, "Health should have 'ok' field"
    assert isinstance(data["ok"], bool), "ok should be boolean"


def test_core_health_detailed(client):
    """Test detailed health endpoint"""
    response = client.get("/health/detailed")

    assert response.status_code == 200, "Detailed health should return 200"

    data = response.json()
    assert "status" in data, "Should have status"
    assert "details" in data, "Should have details"
    assert isinstance(data["details"], dict), "Details should be a dict"

    # Check details structure
    details = data["details"]
    assert (
        "service" in details or "total_routes" in details
    ), "Details should have service info"


def test_core_health_check(client):
    """Test core health with dependencies"""
    response = client.get("/api/core/health")

    assert response.status_code == 200, "Core health should return 200"

    data = response.json()
    assert "status" in data, "Should have status"
    assert "details" in data, "Should have details dict"

    details = data["details"]
    assert isinstance(details, dict), "Details should be a dict"

    # Should report on dependencies
    assert "fastapi" in details, "Should report FastAPI status"


def test_rag_query_basic(client):
    """Test basic RAG query"""
    payload = {
        "query": "What is machine learning?",
        "top_k": 5,
    }

    response = client.post("/api/query", json=payload)

    # Status: 200 if RAG available, 501 if not
    assert response.status_code in [200, 501], "RAG query should return 200 or 501"

    if response.status_code == 200:
        data = response.json()

        # Check Phase 1 QueryResponse structure
        assert "answer" in data, "Response should have answer"
        assert "citations" in data, "Response should have citations"
        assert "contexts" in data, "Response should have contexts"

        # Type checks
        assert isinstance(data["answer"], str), "Answer should be string"
        assert isinstance(data["citations"], list), "Citations should be list"
        assert isinstance(data["contexts"], list), "Contexts should be list"


def test_rag_query_empty(client):
    """Test RAG query with empty query"""
    payload = {
        "query": "",
    }

    response = client.post("/api/query", json=payload)

    # Should reject empty query
    assert response.status_code in [400, 422], "Empty query should return 400 or 422"


def test_ingest_web_basic(client):
    """Test web content ingestion"""
    payload = {
        "query": "Python programming",
        "max_results": 3,
    }

    response = client.post("/api/ingest/web", json=payload)

    # Status: 200 if available, 501 if not
    assert response.status_code in [
        200,
        501,
        502,
    ], "Web ingest should return valid status"

    if response.status_code == 200:
        data = response.json()

        # Check WebIngestResponse structure
        assert "chunks_indexed" in data, "Should report chunks indexed"
        assert isinstance(data["chunks_indexed"], int), "Chunks should be int"
        assert data["chunks_indexed"] >= 0, "Chunks should be non-negative"


def test_vector_store_reset(client):
    """Test vector store reset endpoint"""
    response = client.post("/api/reset")

    # Status: 200 if available, 501 if not
    assert response.status_code in [200, 501], "Reset should return valid status"

    if response.status_code == 200:
        data = response.json()

        # Check ResetResponse structure
        assert "status" in data, "Should have status"
        assert "message" in data, "Should have message"
        assert isinstance(data["status"], str), "Status should be string"
        assert isinstance(data["message"], str), "Message should be string"


def test_task_list(client):
    """Test listing scheduled tasks"""
    response = client.get("/api/tasks")

    # Status: 200 if available, 501 if not
    assert response.status_code in [200, 501], "Task list should return valid status"

    if response.status_code == 200:
        data = response.json()

        # Check TaskListResponse structure
        assert "jobs" in data, "Should have jobs list"
        assert isinstance(data["jobs"], list), "Jobs should be a list"


def test_task_schedule(client):
    """Test scheduling a task"""
    payload = {
        "topic": "test topic",
        "cron": "0 9 * * *",
    }

    response = client.post("/api/tasks/watch", json=payload)

    # Status: 200 if available, 501 if not
    assert response.status_code in [
        200,
        501,
    ], "Task schedule should return valid status"

    if response.status_code == 200:
        data = response.json()

        # Check TaskScheduleResponse structure
        assert "status" in data, "Should have status"
        assert "job_id" in data, "Should have job_id"
        assert "topic" in data, "Should have topic"
        assert "cron" in data, "Should have cron"

        # Value checks
        assert data["topic"] == "test topic", "Topic should match"
        assert data["cron"] == "0 9 * * *", "Cron should match"


def test_task_cancel(client):
    """Test cancelling a task"""
    # First schedule a task
    schedule_response = client.post(
        "/api/tasks/watch",
        json={
            "topic": "test cancel",
            "cron": "0 0 * * *",
        },
    )

    job_id = None
    if schedule_response.status_code == 200:
        data = schedule_response.json()
        job_id = data.get("job_id")

    # Try to cancel
    if job_id:
        cancel_response = client.delete(
            "/api/tasks",
            json={
                "job_id": job_id,
            },
        )

        assert cancel_response.status_code in [
            200,
            404,
        ], "Cancel should return 200 or 404"

        if cancel_response.status_code == 200:
            data = cancel_response.json()
            assert "status" in data, "Should have status"
            assert "job_id" in data, "Should have job_id"


def test_rag_citation_structure(client):
    """Test RAG citations have proper structure"""
    payload = {
        "query": "Test query",
        "top_k": 3,
    }

    response = client.post("/api/query", json=payload)

    if response.status_code == 200:
        data = response.json()

        citations = data.get("citations", [])
        for citation in citations:
            assert isinstance(citation, dict), "Citation should be a dict"

            # Check Citation structure from Phase 1
            if "url" in citation:
                assert isinstance(
                    citation["url"], (str, type(None))
                ), "URL should be string or null"
            if "score" in citation:
                assert isinstance(
                    citation["score"], (int, float)
                ), "Score should be numeric"


def test_core_endpoints_response_models(client):
    """Verify core endpoints use standardized response models"""
    # Test that responses match Phase 1 models

    # Health should return AckResponse
    health = client.get("/health")
    if health.status_code == 200:
        data = health.json()
        assert "ok" in data, "AckResponse should have 'ok'"

    # Detailed health should return HealthResponse
    detailed = client.get("/health/detailed")
    if detailed.status_code == 200:
        data = detailed.json()
        assert (
            "status" in data and "details" in data
        ), "HealthResponse should have status and details"

    # Core health should return CoreHealthResponse
    core = client.get("/api/core/health")
    if core.status_code == 200:
        data = core.json()
        assert (
            "status" in data and "details" in data
        ), "CoreHealthResponse should have status and details"


def test_core_error_format(client):
    """Test that errors follow standardized format"""
    # Try an invalid endpoint
    response = client.get("/api/nonexistent-endpoint-12345")

    assert response.status_code == 404, "Nonexistent endpoint should return 404"

    data = response.json()

    # Check ErrorResponse structure from Phase 1
    assert "detail" in data, "Error should have detail"
    assert "code" in data, "Error should have code"
    assert "meta" in data, "Error should have meta"

    # Type checks
    assert isinstance(data["detail"], str), "Detail should be string"
    assert isinstance(data["code"], str), "Code should be string"
    assert isinstance(data["meta"], dict), "Meta should be dict"


def test_core_endpoints_availability(client):
    """Verify core endpoints are registered"""
    response = client.get("/openapi.json")

    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})

        # Check for required core endpoints
        assert "/health" in paths, "Should have /health"
        assert "/health/detailed" in paths, "Should have /health/detailed"

        # Check for API endpoints
        api_paths = [p for p in paths.keys() if p.startswith("/api")]
        assert len(api_paths) > 0, "Should have API endpoints"
