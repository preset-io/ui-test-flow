"""Tests for core data models."""

from datetime import datetime
from uuid import uuid4

from uitestflow.core.models import (
    ActionType,
    AuthConfig,
    AuthType,
    BrowserConfig,
    BrowserType,
    EvalResult,
    EvaluatorConfig,
    LogEntry,
    Screenshot,
    TestDefinition,
    TestResult,
    TestRun,
    TestStatus,
    TestStep,
    ViewportConfig,
)


class TestEnums:
    """Test enum definitions."""

    def test_test_status_values(self):
        """Test TestStatus enum has expected values."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.COMPLETED.value == "completed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.ABORTED.value == "aborted"

    def test_action_type_values(self):
        """Test ActionType enum has expected values."""
        assert ActionType.GOTO.value == "goto"
        assert ActionType.CLICK.value == "click"
        assert ActionType.FILL.value == "fill"
        assert ActionType.WAIT_FOR.value == "wait_for"

    def test_browser_type_values(self):
        """Test BrowserType enum has expected values."""
        assert BrowserType.CHROMIUM.value == "chromium"
        assert BrowserType.FIREFOX.value == "firefox"
        assert BrowserType.WEBKIT.value == "webkit"


class TestBrowserConfig:
    """Test BrowserConfig model."""

    def test_browser_config_defaults(self):
        """Test BrowserConfig with default values."""
        config = BrowserConfig()
        assert config.browser_type == BrowserType.CHROMIUM
        assert config.headless is True
        assert config.viewport.width == 1920
        assert config.viewport.height == 1080

    def test_browser_config_custom(self):
        """Test BrowserConfig with custom values."""
        config = BrowserConfig(
            browser_type=BrowserType.FIREFOX,
            headless=False,
            viewport=ViewportConfig(width=1280, height=720),
            locale="en-GB",
        )
        assert config.browser_type == BrowserType.FIREFOX
        assert config.headless is False
        assert config.viewport.width == 1280
        assert config.locale == "en-GB"


class TestAuthConfig:
    """Test AuthConfig model."""

    def test_auth_config_form(self):
        """Test form authentication config."""
        config = AuthConfig(auth_type=AuthType.FORM, username="testuser", password="testpass")
        assert config.auth_type == AuthType.FORM
        assert config.username == "testuser"
        assert config.password == "testpass"

    def test_auth_config_bearer(self):
        """Test bearer token authentication."""
        config = AuthConfig(auth_type=AuthType.BEARER, token="test-token-123")
        assert config.auth_type == AuthType.BEARER
        assert config.token == "test-token-123"


class TestTestStep:
    """Test TestStep model."""

    def test_test_step_goto(self):
        """Test goto step."""
        step = TestStep(name="Navigate to page", action=ActionType.GOTO, url="https://example.com")
        assert step.name == "Navigate to page"
        assert step.action == ActionType.GOTO
        assert step.url == "https://example.com"

    def test_test_step_click(self):
        """Test click step."""
        step = TestStep(name="Click button", action=ActionType.CLICK, selector=".submit-button")
        assert step.action == ActionType.CLICK
        assert step.selector == ".submit-button"

    def test_test_step_with_timeout(self):
        """Test step with custom timeout."""
        step = TestStep(
            name="Wait for element", action=ActionType.WAIT_FOR, selector=".content", timeout=10000
        )
        assert step.timeout == 10000


class TestTestDefinition:
    """Test TestDefinition model."""

    def test_test_definition_basic(self):
        """Test basic test definition."""
        test_id = uuid4()
        test_def = TestDefinition(
            id=test_id,
            name="Sample Test",
            description="A sample test",
            version="1.0",
            base_url="https://example.com",
            steps=[TestStep(name="Navigate", action=ActionType.GOTO, url="https://example.com")],
            evaluators=[
                EvaluatorConfig(name="execution_successful", evaluator_type="execution_successful")
            ],
        )
        assert test_def.id == test_id
        assert test_def.name == "Sample Test"
        assert len(test_def.steps) == 1
        assert len(test_def.evaluators) == 1

    def test_test_definition_with_tags(self):
        """Test definition with tags."""
        test_def = TestDefinition(
            name="Test",
            version="1.0",
            steps=[TestStep(name="Dummy step", action=ActionType.GOTO, url="https://example.com")],
            evaluators=[],
            tags=["smoke", "regression"],
        )
        assert "smoke" in test_def.tags
        assert "regression" in test_def.tags


class TestTestRun:
    """Test TestRun model."""

    def test_test_run_creation(self):
        """Test creating a test run."""
        run = TestRun(
            test_id=uuid4(),
            test_name="Sample Test",
            triggered_by="manual",
            profile="local",
            context={"pr_number": 123},
        )
        assert run.status == TestStatus.PENDING
        assert run.context["pr_number"] == 123

    def test_test_run_mark_started(self):
        """Test marking test run as started."""
        run = TestRun(
            test_id=uuid4(), test_name="Sample Test", triggered_by="manual", profile="local"
        )
        run.mark_started()
        assert run.status == TestStatus.RUNNING
        assert run.started_at is not None

    def test_test_run_mark_completed(self):
        """Test marking test run as completed."""
        run = TestRun(
            test_id=uuid4(), test_name="Sample Test", triggered_by="manual", profile="local"
        )
        run.mark_started()

        result = TestResult(
            passed=True,
            score=1.0,
            total_steps=5,
            steps_executed=5,
            steps_passed=5,
            steps_failed=0,
            evaluator_results=[],
            total_duration_ms=1000,
        )
        run.mark_completed(result)

        assert run.status == TestStatus.COMPLETED
        assert run.completed_at is not None
        assert run.result == result

    def test_test_run_mark_failed(self):
        """Test marking test run as failed."""
        run = TestRun(
            test_id=uuid4(), test_name="Sample Test", triggered_by="manual", profile="local"
        )
        run.mark_started()

        result = TestResult(
            passed=False,
            score=0.0,
            total_steps=3,
            steps_executed=3,
            steps_passed=2,
            steps_failed=1,
            evaluator_results=[],
            total_duration_ms=500,
            error_message="Step failed",
        )
        run.mark_completed(result)  # mark_completed handles both pass and fail

        assert run.status == TestStatus.FAILED
        assert run.result.passed is False


class TestEvalResult:
    """Test EvalResult model."""

    def test_eval_result_passed(self):
        """Test passed evaluation result."""
        result = EvalResult(
            passed=True,
            score=1.0,
            evaluator_name="execution_successful",
            reason="All steps completed successfully",
        )
        assert result.passed is True
        assert result.score == 1.0

    def test_eval_result_failed(self):
        """Test failed evaluation result."""
        result = EvalResult(
            passed=False,
            score=0.0,
            evaluator_name="no_console_errors",
            reason="Found 3 console errors",
            details={"error_count": 3},
        )
        assert result.passed is False
        assert result.details["error_count"] == 3


class TestScreenshot:
    """Test Screenshot model."""

    def test_screenshot_creation(self):
        """Test creating screenshot."""
        screenshot = Screenshot(
            id=uuid4(),
            test_run_id=uuid4(),
            step_name="Click button",
            step_index=2,
            url="https://s3.example.com/screenshots/abc123.png",
            timestamp=datetime.now(),
        )
        assert screenshot.step_name == "Click button"
        assert screenshot.step_index == 2
        assert "screenshots" in screenshot.url


class TestLogEntry:
    """Test LogEntry model."""

    def test_log_entry_creation(self):
        """Test creating log entry."""
        log = LogEntry(level="info", message="Test step completed", source="https://example.com:10")
        assert log.level == "info"
        assert log.message == "Test step completed"
        assert log.source == "https://example.com:10"
