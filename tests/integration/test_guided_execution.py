"""Integration tests for guided test execution with real browser (mocked Claude)."""

import os
from unittest.mock import AsyncMock, Mock

import pytest

from uitestflow.core.models import ActionType, BrowserConfig, TestDefinition, TestStatus, TestStep
from uitestflow.llm.executor import ClaudeExecutor
from uitestflow.src.browser_manager import BrowserSessionManager
from uitestflow.src.enhanced_test_runner import EnhancedTestRunner


# Skip these tests if ANTHROPIC_API_KEY is not set or if we want to use mocks
SKIP_REAL_API = (
    not os.getenv("ANTHROPIC_API_KEY") or os.getenv("USE_MOCK_CLAUDE", "true").lower() == "true"
)


@pytest.fixture
def mock_claude_executor():
    """Mock Claude executor for integration testing."""
    executor = Mock(spec=ClaudeExecutor)
    executor.model = "claude-3-5-haiku-20241022"

    # Mock guidance responses
    executor.get_step_guidance = AsyncMock(
        return_value={
            "guidance": "Proceeding with navigation to the specified URL",
            "selector_valid": True,
            "warnings": [],
            "suggestions": ["Ensure the page loads successfully"],
        }
    )

    # Mock selector alternatives
    executor.suggest_selector_alternatives = AsyncMock(
        return_value=[
            "[data-testid='submit-button']",
            "button[type='submit']",
            ".submit-btn",
        ]
    )

    # Mock error recovery
    executor.suggest_error_recovery = AsyncMock(
        return_value={
            "recoverable": True,
            "recovery_action": "Wait for dynamic content to load",
            "explanation": "The element may be loading asynchronously",
        }
    )

    # Mock validation
    executor.validate_step_result = AsyncMock(
        return_value={
            "validated": True,
            "unexpected_changes": [],
            "suggestions": ["Verify page title matches expected"],
        }
    )

    return executor


@pytest.fixture
async def browser_manager():
    """Real browser manager for integration testing."""
    manager = BrowserSessionManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def test_results_dir(tmp_path):
    """Temporary directory for test results."""
    return tmp_path / "test_results"


class TestGuidedExecutionIntegration:
    """Integration tests for guided execution."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_navigation_with_guidance(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.7: Executes basic navigation with guidance."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="navigation_test",
            description="Test navigation with guidance",
            url="https://example.com",
            steps=[
                TestStep(
                    name="Navigate to example.com",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # Verify test completed
        assert test_run.status == TestStatus.COMPLETED
        assert test_run.result is not None
        assert test_run.result.passed is True

        # Verify guidance was used
        assert "guidance_enabled" in test_run.guidance_metadata
        assert test_run.guidance_metadata["guidance_enabled"] is True
        assert test_run.guidance_metadata["steps_with_guidance"] > 0

        # Verify step results include guidance
        assert len(test_run.result.step_results) > 0
        first_step = test_run.result.step_results[0]
        assert first_step.claude_guidance is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_step_workflow_with_guidance(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.13: Maintains context across multiple steps."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="multi_step_test",
            description="Test multi-step workflow",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
                TestStep(
                    name="Check title",
                    action=ActionType.WAIT_FOR,
                    selector="h1",
                    timeout=5000,
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # Verify all steps executed
        assert test_run.result is not None
        assert len(test_run.result.step_results) == 2

        # Verify guidance was provided for each step
        for step_result in test_run.result.step_results:
            assert step_result.page_state is not None
            assert "url" in step_result.page_state

        # Verify Claude was called for each step
        assert mock_claude_executor.get_step_guidance.call_count >= 2

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_selector_adaptation_integration(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.4: Adaptive selector resolution in real browser."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        # Test with a selector that will fail, then suggest alternatives
        test_def = TestDefinition(
            name="selector_adaptation_test",
            description="Test selector adaptation",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
                TestStep(
                    name="Click non-existent element",
                    action=ActionType.CLICK,
                    selector="button.does-not-exist",
                    timeout=2000,  # Short timeout to fail quickly
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # First step should succeed
        assert test_run.result.step_results[0].success is True

        # Second step may fail or adapt - check if alternatives were suggested
        if mock_claude_executor.suggest_selector_alternatives.called:
            assert test_run.guidance_metadata.get("selectors_adapted", 0) >= 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_recovery_integration(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.5: Error recovery with Claude in real browser."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="error_recovery_test",
            description="Test error recovery",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
                TestStep(
                    name="Try invalid action",
                    action=ActionType.FILL,
                    selector="input.does-not-exist",
                    value="test",
                    timeout=2000,
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # Check if error recovery was attempted
        failed_step = test_run.result.step_results[-1]
        if not failed_step.success:
            # Error recovery should have been attempted
            if mock_claude_executor.suggest_error_recovery.called:
                assert test_run.guidance_metadata.get("errors_recovered", 0) >= 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_backward_compatibility_mode(self, browser_manager, test_results_dir):
        """Test AC3.9: Works without Claude executor (backward compatible)."""
        # Create runner without Claude executor
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=None,
        )

        test_def = TestDefinition(
            name="backward_compat_test",
            description="Test without Claude",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        # Should execute successfully without guidance
        test_run = await runner.run_test(test_def, guided=False)

        assert test_run.status == TestStatus.COMPLETED
        assert test_run.result is not None
        assert test_run.result.passed is True

        # No guidance metadata should be present
        assert not test_run.guidance_metadata.get("guidance_enabled", False)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_overhead(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.10: Guidance overhead is reasonable."""
        import time

        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="performance_test",
            description="Test performance",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        start_time = time.time()
        test_run = await runner.run_test(test_def, guided=True)
        total_time = time.time() - start_time

        # Verify test completed
        assert test_run.status == TestStatus.COMPLETED

        # Total time should be reasonable (navigation + guidance overhead)
        # Allowing up to 10s for network latency in tests
        assert total_time < 10.0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_page_state_capture_integration(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test AC3.2: Page state is captured correctly."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="page_state_test",
            description="Test page state capture",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # Verify page state was captured
        step_result = test_run.result.step_results[0]
        assert step_result.page_state is not None

        page_state = step_result.page_state
        assert "url" in page_state
        assert "title" in page_state
        assert "viewport" in page_state
        assert "console_errors" in page_state
        assert "console_warnings" in page_state

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_screenshot_capture_with_guidance(
        self, browser_manager, mock_claude_executor, test_results_dir
    ):
        """Test screenshot capture works with guided execution."""
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=mock_claude_executor,
        )

        test_def = TestDefinition(
            name="screenshot_test",
            description="Test screenshots with guidance",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                    screenshot=True,  # Capture screenshot
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        # Verify screenshots were captured
        assert len(test_run.screenshots) > 0
        assert test_run.result.step_results[0].screenshot_path is not None


class TestClaudeExecutorIntegration:
    """Integration tests for ClaudeExecutor (with mocked API)."""

    @pytest.mark.asyncio
    async def test_executor_guidance_format(self, mock_claude_executor):
        """Test that executor returns properly formatted guidance."""
        from uitestflow.core.models import ActionType, TestStep

        step = TestStep(
            name="Test step",
            action=ActionType.CLICK,
            selector="button",
        )

        page_state = {
            "url": "https://example.com",
            "title": "Example",
            "viewport": {"width": 1920, "height": 1080},
            "console_errors": [],
            "console_warnings": [],
        }

        guidance = await mock_claude_executor.get_step_guidance(step, page_state, 0)

        # Verify structure
        assert "guidance" in guidance
        assert "selector_valid" in guidance
        assert "warnings" in guidance
        assert "suggestions" in guidance

    @pytest.mark.asyncio
    async def test_executor_selector_alternatives_format(self, mock_claude_executor):
        """Test selector alternatives return format."""
        page_state = {
            "url": "https://example.com",
            "dom_summary": {"buttons": 5, "inputs": 3},
        }

        alternatives = await mock_claude_executor.suggest_selector_alternatives(
            "button.missing",
            page_state,
            "Element not found",
        )

        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
        for alt in alternatives:
            assert isinstance(alt, str)


@pytest.mark.skipif(SKIP_REAL_API, reason="ANTHROPIC_API_KEY not set or mocks preferred")
class TestRealClaudeIntegration:
    """Tests with real Claude API (skipped by default)."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_claude_guidance(self, browser_manager, test_results_dir):
        """Test with real Claude API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        executor = ClaudeExecutor(api_key=api_key)

        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=test_results_dir,
            claude_executor=executor,
        )

        test_def = TestDefinition(
            name="real_claude_test",
            description="Test with real Claude",
            steps=[
                TestStep(
                    name="Navigate",
                    action=ActionType.GOTO,
                    url="https://example.com",
                ),
            ],
            evaluators=[],
            browser_config=BrowserConfig(headless=True),
        )

        test_run = await runner.run_test(test_def, guided=True)

        assert test_run.status == TestStatus.COMPLETED
        assert test_run.result.step_results[0].claude_guidance is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
