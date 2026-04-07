"""
Unit tests for Claude client test generation.

These tests use mocked Anthropic API responses to test the ClaudeTestGenerator
without making actual API calls.
"""

import json
from unittest.mock import Mock, patch

import pytest

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import (
    APIKeyError,
    GenerationConfig,
    ParseError,
    RateLimitError,
    ValidationError,
)


class TestClaudeTestGeneratorInitialization:
    """Test ClaudeTestGenerator initialization."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        assert generator.api_key == "sk-ant-test-key"
        assert generator.config is not None

    def test_init_with_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization with API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        generator = ClaudeTestGenerator()
        assert generator.api_key == "sk-ant-env-key"

    def test_init_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(APIKeyError) as exc_info:
            ClaudeTestGenerator()
        assert "API key is required" in str(exc_info.value)

    def test_init_with_custom_config(self) -> None:
        """Test initialization with custom configuration."""
        config = GenerationConfig(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048,
        )
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key", config=config)
        assert generator.config.model == "claude-3-5-sonnet-20241022"
        assert generator.config.temperature == 0.7
        assert generator.config.max_tokens == 2048


class TestTestGeneration:
    """Test test generation functionality."""

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock Claude API response."""
        test_definition = {
            "name": "login_test",
            "description": "Test user login",
            "version": "1.0",
            "url": "https://example.com/login",
            "steps": [
                {
                    "name": "Navigate to login",
                    "action": "goto",
                    "url": "https://example.com/login",
                },
                {
                    "name": "Fill username",
                    "action": "fill",
                    "selector": "input[name='username']",
                    "value": "admin",
                },
                {
                    "name": "Fill password",
                    "action": "fill",
                    "selector": "input[name='password']",
                    "value": "password123",
                },
                {
                    "name": "Click login",
                    "action": "click",
                    "selector": "button[type='submit']",
                },
            ],
            "evaluators": [
                {
                    "name": "All steps completed",
                    "evaluator_type": "all_steps_completed",
                    "params": {},
                }
            ],
            "timeout": 30000,
            "tags": ["login", "authentication"],
        }

        response = Mock()
        response.content = [Mock(text=json.dumps(test_definition))]
        response.model = "claude-3-5-haiku-20241022"
        response.usage = Mock(input_tokens=100, output_tokens=200)
        return response

    @pytest.mark.asyncio
    async def test_generate_simple_login_test(self, mock_response: Mock) -> None:
        """Test generating a simple login test."""
        with patch("uitestflow.llm.claude_client.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
            test_def = await generator.generate_test(
                description="Login with username 'admin' and password 'password123'"
            )

            assert test_def.name == "login_test"
            assert len(test_def.steps) == 4
            assert any(step.action == "goto" for step in test_def.steps)
            assert any(step.action == "fill" for step in test_def.steps)
            assert any(step.action == "click" for step in test_def.steps)

    @pytest.mark.asyncio
    async def test_generate_with_base_url(self, mock_response: Mock) -> None:
        """Test generating test with explicit base URL."""
        with patch("uitestflow.llm.claude_client.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
            test_def = await generator.generate_test(
                description="Login test",
                base_url="https://myapp.com",
            )

            # Verify API was called with base URL in prompt
            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs["messages"]
            assert "https://myapp.com" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_generate_with_config_override(self, mock_response: Mock) -> None:
        """Test generation with configuration override."""
        with patch("uitestflow.llm.claude_client.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
            config = GenerationConfig(temperature=0.9, max_tokens=8192)

            test_def = await generator.generate_test(
                description="Login test",
                config_override=config,
            )

            # Verify API was called with overridden config
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["temperature"] == 0.9
            assert call_args.kwargs["max_tokens"] == 8192

    @pytest.mark.asyncio
    async def test_generate_empty_description_fails(self) -> None:
        """Test that empty description raises ValidationError."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")

        with pytest.raises(ValidationError) as exc_info:
            await generator.generate_test(description="")

        assert "cannot be empty" in str(exc_info.value)


class TestResponseParsing:
    """Test response parsing functionality."""

    def test_extract_json_plain(self) -> None:
        """Test extracting JSON from plain response."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        response = '{"name": "test", "version": "1.0"}'

        result = generator._extract_json_from_response(response)

        assert result["name"] == "test"
        assert result["version"] == "1.0"

    def test_extract_json_with_markdown(self) -> None:
        """Test extracting JSON from markdown code block."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        response = """Here's the test definition:

```json
{
  "name": "test",
  "version": "1.0"
}
```

That should work!"""

        result = generator._extract_json_from_response(response)

        assert result["name"] == "test"
        assert result["version"] == "1.0"

    def test_extract_json_with_code_block(self) -> None:
        """Test extracting JSON from generic code block."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        response = """```
{"name": "test", "version": "1.0"}
```"""

        result = generator._extract_json_from_response(response)

        assert result["name"] == "test"

    def test_extract_json_with_extra_text(self) -> None:
        """Test extracting JSON with surrounding text."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        response = 'Here is your test: {"name": "test"} Hope it helps!'

        result = generator._extract_json_from_response(response)

        assert result["name"] == "test"

    def test_extract_malformed_json_fails(self) -> None:
        """Test that malformed JSON raises ParseError."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        response = '{"name": "test", invalid json}'

        with pytest.raises(ParseError) as exc_info:
            generator._extract_json_from_response(response)

        assert "Failed to parse" in str(exc_info.value)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self) -> None:
        """Test handling of rate limit errors."""
        from anthropic import RateLimitError as AnthropicRateLimitError

        with patch("uitestflow.llm.claude_client.Anthropic") as mock_anthropic:
            mock_client = Mock()
            # Create a proper mock exception with required attributes
            mock_response = Mock()
            mock_response.status_code = 429
            error = AnthropicRateLimitError(
                message="Rate limited",
                response=mock_response,
                body={"error": {"message": "Rate limited"}},
            )
            mock_client.messages.create.side_effect = error
            mock_anthropic.return_value = mock_client

            generator = ClaudeTestGenerator(api_key="sk-ant-test-key")

            with pytest.raises(RateLimitError):
                await generator.generate_test(description="Test")

    @pytest.mark.asyncio
    async def test_api_error_propagation(self) -> None:
        """Test that API errors are properly handled."""
        from anthropic import APIError

        with patch("uitestflow.llm.claude_client.Anthropic") as mock_anthropic:
            mock_client = Mock()
            # Create a proper mock exception with required attributes
            mock_request = Mock()
            error = APIError(message="API Error", request=mock_request, body=None)
            mock_client.messages.create.side_effect = error
            mock_anthropic.return_value = mock_client

            generator = ClaudeTestGenerator(api_key="sk-ant-test-key")

            # Should retry 3 times then fail
            with pytest.raises(Exception):  # LLMError or APIError
                await generator.generate_test(description="Test")

            # Verify retries happened
            assert mock_client.messages.create.call_count >= 1


class TestValidation:
    """Test validation functionality."""

    def test_list_available_models(self) -> None:
        """Test listing available models."""
        generator = ClaudeTestGenerator(api_key="sk-ant-test-key")
        models = generator.list_available_models()

        assert len(models) > 0
        assert "claude-3-5-haiku-20241022" in models
        assert "claude-3-5-sonnet-20241022" in models


class TestPromptGeneration:
    """Test prompt generation."""

    def test_prompt_includes_description(self) -> None:
        """Test that generated prompt includes the description."""
        from uitestflow.llm.prompts import get_test_generation_prompt

        description = "Login with username admin"
        prompt = get_test_generation_prompt(description)

        assert description in prompt

    def test_prompt_includes_base_url(self) -> None:
        """Test that prompt includes base URL when provided."""
        from uitestflow.llm.prompts import get_test_generation_prompt

        base_url = "https://myapp.com"
        prompt = get_test_generation_prompt("Test", base_url=base_url)

        assert base_url in prompt

    def test_system_prompt_exists(self) -> None:
        """Test that system prompt is defined."""
        from uitestflow.llm.prompts import SYSTEM_PROMPT_TEST_GENERATION

        assert len(SYSTEM_PROMPT_TEST_GENERATION) > 0
        assert "test definition" in SYSTEM_PROMPT_TEST_GENERATION.lower()
