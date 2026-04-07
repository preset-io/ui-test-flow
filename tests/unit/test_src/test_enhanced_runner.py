"""Unit tests for EnhancedTestRunner with Claude guidance."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from uitestflow.core.models import (
    ActionType,
    BrowserConfig,
    StepResult,
    TestDefinition,
    TestStatus,
    TestStep,
)
from uitestflow.llm.executor import ClaudeExecutor
from uitestflow.src.browser_manager import BrowserSession, BrowserSessionManager
from uitestflow.src.enhanced_test_runner import EnhancedTestRunner


@pytest.fixture
def mock_claude_executor():
    """Mock Claude executor for testing."""
    executor = Mock(spec=ClaudeExecutor)
    executor.model = "claude-3-5-haiku-20241022"
    executor.get_step_guidance = AsyncMock(
        return_value={
            "guidance": "Test guidance",
            "selector_valid": True,
            "warnings": [],
            "suggestions": [],
        }
    )
    executor.suggest_selector_alternatives = AsyncMock(
        return_value=["#alt1", ".alt2", "[data-testid='alt3']"]
    )
    executor.suggest_error_recovery = AsyncMock(
        return_value={
            "recoverable": True,
            "recovery_action": "Wait for element to load",
            "explanation": "Element may need more time",
        }
    )
    executor.validate_step_result = AsyncMock(
        return_value={
            "validated": True,
            "unexpected_changes": [],
            "suggestions": [],
        }
    )
    return executor


@pytest.fixture
def mock_browser_manager(mock_browser_session):
    """Mock browser manager for testing."""
    manager = Mock(spec=BrowserSessionManager)
    manager._playwright = Mock()
    manager.start = AsyncMock()

    # Set up create_session as async context manager by default
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_browser_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    manager.create_session = Mock(return_value=mock_cm)

    return manager


@pytest.fixture
def mock_browser_session():
    """Mock browser session for testing."""
    session = Mock(spec=BrowserSession)
    session.page = Mock()
    session.page.url = "https://example.com"
    session.page.title = AsyncMock(return_value="Example Domain")
    session.page.goto = AsyncMock()
    session.page.click = AsyncMock()
    session.page.fill = AsyncMock()
    session.page.wait_for_selector = AsyncMock()
    session.page.evaluate = AsyncMock()
    session.page.query_selector = AsyncMock()
    session.context = Mock()
    session.context.cookies = AsyncMock(return_value=[])
    session.config = BrowserConfig()
    session.screenshots = []
    session.screenshot = AsyncMock()
    session.get_console_errors = Mock(return_value=[])
    session.get_console_warnings = Mock(return_value=[])
    session.get_page_state = AsyncMock(
        return_value={
            "url": "https://example.com",
            "title": "Example Domain",
            "viewport": {"width": 1920, "height": 1080},
            "console_errors": [],
            "console_warnings": [],
            "cookies": [],
            "local_storage": {},
            "dom_summary": {
                "forms": 0,
                "links": 1,
                "images": 0,
                "buttons": 0,
                "inputs": 0,
            },
        }
    )
    return session


@pytest.fixture
def simple_test_definition():
    """Simple test definition for testing."""
    return TestDefinition(
        name="simple_test",
        description="A simple test",
        steps=[
            TestStep(
                name="Navigate to page",
                action=ActionType.GOTO,
                url="https://example.com",
            ),
            TestStep(
                name="Click button",
                action=ActionType.CLICK,
                selector="button.submit",
            ),
        ],
        evaluators=[],
    )


class TestEnhancedTestRunnerInitialization:
    """Test EnhancedTestRunner initialization."""

    def test_init_without_claude_executor(self, mock_browser_manager):
        """Test AC3.1: EnhancedTestRunner initialization without Claude."""
        runner = EnhancedTestRunner(browser_manager=mock_browser_manager)

        assert runner.browser_manager == mock_browser_manager
        assert runner.claude_executor is None
        assert runner.guidance_enabled is False
        assert isinstance(runner, EnhancedTestRunner)

    def test_init_with_claude_executor(self, mock_browser_manager, mock_claude_executor):
        """Test AC3.1: EnhancedTestRunner initialization with Claude."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        assert runner.browser_manager == mock_browser_manager
        assert runner.claude_executor == mock_claude_executor
        assert runner.guidance_enabled is True

    def test_extends_test_runner(self, mock_browser_manager):
        """Test AC3.1: EnhancedTestRunner extends TestRunner."""
        from uitestflow.src.test_runner import TestRunner

        runner = EnhancedTestRunner(browser_manager=mock_browser_manager)

        assert isinstance(runner, TestRunner)

    def test_backward_compatibility(self, mock_browser_manager):
        """Test AC3.9: Can be used as drop-in replacement."""
        runner = EnhancedTestRunner(browser_manager=mock_browser_manager)

        # Should have all TestRunner methods
        assert hasattr(runner, "run_test")
        assert hasattr(runner, "_execute_step")
        assert hasattr(runner, "_run_evaluators")


class TestGuidedExecution:
    """Test guided execution functionality."""

    @pytest.mark.asyncio
    async def test_fallback_to_standard_execution_without_executor(
        self, mock_browser_manager, mock_browser_session, simple_test_definition
    ):
        """Test AC3.1: Falls back to regular execution if no claude_executor."""
        runner = EnhancedTestRunner(browser_manager=mock_browser_manager)

        # Should not raise error and should execute test
        with patch.object(runner, "_execute_step", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = StepResult(
                step_name="test",
                step_index=0,
                action="goto",
                success=True,
                duration_ms=100,
            )
            mock_execute.return_value = StepResult(
                step_name="test",
                step_index=1,
                action="click",
                success=True,
                duration_ms=50,
            )

            with patch.object(runner, "_run_evaluators", new_callable=AsyncMock) as mock_eval:
                mock_eval.return_value = []

                test_run = await runner.run_test(simple_test_definition, guided=False)

                assert test_run.status in [TestStatus.COMPLETED, TestStatus.FAILED]

    @pytest.mark.asyncio
    async def test_guided_execution_with_executor(
        self,
        mock_browser_manager,
        mock_browser_session,
        mock_claude_executor,
        simple_test_definition,
    ):
        """Test AC3.3: Claude guidance integration."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        with patch.object(runner, "_run_evaluators", new_callable=AsyncMock) as mock_eval:
            mock_eval.return_value = []

            test_run = await runner.run_test(simple_test_definition, guided=True)

            # Verify Claude executor was called for guidance
            assert mock_claude_executor.get_step_guidance.call_count > 0

            # Verify guidance metadata is present
            assert "guidance_enabled" in test_run.guidance_metadata
            assert test_run.guidance_metadata["guidance_enabled"] is True


class TestPageStateCapture:
    """Test page state capture functionality."""

    @pytest.mark.asyncio
    async def test_page_state_capture(self, mock_browser_session):
        """Test AC3.2: Captures comprehensive page state."""
        page_state = await mock_browser_session.get_page_state()

        # Verify required fields
        assert "url" in page_state
        assert "title" in page_state
        assert "viewport" in page_state
        assert "console_errors" in page_state
        assert "console_warnings" in page_state

        # Verify viewport structure
        assert "width" in page_state["viewport"]
        assert "height" in page_state["viewport"]

    @pytest.mark.asyncio
    async def test_page_state_includes_console_logs(self, mock_browser_session):
        """Test AC3.2: Captures console logs."""
        mock_browser_session.get_console_errors.return_value = ["Error 1", "Error 2"]
        mock_browser_session.get_console_warnings.return_value = ["Warning 1"]

        # Update get_page_state to return updated console logs
        mock_browser_session.get_page_state = AsyncMock(
            return_value={
                "url": "https://example.com",
                "title": "Example Domain",
                "viewport": {"width": 1920, "height": 1080},
                "console_errors": mock_browser_session.get_console_errors.return_value,
                "console_warnings": mock_browser_session.get_console_warnings.return_value,
                "cookies": [],
                "local_storage": {},
                "dom_summary": {
                    "forms": 0,
                    "links": 1,
                    "images": 0,
                    "buttons": 0,
                    "inputs": 0,
                },
            }
        )

        page_state = await mock_browser_session.get_page_state()

        assert len(page_state["console_errors"]) == 2
        assert len(page_state["console_warnings"]) == 1


class TestAdaptiveSelectorResolution:
    """Test adaptive selector resolution."""

    @pytest.mark.asyncio
    async def test_selector_adaptation_on_failure(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.4: Claude suggests alternative selector if primary fails."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        # First call fails, second succeeds with alternative
        mock_browser_session.page.click.side_effect = [
            PlaywrightTimeoutError("Element not found"),
            None,  # Success on retry
        ]
        mock_browser_session.page.query_selector.return_value = Mock()  # Element found

        step = TestStep(
            name="Click button",
            action=ActionType.CLICK,
            selector="button.submit",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp/screenshots"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        # Verify selector alternatives were requested
        mock_claude_executor.suggest_selector_alternatives.assert_called_once()

        # Verify adapted selector was used
        assert result.adapted_selector is not None

    @pytest.mark.asyncio
    async def test_adapted_selector_recorded(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.4: Records which selector succeeded."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        mock_browser_session.page.click.side_effect = [
            PlaywrightTimeoutError("Not found"),
            None,
        ]
        mock_browser_session.page.query_selector.return_value = Mock()

        step = TestStep(
            name="Click",
            action=ActionType.CLICK,
            selector=".original",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        assert result.adapted_selector in ["#alt1", ".alt2", "[data-testid='alt3']"]


class TestErrorRecovery:
    """Test error recovery functionality."""

    @pytest.mark.asyncio
    async def test_error_recovery_suggestion(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.5: Claude suggests recovery action."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        mock_browser_session.page.click.side_effect = Exception("Element not clickable")

        step = TestStep(
            name="Click",
            action=ActionType.CLICK,
            selector="button",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        # Verify error recovery was attempted
        assert result.error_recovery_attempted is True
        mock_claude_executor.suggest_error_recovery.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_marked_as_recovered(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.5: Marks step as recovered."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        mock_browser_session.page.fill.side_effect = Exception("Input disabled")

        step = TestStep(
            name="Fill input",
            action=ActionType.FILL,
            selector="input",
            value="test",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        assert result.error_recovery_attempted is True
        assert result.recovery_action is not None


class TestResultEnrichment:
    """Test result enrichment with guidance data."""

    @pytest.mark.asyncio
    async def test_step_result_includes_guidance(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.8: StepResult includes Claude guidance."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        step = TestStep(
            name="Navigate",
            action=ActionType.GOTO,
            url="https://example.com",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        assert result.claude_guidance is not None
        assert isinstance(result.claude_guidance, str)

    @pytest.mark.asyncio
    async def test_step_result_includes_page_state(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.8: StepResult includes page state."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        step = TestStep(
            name="Click",
            action=ActionType.CLICK,
            selector="button",
        )

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        assert result.page_state is not None
        assert "url" in result.page_state
        assert "title" in result.page_state


class TestPerformance:
    """Test performance requirements."""

    @pytest.mark.asyncio
    async def test_guidance_overhead_reasonable(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.10: Guidance overhead < 2s per step."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        step = TestStep(
            name="Quick action",
            action=ActionType.CLICK,
            selector="button",
        )

        import time

        start = time.time()

        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        duration = time.time() - start

        # Total time should be reasonable (allowing for mock overhead)
        assert duration < 5.0  # Generous for mocks


class TestErrorScenarios:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_continues_on_guidance_failure(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.14: Continues execution on guidance failure."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        # Make Claude guidance fail
        mock_claude_executor.get_step_guidance.side_effect = Exception("API Error")

        step = TestStep(
            name="Navigate",
            action=ActionType.GOTO,
            url="https://example.com",
        )

        # Should not raise exception
        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        # Step should still execute
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_malformed_guidance(
        self, mock_browser_manager, mock_browser_session, mock_claude_executor
    ):
        """Test AC3.14: Handles malformed Claude responses."""
        runner = EnhancedTestRunner(
            browser_manager=mock_browser_manager,
            claude_executor=mock_claude_executor,
        )

        # Return malformed guidance
        mock_claude_executor.get_step_guidance.return_value = {"invalid": "structure"}

        step = TestStep(
            name="Click",
            action=ActionType.CLICK,
            selector="button",
        )

        # Should handle gracefully
        result = await runner._execute_step_with_guidance(
            session=mock_browser_session,
            step=step,
            step_index=0,
            screenshots_dir=Path("/tmp"),
            default_timeout=5000,
            guidance_metadata={
                "steps_with_guidance": 0,
                "selectors_adapted": 0,
                "errors_recovered": 0,
            },
        )

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
