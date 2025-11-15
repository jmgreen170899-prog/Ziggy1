"""
Chat Domain Smoke Tests

Tests for chat/LLM endpoints:
- Chat completion
- Health checks
- Configuration
- Streaming
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app

    return TestClient(app)


def test_chat_health(client):
    """Test chat service health check"""
    response = client.get("/chat/health")

    assert response.status_code == 200, "Chat health should return 200"

    data = response.json()

    # Required fields from Phase 1
    assert "provider" in data, "Should report provider (openai or local)"
    assert "base" in data, "Should report base URL"
    assert "model" in data, "Should report model name"
    assert "ok" in data, "Should report health status"

    # Type checks
    assert isinstance(data["provider"], str), "Provider should be string"
    assert isinstance(data["base"], str), "Base URL should be string"
    assert isinstance(data["model"], str), "Model should be string"
    assert isinstance(data["ok"], bool), "Health status should be boolean"

    # Value checks
    assert data["provider"] in ["openai", "local"], "Provider should be openai or local"


def test_chat_config(client):
    """Test chat configuration endpoint"""
    response = client.get("/chat/config")

    assert response.status_code == 200, "Chat config should return 200"

    data = response.json()

    # Required fields from Phase 1
    assert "provider" in data, "Should have provider"
    assert "base" in data, "Should have base URL"
    assert "default_model" in data, "Should have default model"
    assert "timeout_sec" in data, "Should have timeout"
    assert "use_openai" in data, "Should have use_openai flag"

    # Type checks
    assert isinstance(data["provider"], str), "Provider should be string"
    assert isinstance(data["default_model"], str), "Model should be string"
    assert isinstance(data["timeout_sec"], (int, float)), "Timeout should be numeric"
    assert isinstance(data["use_openai"], bool), "use_openai should be boolean"

    # Value checks
    assert data["timeout_sec"] > 0, "Timeout should be positive"


def test_chat_completion_basic(client):
    """Test basic chat completion"""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
    }

    response = client.post("/chat/complete", json=payload)

    # Status codes: 200 if LLM available, 500/501 if not
    assert response.status_code in [
        200,
        500,
        501,
        502,
        503,
    ], "Chat completion should return valid status"

    if response.status_code == 200:
        data = response.json()

        # Should have some response structure
        assert isinstance(data, dict), "Response should be a dict"

        # Common OpenAI-compatible fields
        if "choices" in data:
            assert isinstance(data["choices"], list), "Choices should be a list"
            if len(data["choices"]) > 0:
                choice = data["choices"][0]
                assert (
                    "message" in choice or "text" in choice
                ), "Choice should have message or text"


def test_chat_completion_with_options(client):
    """Test chat completion with optional parameters"""
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ],
        "temperature": 0.7,
        "max_tokens": 50,
    }

    response = client.post("/chat/complete", json=payload)

    # Accept various responses
    assert response.status_code in [
        200,
        400,
        422,
        500,
        501,
        502,
        503,
    ], "Chat with options should be handled"

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"


def test_chat_completion_streaming_disabled(client):
    """Test chat completion with streaming disabled"""
    payload = {
        "messages": [{"role": "user", "content": "Test"}],
        "stream": False,
    }

    response = client.post("/chat/complete", json=payload)

    # Should handle non-streaming
    assert response.status_code in [
        200,
        400,
        422,
        500,
        501,
    ], "Non-streaming should be handled"


def test_chat_completion_empty_messages(client):
    """Test chat completion with empty messages"""
    payload = {
        "messages": [],
    }

    response = client.post("/chat/complete", json=payload)

    # Should reject empty messages
    assert response.status_code in [400, 422], "Empty messages should return 400 or 422"


def test_chat_completion_invalid_role(client):
    """Test chat completion with invalid role"""
    payload = {
        "messages": [{"role": "invalid", "content": "Test"}],
    }

    response = client.post("/chat/complete", json=payload)

    # Should handle gracefully
    assert response.status_code in [
        200,
        400,
        422,
        500,
    ], "Invalid role should be handled"


def test_chat_health_connectivity(client):
    """Test that health check actually tests connectivity"""
    response = client.get("/chat/health")

    assert response.status_code == 200
    data = response.json()

    # If ok is True, provider should be configured
    if data["ok"]:
        assert data["base"], "If healthy, should have base URL"
        assert data["model"], "If healthy, should have model"

    # If ok is False, should have error details
    if not data["ok"]:
        assert (
            "error" in data or "detail" in data
        ), "If unhealthy, should have error info"


def test_chat_provider_consistency(client):
    """Test that provider is consistent between config and health"""
    health_response = client.get("/chat/health")
    config_response = client.get("/chat/config")

    if health_response.status_code == 200 and config_response.status_code == 200:
        health_data = health_response.json()
        config_data = config_response.json()

        # Provider should match
        assert (
            health_data["provider"] == config_data["provider"]
        ), "Provider should be consistent"


def test_chat_completion_response_structure(client):
    """Test chat completion response has proper structure"""
    payload = {
        "messages": [{"role": "user", "content": "Say 'test'"}],
        "max_tokens": 10,
    }

    response = client.post("/chat/complete", json=payload)

    if response.status_code == 200:
        data = response.json()

        # Check for OpenAI-compatible structure
        if "choices" in data:
            choices = data["choices"]
            assert isinstance(choices, list), "Choices should be a list"

            if len(choices) > 0:
                choice = choices[0]

                # Should have message or text
                has_content = "message" in choice or "text" in choice
                assert has_content, "Choice should have content"

                # If message, check structure
                if "message" in choice:
                    message = choice["message"]
                    assert "role" in message, "Message should have role"
                    assert "content" in message, "Message should have content"


def test_chat_model_configuration(client):
    """Test that model can be specified in request"""
    payload = {
        "messages": [{"role": "user", "content": "Test"}],
        "model": "gpt-3.5-turbo",
    }

    response = client.post("/chat/complete", json=payload)

    # Should accept model parameter
    assert response.status_code in [
        200,
        400,
        422,
        500,
        501,
    ], "Model parameter should be handled"


def test_chat_endpoints_availability(client):
    """Verify chat endpoints are registered"""
    response = client.get("/openapi.json")

    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})

        # Check for chat-related paths
        chat_paths = [p for p in paths.keys() if "/chat" in p]

        assert (
            len(chat_paths) >= 2
        ), "Should have at least health and complete endpoints"

        # Check for required endpoints
        assert any(
            "/chat/health" in p for p in chat_paths
        ), "Should have health endpoint"
        assert any(
            "/chat/complete" in p for p in chat_paths
        ), "Should have complete endpoint"
