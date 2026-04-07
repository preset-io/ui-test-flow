"""
Integration tests for test generation with Claude.

These tests make real API calls to Claude (if API key is available).
They are skipped if no API key is found.
"""

import os

import pytest

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import GenerationConfig


# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping integration tests",
)


class TestRealClaudeGeneration:
    """Integration tests with real Claude API."""

    @pytest.fixture
    def generator(self) -> ClaudeTestGenerator:
        """Create generator with real API key."""
        return ClaudeTestGenerator()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_simple_login_test(self, generator: ClaudeTestGenerator) -> None:
        """Test generating a simple login test with real API."""
        description = "Login with username 'admin' and password 'password123'"

        test_def = await generator.generate_test(description)

        # Verify basic structure
        assert test_def.name is not None
        assert len(test_def.steps) >= 3

        # Verify it has login-related steps
        step_actions = [step.action for step in test_def.steps]
        assert "goto" in step_actions or any("goto" in str(action) for action in step_actions)
        assert "fill" in step_actions or any("fill" in str(action) for action in step_actions)
        assert "click" in step_actions or any("click" in str(action) for action in step_actions)

        # Verify it has at least one evaluator
        assert len(test_def.evaluators) >= 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_form_submission_test(self, generator: ClaudeTestGenerator) -> None:
        """Test generating a form submission test."""
        description = """
        Fill out a contact form with:
        - Name: John Doe
        - Email: john@example.com
        - Message: Test message
        Then submit the form and verify success message appears
        """

        test_def = await generator.generate_test(
            description,
            base_url="https://example.com/contact",
        )

        # Verify structure
        assert test_def.name is not None
        assert len(test_def.steps) >= 4  # At least fill 3 fields + submit

        # Should have fill steps for form fields
        fill_steps = [step for step in test_def.steps if "fill" in str(step.action).lower()]
        assert len(fill_steps) >= 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_navigation_test(self, generator: ClaudeTestGenerator) -> None:
        """Test generating a navigation test."""
        description = "Navigate to homepage, click Products menu, then click on first product"

        test_def = await generator.generate_test(description)

        # Verify structure
        assert test_def.name is not None
        assert len(test_def.steps) >= 3

        # Should have navigation and click steps
        actions = [str(step.action).lower() for step in test_def.steps]
        assert any("goto" in action for action in actions)
        assert any("click" in action for action in actions)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_with_haiku_model(self, generator: ClaudeTestGenerator) -> None:
        """Test generation with Haiku model (faster)."""
        config = GenerationConfig(
            model="claude-3-5-haiku-20241022",
            temperature=0.3,
            max_tokens=2048,
        )

        test_def = await generator.generate_test(
            description="Simple login test",
            config_override=config,
        )

        assert test_def.name is not None
        assert len(test_def.steps) >= 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_search_test(self, generator: ClaudeTestGenerator) -> None:
        """Test generating a search test."""
        description = "Search for 'playwright automation' and verify results appear"

        test_def = await generator.generate_test(
            description,
            base_url="https://example.com",
        )

        # Verify structure
        assert test_def.name is not None

        # Should have fill step for search input and wait/expect for results
        step_actions = [str(step.action).lower() for step in test_def.steps]
        assert any("fill" in action or "type" in action for action in step_actions)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generated_test_has_evaluators(self, generator: ClaudeTestGenerator) -> None:
        """Test that generated tests have appropriate evaluators."""
        test_def = await generator.generate_test(
            description="Login test that should not have console errors"
        )

        # Should have at least one evaluator
        assert len(test_def.evaluators) >= 1

        # Check evaluator types are valid
        for evaluator in test_def.evaluators:
            assert evaluator.name is not None
            assert evaluator.type is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generated_test_has_proper_selectors(
        self, generator: ClaudeTestGenerator
    ) -> None:
        """Test that generated tests have reasonable selectors."""
        test_def = await generator.generate_test(
            description="Fill login form with username and password fields"
        )

        # Find fill steps
        fill_steps = [step for step in test_def.steps if "fill" in str(step.action).lower()]

        assert len(fill_steps) >= 2

        # Verify selectors exist
        for step in fill_steps:
            assert step.selector is not None
            assert len(step.selector) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_multi_page_workflow(self, generator: ClaudeTestGenerator) -> None:
        """Test generating a multi-page workflow."""
        description = """
        1. Go to login page and login
        2. Navigate to settings
        3. Update profile information
        4. Save changes
        5. Verify success message
        """

        test_def = await generator.generate_test(description)

        # Should have multiple steps for multi-page workflow
        assert len(test_def.steps) >= 5

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generation_with_different_temperatures(
        self, generator: ClaudeTestGenerator
    ) -> None:
        """Test that different temperatures produce valid results."""
        description = "Login test"

        # Low temperature (deterministic)
        config_low = GenerationConfig(temperature=0.0)
        test_low = await generator.generate_test(
            description,
            config_override=config_low,
        )

        # High temperature (creative)
        config_high = GenerationConfig(temperature=0.7)
        test_high = await generator.generate_test(
            description,
            config_override=config_high,
        )

        # Both should be valid
        assert test_low.name is not None
        assert test_high.name is not None
        assert len(test_low.steps) >= 1
        assert len(test_high.steps) >= 1
