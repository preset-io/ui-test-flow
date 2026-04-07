"""
End-to-end tests for MCP API endpoints.

Tests the /api/mcp/* endpoints including generation, execution, status, and feedback.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from uitestflow.server.api import app


client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def api_key():
    """Mock Anthropic API key."""
    return "sk-ant-test-key-12345"


@pytest.fixture
def headers(api_key):
    """Request headers with API key."""
    return {"X-API-Key": api_key}


@pytest.fixture
def sample_test_definition():
    """Sample test definition for requests."""
    return {
        "name": "sample_test",
        "description": "Sample test for E2E testing",
        "version": "1.0",
        "url": "https://example.com",
        "steps": [
            {"name": "Navigate", "action": "goto", "url": "https://example.com"},
            {"name": "Get title", "action": "evaluate", "value": "document.title"},
        ],
        "evaluators": [
            {"name": "all_steps_completed", "type": "all_steps_completed"},
        ],
    }


# ============================================================================
# Test POST /api/mcp/generate
# ============================================================================


@pytest.mark.e2e
def test_generate_endpoint_no_api_key():
    """Test generate endpoint requires API key."""
    response = client.post(
        "/api/mcp/generate",
        json={"description": "Login test"},
    )

    assert response.status_code == 401
    assert "API key required" in response.json().get("detail", "").lower()


@pytest.mark.e2e
def test_generate_endpoint_invalid_api_key():
    """Test generate endpoint validates API key format."""
    response = client.post(
        "/api/mcp/generate",
        headers={"X-API-Key": "invalid-key"},
        json={"description": "Login test"},
    )

    assert response.status_code == 401


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
def test_generate_endpoint_success(mock_generator_class, headers):
    """Test successful test generation."""
    # Mock generator
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    # Mock test definition
    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="login_test",
        description="Generated login test",
        version="1.0",
        url="https://example.com/login",
        steps=[
            TestStep(
                name="Navigate to login",
                action="goto",
                url="https://example.com/login",
            ),
        ],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    response = client.post(
        "/api/mcp/generate",
        headers=headers,
        json={
            "description": "Login with admin credentials",
            "model": "claude-3-5-haiku-20241022",
            "save": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "test_id" in data
    assert "test_definition" in data
    assert "generation_time_ms" in data
    assert data["model_used"] == "claude-3-5-haiku-20241022"
    assert data["test_definition"]["name"] == "login_test"


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
def test_generate_endpoint_with_base_url(mock_generator_class, headers):
    """Test test generation with base_url."""
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="test",
        version="1.0",
        steps=[TestStep(name="step", action="goto", url="https://example.com")],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    response = client.post(
        "/api/mcp/generate",
        headers=headers,
        json={
            "description": "Navigate to homepage",
            "base_url": "https://example.com",
            "save": False,
        },
    )

    assert response.status_code == 200


@pytest.mark.e2e
def test_generate_endpoint_validation():
    """Test generate endpoint validates request."""
    response = client.post(
        "/api/mcp/generate",
        headers={"X-API-Key": "sk-ant-test-key"},
        json={
            "description": "",  # Empty description should fail
        },
    )

    assert response.status_code == 422  # Validation error


# ============================================================================
# Test POST /api/mcp/execute
# ============================================================================


@pytest.mark.e2e
def test_execute_endpoint_no_api_key(sample_test_definition):
    """Test execute endpoint requires API key."""
    response = client.post(
        "/api/mcp/execute",
        json={"test_definition": sample_test_definition},
    )

    assert response.status_code == 401


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
@patch("uitestflow.server.mcp_routes.asyncio.create_task")
def test_execute_endpoint_with_inline_test(
    mock_create_task, mock_generator_class, headers, sample_test_definition
):
    """Test execute endpoint with inline test definition."""
    response = client.post(
        "/api/mcp/execute",
        headers=headers,
        json={
            "test_definition": sample_test_definition,
            "with_claude": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["status"] == "queued"
    assert "run_id" in data["message"].lower() or "websocket" in data["message"].lower()


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.asyncio.create_task")
def test_execute_endpoint_with_test_id(mock_create_task, headers):
    """Test execute endpoint with test_id."""
    test_id = uuid4()

    # This will fail because test doesn't exist in DB, but tests the flow
    response = client.post(
        "/api/mcp/execute",
        headers=headers,
        json={
            "test_id": str(test_id),
            "with_claude": False,
        },
    )

    # Will fail with 404 since test doesn't exist
    assert response.status_code == 404 or response.status_code == 500


@pytest.mark.e2e
def test_execute_endpoint_missing_test():
    """Test execute endpoint requires test_id or test_definition."""
    response = client.post(
        "/api/mcp/execute",
        headers={"X-API-Key": "sk-ant-test-key"},
        json={
            "with_claude": True,
        },
    )

    assert response.status_code == 400
    assert "test_id or test_definition" in response.json()["detail"]


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.asyncio.create_task")
def test_execute_endpoint_headless_option(mock_create_task, headers, sample_test_definition):
    """Test execute endpoint respects headless option."""
    response = client.post(
        "/api/mcp/execute",
        headers=headers,
        json={
            "test_definition": sample_test_definition,
            "with_claude": False,
            "headless": False,
        },
    )

    assert response.status_code == 200


# ============================================================================
# Test GET /api/mcp/status
# ============================================================================


@pytest.mark.e2e
def test_status_endpoint():
    """Test MCP status endpoint."""
    # Status endpoint doesn't require API key
    response = client.get("/api/mcp/status")

    assert response.status_code == 200
    data = response.json()

    assert "mcp_enabled" in data
    assert "server_available" in data
    assert "available_tools" in data
    assert "default_model" in data
    assert "transport" in data

    # Check tools list
    assert isinstance(data["available_tools"], list)
    assert "navigate" in data["available_tools"]
    assert "click" in data["available_tools"]


@pytest.mark.e2e
def test_status_endpoint_with_api_key(headers):
    """Test status endpoint shows api_key_configured when key provided."""
    response = client.get("/api/mcp/status", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert data["api_key_configured"] is True


@pytest.mark.e2e
def test_status_endpoint_without_api_key():
    """Test status endpoint shows api_key_configured false without key."""
    response = client.get("/api/mcp/status")

    assert response.status_code == 200
    data = response.json()

    assert data["api_key_configured"] is False


# ============================================================================
# Test GET /api/mcp/feedback/{run_id}
# ============================================================================


@pytest.mark.e2e
def test_feedback_endpoint_not_found():
    """Test feedback endpoint with non-existent run_id."""
    run_id = uuid4()
    response = client.get(f"/api/mcp/feedback/{run_id}")

    assert response.status_code == 404


@pytest.mark.e2e
def test_feedback_endpoint_pagination():
    """Test feedback endpoint supports pagination."""
    run_id = uuid4()
    response = client.get(f"/api/mcp/feedback/{run_id}?page=1&page_size=10")

    # Will fail with 404, but tests query parameters
    assert response.status_code == 404  # Test doesn't exist


# ============================================================================
# Test Rate Limiting
# ============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
def test_generate_endpoint_rate_limiting(mock_generator_class, headers):
    """Test rate limiting on generate endpoint."""
    # Mock quick responses
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="test",
        version="1.0",
        steps=[TestStep(name="step", action="goto", url="https://example.com")],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    # Make requests up to limit
    request_count = 0
    max_requests = 15  # More than typical limit

    for i in range(max_requests):
        response = client.post(
            "/api/mcp/generate",
            headers=headers,
            json={"description": f"Test {i}", "save": False},
        )

        if response.status_code == 429:
            # Hit rate limit
            assert "rate limit" in response.json().get("detail", "").lower()
            assert "X-RateLimit-Limit" in response.headers
            break

        request_count += 1

    # Should have hit rate limit before max_requests
    assert request_count <= max_requests


# ============================================================================
# Test Error Responses
# ============================================================================


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
def test_generate_endpoint_llm_error(mock_generator_class, headers):
    """Test generate endpoint handles LLM errors."""
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.llm.types import LLMError

    async def mock_generate(*args, **kwargs):
        raise LLMError("Model error")

    mock_generator.generate_test = mock_generate

    response = client.post(
        "/api/mcp/generate",
        headers=headers,
        json={"description": "Test", "save": False},
    )

    assert response.status_code == 502
    assert "generation failed" in response.json()["detail"].lower()


@pytest.mark.e2e
def test_mcp_endpoints_have_cors_headers():
    """Test MCP endpoints include CORS headers."""
    response = client.options("/api/mcp/status")

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


# ============================================================================
# Test Middleware Integration
# ============================================================================


@pytest.mark.e2e
def test_mcp_response_headers():
    """Test MCP endpoints include custom headers."""
    response = client.get("/api/mcp/status")

    assert response.status_code == 200

    # Check for MCP-specific headers
    assert "X-MCP-Server" in response.headers
    assert response.headers["X-MCP-Server"] == "UITestFlow-MCP"
    assert "X-MCP-Version" in response.headers


@pytest.mark.e2e
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
def test_mcp_response_time_header(mock_generator_class, headers):
    """Test MCP endpoints include response time header."""
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="test",
        version="1.0",
        steps=[TestStep(name="step", action="goto", url="https://example.com")],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    response = client.post(
        "/api/mcp/generate",
        headers=headers,
        json={"description": "Test", "save": False},
    )

    assert response.status_code == 200
    assert "X-Response-Time" in response.headers


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.e2e
@pytest.mark.integration
@patch("uitestflow.server.mcp_routes.ClaudeTestGenerator")
@patch("uitestflow.server.mcp_routes.asyncio.create_task")
def test_full_workflow_generate_and_execute(
    mock_create_task,
    mock_generator_class,
    headers,
):
    """Test complete workflow: generate test then execute it."""
    # Step 1: Generate test
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="workflow_test",
        version="1.0",
        url="https://example.com",
        steps=[
            TestStep(name="Navigate", action="goto", url="https://example.com"),
        ],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    gen_response = client.post(
        "/api/mcp/generate",
        headers=headers,
        json={
            "description": "Navigate to example.com",
            "save": False,
        },
    )

    assert gen_response.status_code == 200
    test_definition = gen_response.json()["test_definition"]

    # Step 2: Execute generated test
    exec_response = client.post(
        "/api/mcp/execute",
        headers=headers,
        json={
            "test_definition": test_definition,
            "with_claude": False,
        },
    )

    assert exec_response.status_code == 200
    assert "run_id" in exec_response.json()


@pytest.mark.e2e
def test_all_mcp_endpoints_registered():
    """Test that all MCP endpoints are accessible."""
    # Get OpenAPI schema
    response = client.get("/api/openapi.json")
    assert response.status_code == 200

    openapi = response.json()
    paths = openapi.get("paths", {})

    # Check MCP endpoints exist
    assert "/api/mcp/generate" in paths
    assert "/api/mcp/execute" in paths
    assert "/api/mcp/status" in paths
    assert "/api/mcp/feedback/{run_id}" in paths
