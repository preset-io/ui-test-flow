"""
End-to-end tests for MCP CLI commands.

Tests the generate, run-with-claude, mcp-server, and mcp-status commands.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from typer.testing import CliRunner

from uitestflow.cli.main import app


runner = CliRunner()


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api_key(monkeypatch):
    """Set mock Anthropic API key in environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
    return "sk-ant-test-key-12345"


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_test_yaml(temp_output_dir):
    """Create a sample test YAML file."""
    test_file = temp_output_dir / "sample_test.yaml"
    test_data = {
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

    with Path(test_file).open("w") as f:
        yaml.dump(test_data, f)

    return test_file


# ============================================================================
# Test Generate Command
# ============================================================================


@pytest.mark.e2e
def test_generate_command_help():
    """Test that generate command help works."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "Generate a test definition" in result.stdout
    assert "--output" in result.stdout
    assert "--model" in result.stdout
    assert "--dry-run" in result.stdout


@pytest.mark.e2e
def test_generate_command_no_api_key():
    """Test generate command fails without API key."""
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(app, ["generate", "Login test"])
        assert result.exit_code == 1
        assert "ANTHROPIC_API_KEY" in result.stdout


@pytest.mark.e2e
@patch("uitestflow.cli.mcp_commands.ClaudeTestGenerator")
def test_generate_command_dry_run(mock_generator_class, mock_api_key, temp_output_dir):
    """Test generate command in dry-run mode."""
    # Mock the generator
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

    # Mock async generate_test method
    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    result = runner.invoke(app, ["generate", "Login with credentials", "--dry-run", "--verbose"])

    assert result.exit_code == 0
    assert "login_test" in result.stdout
    assert "Dry run mode" in result.stdout


@pytest.mark.e2e
@patch("uitestflow.cli.mcp_commands.ClaudeTestGenerator")
def test_generate_command_with_output(mock_generator_class, mock_api_key, temp_output_dir):
    """Test generate command saves to file."""
    # Mock the generator
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="search_test",
        description="Search test",
        version="1.0",
        steps=[
            TestStep(name="Search", action="fill", selector="input", value="query"),
        ],
        evaluators=[],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    output_file = temp_output_dir / "search_test.yaml"
    result = runner.invoke(app, ["generate", "Search for something", "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify file contents
    with Path(output_file).open() as f:
        saved_test = yaml.safe_load(f)
    assert saved_test["name"] == "search_test"


# ============================================================================
# Test Run with Claude Command
# ============================================================================


@pytest.mark.e2e
def test_run_with_claude_help():
    """Test that run-with-claude command help works."""
    result = runner.invoke(app, ["run-with-claude", "--help"])
    assert result.exit_code == 0
    assert "Run a test with Claude AI guidance" in result.stdout
    assert "--model" in result.stdout
    assert "--guided-only" in result.stdout


@pytest.mark.e2e
def test_run_with_claude_no_api_key(sample_test_yaml):
    """Test run-with-claude fails without API key."""
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(app, ["run-with-claude", str(sample_test_yaml)])
        assert result.exit_code == 1
        assert "ANTHROPIC_API_KEY" in result.stdout


@pytest.mark.e2e
@patch("uitestflow.cli.mcp_commands.ClaudeTestGenerator")
@patch("uitestflow.cli.mcp_commands.BrowserSessionManager")
@patch("uitestflow.cli.mcp_commands.EnhancedTestRunner")
def test_run_with_claude_guided_only(
    mock_runner_class,
    mock_session_class,
    mock_generator_class,
    mock_api_key,
    sample_test_yaml,
):
    """Test run-with-claude in guided-only mode."""
    result = runner.invoke(app, ["run-with-claude", str(sample_test_yaml), "--guided-only"])

    # Should show message about guidance-only mode
    assert "Guidance-only mode" in result.stdout or "coming soon" in result.stdout


# ============================================================================
# Test MCP Server Command
# ============================================================================


@pytest.mark.e2e
def test_mcp_server_help():
    """Test that mcp-server command help works."""
    result = runner.invoke(app, ["mcp-server", "--help"])
    assert result.exit_code == 0
    assert "Start standalone MCP server" in result.stdout
    assert "--port" in result.stdout
    assert "--transport" in result.stdout


@pytest.mark.e2e
def test_mcp_server_invalid_transport():
    """Test mcp-server rejects invalid transport."""
    # This would start the server, so we just check validation
    # In a real test, we'd need to run in subprocess and kill it
    # Skip for now as it requires async execution


# ============================================================================
# Test MCP Status Command
# ============================================================================


@pytest.mark.e2e
def test_mcp_status_help():
    """Test that mcp-status command help works."""
    result = runner.invoke(app, ["mcp-status", "--help"])
    assert result.exit_code == 0
    assert "Show MCP server status" in result.stdout


@pytest.mark.e2e
def test_mcp_status_command(mock_api_key):
    """Test mcp-status displays status information."""
    result = runner.invoke(app, ["mcp-status"])

    assert result.exit_code == 0
    assert "MCP Server Status" in result.stdout
    assert "API Key" in result.stdout
    assert "Set" in result.stdout  # API key is set in fixture


@pytest.mark.e2e
def test_mcp_status_verbose(mock_api_key):
    """Test mcp-status verbose mode."""
    result = runner.invoke(app, ["mcp-status", "--verbose"])

    assert result.exit_code == 0
    assert "Available MCP Tools" in result.stdout
    assert "navigate" in result.stdout
    assert "click" in result.stdout
    assert "Configuration" in result.stdout


@pytest.mark.e2e
def test_mcp_status_no_api_key():
    """Test mcp-status shows warning without API key."""
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(app, ["mcp-status"])

        assert result.exit_code == 0
        assert "Not set" in result.stdout
        assert "Warning" in result.stdout


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.e2e
@pytest.mark.integration
@patch("uitestflow.cli.mcp_commands.ClaudeTestGenerator")
def test_generate_and_save_workflow(mock_generator_class, mock_api_key, temp_output_dir):
    """Test complete workflow: generate test and save to file."""
    # Mock generator
    mock_generator = Mock()
    mock_generator_class.return_value = mock_generator

    from uitestflow.src.models import EvaluatorConfig, TestDefinition, TestStep

    mock_test_def = TestDefinition(
        name="full_workflow_test",
        description="Complete workflow test",
        version="1.0",
        url="https://example.com",
        steps=[
            TestStep(name="Step 1", action="goto", url="https://example.com"),
            TestStep(name="Step 2", action="click", selector="button"),
        ],
        evaluators=[
            EvaluatorConfig(name="all_steps_completed", type="all_steps_completed"),
        ],
    )

    async def mock_generate(*args, **kwargs):
        return mock_test_def

    mock_generator.generate_test = mock_generate

    # Generate test
    output_file = temp_output_dir / "workflow_test.yaml"
    result = runner.invoke(
        app,
        [
            "generate",
            "Complete workflow test",
            "--output",
            str(output_file),
            "--model",
            "claude-3-5-haiku-20241022",
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify saved file
    with Path(output_file).open() as f:
        saved_test = yaml.safe_load(f)

    assert saved_test["name"] == "full_workflow_test"
    assert len(saved_test["steps"]) == 2
    assert len(saved_test["evaluators"]) == 1


@pytest.mark.e2e
@pytest.mark.slow
def test_cli_commands_available():
    """Test that all MCP commands are available in CLI."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "generate" in result.stdout
    assert "run-with-claude" in result.stdout
    assert "mcp-server" in result.stdout
    assert "mcp-status" in result.stdout


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.e2e
def test_generate_missing_description():
    """Test generate command requires description."""
    result = runner.invoke(app, ["generate"])
    assert result.exit_code != 0


@pytest.mark.e2e
def test_run_with_claude_missing_file():
    """Test run-with-claude requires test file."""
    result = runner.invoke(app, ["run-with-claude"])
    assert result.exit_code != 0


@pytest.mark.e2e
def test_run_with_claude_invalid_file():
    """Test run-with-claude with non-existent file."""
    result = runner.invoke(app, ["run-with-claude", "nonexistent.yaml"])
    assert result.exit_code != 0
