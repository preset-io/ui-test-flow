"""Tests for evaluators."""

from uitestflow.evals.base_evaluators import (
    AllStepsCompleted,
    ElementVisible,
    ExecutionSuccessful,
    NoConsoleErrors,
    UrlMatches,
    WithinTimeLimit,
)


class TestExecutionSuccessful:
    """Test ExecutionSuccessful evaluator."""

    def test_execution_successful_pass(self):
        """Test successful execution evaluation."""
        evaluator = ExecutionSuccessful()
        context = {"steps_executed": 5, "steps_failed": 0, "errors": []}

        result = evaluator.evaluate(context)
        assert result.passed is True
        assert result.score == 1.0
        assert "successfully" in result.reason.lower()

    def test_execution_successful_fail(self):
        """Test failed execution evaluation."""
        evaluator = ExecutionSuccessful()
        context = {"steps_executed": 5, "steps_failed": 2, "errors": ["Error 1", "Error 2"]}

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert result.score == 0.0
        assert "2" in result.reason


class TestAllStepsCompleted:
    """Test AllStepsCompleted evaluator."""

    def test_all_steps_completed_pass(self):
        """Test all steps completed successfully."""
        evaluator = AllStepsCompleted()
        context = {"total_steps": 5, "steps_executed": 5}

        result = evaluator.evaluate(context)
        assert result.passed is True
        assert result.score == 1.0

    def test_all_steps_completed_fail(self):
        """Test not all steps completed."""
        evaluator = AllStepsCompleted()
        context = {"total_steps": 5, "steps_executed": 3}

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert "3/5" in result.reason


class TestNoConsoleErrors:
    """Test NoConsoleErrors evaluator."""

    def test_no_console_errors_pass(self):
        """Test no console errors."""
        evaluator = NoConsoleErrors()
        context = {
            "console_messages": [
                {"level": "log", "text": "Info message"},
                {"level": "warn", "text": "Warning message"},
            ]
        }

        result = evaluator.evaluate(context)
        assert result.passed is True
        assert result.score == 1.0

    def test_no_console_errors_fail(self):
        """Test with console errors."""
        evaluator = NoConsoleErrors()
        context = {
            "console_messages": [
                {"level": "error", "text": "Error 1"},
                {"level": "error", "text": "Error 2"},
            ]
        }

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert "2" in result.reason

    def test_no_console_errors_with_max(self):
        """Test with max errors threshold."""
        evaluator = NoConsoleErrors(max_errors=2)
        context = {
            "console_messages": [
                {"level": "error", "text": "Error 1"},
                {"level": "error", "text": "Error 2"},
            ]
        }

        # Should pass with max_errors=2
        result = evaluator.evaluate(context)
        assert result.passed is True


class TestWithinTimeLimit:
    """Test WithinTimeLimit evaluator."""

    def test_within_time_limit_pass(self):
        """Test execution within time limit."""
        evaluator = WithinTimeLimit(max_duration_ms=5000)
        context = {"duration_ms": 3000}

        result = evaluator.evaluate(context)
        assert result.passed is True
        assert result.score == 1.0

    def test_within_time_limit_fail(self):
        """Test execution exceeding time limit."""
        evaluator = WithinTimeLimit(max_duration_ms=5000)
        context = {"duration_ms": 7000}

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert "7000ms" in result.reason
        assert "5000ms" in result.reason


class TestElementVisible:
    """Test ElementVisible evaluator."""

    def test_element_visible_pass(self):
        """Test element is visible."""
        evaluator = ElementVisible(selector=".content")
        context = {"page_elements": {".content": {"visible": True}}}

        result = evaluator.evaluate(context)
        assert result.passed is True

    def test_element_visible_fail(self):
        """Test element is not visible."""
        evaluator = ElementVisible(selector=".content")
        context = {"page_elements": {".content": {"visible": False}}}

        result = evaluator.evaluate(context)
        assert result.passed is False

    def test_element_not_found(self):
        """Test element not found in context."""
        evaluator = ElementVisible(selector=".missing")
        context = {"page_elements": {}}

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert "not found" in result.reason.lower()


class TestUrlMatches:
    """Test UrlMatches evaluator."""

    def test_url_exact_match(self):
        """Test exact URL match."""
        evaluator = UrlMatches(expected_url="https://example.com/page")
        context = {"current_url": "https://example.com/page"}

        result = evaluator.evaluate(context)
        assert result.passed is True

    def test_url_exact_mismatch(self):
        """Test exact URL mismatch."""
        evaluator = UrlMatches(expected_url="https://example.com/page")
        context = {"current_url": "https://example.com/other"}

        result = evaluator.evaluate(context)
        assert result.passed is False

    def test_url_pattern_match(self):
        """Test URL pattern match."""
        evaluator = UrlMatches(pattern=r"https://example\.com/page/\d+")
        context = {"current_url": "https://example.com/page/123"}

        result = evaluator.evaluate(context)
        assert result.passed is True

    def test_url_pattern_mismatch(self):
        """Test URL pattern mismatch."""
        evaluator = UrlMatches(pattern=r"https://example\.com/page/\d+")
        context = {"current_url": "https://example.com/other/abc"}

        result = evaluator.evaluate(context)
        assert result.passed is False

    def test_url_missing_in_context(self):
        """Test missing URL in context."""
        evaluator = UrlMatches(expected_url="https://example.com")
        context = {}

        result = evaluator.evaluate(context)
        assert result.passed is False
        assert "not found" in result.reason.lower()
