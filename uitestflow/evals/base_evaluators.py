"""
Base evaluation functions for UITestFlow.

These evaluators validate UI test execution results and behavior,
including execution status, element visibility, console errors, and performance.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EvalResult:
    """Result from an evaluation function."""

    passed: bool
    score: float  # 0.0 to 1.0
    evaluator_name: str
    reason: str | None = None
    details: dict[str, Any] | None = None
    screenshot_path: str | None = None


class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        """
        Evaluate based on the provided context.

        Args:
            context: Dictionary containing:
                - test_definition: The test definition
                - test_run: The test run results
                - steps: List of executed test steps
                - screenshots: List of screenshot paths
                - console_logs: Console log entries
                - errors: List of errors encountered
                - start_time: Test start timestamp
                - end_time: Test end timestamp
                - page_state: Current page state (URL, title, etc.)

        Returns:
            EvalResult with pass/fail and details
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the evaluator."""

    @property
    def description(self) -> str:
        """Description of what this evaluator checks."""
        return ""


class ExecutionSuccessful(BaseEvaluator):
    """Check if all test steps completed without errors."""

    @property
    def name(self) -> str:
        return "execution_successful"

    @property
    def description(self) -> str:
        return "Checks if all test steps completed without errors"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        steps = context.get("steps", [])
        errors = context.get("errors", [])

        if not steps:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason="No steps were executed",
            )

        if errors:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"{len(errors)} error(s) occurred during execution",
                details={"errors": errors},
            )

        # Check if all steps completed successfully
        failed_steps = [s for s in steps if s.get("status") == "failed"]
        if failed_steps:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"{len(failed_steps)} step(s) failed",
                details={"failed_steps": [s.get("name") for s in failed_steps]},
            )

        return EvalResult(
            passed=True,
            score=1.0,
            evaluator_name=self.name,
            reason="All steps completed successfully",
            details={"total_steps": len(steps)},
        )


class AllStepsCompleted(BaseEvaluator):
    """Verify all defined steps were executed."""

    @property
    def name(self) -> str:
        return "all_steps_completed"

    @property
    def description(self) -> str:
        return "Verifies all defined test steps were executed"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        test_definition = context.get("test_definition", {})
        steps = context.get("steps", [])

        expected_steps = test_definition.get("steps", [])
        expected_count = len(expected_steps)
        executed_count = len(steps)

        if executed_count == 0:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason="No steps were executed",
            )

        if executed_count < expected_count:
            score = executed_count / expected_count if expected_count > 0 else 0.0
            return EvalResult(
                passed=False,
                score=score,
                evaluator_name=self.name,
                reason=f"Only {executed_count}/{expected_count} steps were executed",
                details={
                    "expected_count": expected_count,
                    "executed_count": executed_count,
                },
            )

        return EvalResult(
            passed=True,
            score=1.0,
            evaluator_name=self.name,
            reason=f"All {executed_count} steps were executed",
            details={"step_count": executed_count},
        )


class NoConsoleErrors(BaseEvaluator):
    """Check for console.error() calls."""

    def __init__(self, max_errors: int = 0):
        """
        Initialize the evaluator.

        Args:
            max_errors: Maximum allowed console errors (default: 0)
        """
        self.max_errors = max_errors

    @property
    def name(self) -> str:
        return "no_console_errors"

    @property
    def description(self) -> str:
        return f"Checks for console errors (max allowed: {self.max_errors})"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        console_logs = context.get("console_logs", [])

        # Filter for error-level logs
        errors = [log for log in console_logs if log.get("level") == "error"]
        error_count = len(errors)

        if error_count > self.max_errors:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"Found {error_count} console error(s), max allowed: {self.max_errors}",
                details={
                    "error_count": error_count,
                    "errors": [e.get("message") for e in errors[:10]],  # First 10 errors
                },
            )

        return EvalResult(
            passed=True,
            score=1.0,
            evaluator_name=self.name,
            reason=f"No console errors found (checked {len(console_logs)} log entries)",
            details={"total_logs": len(console_logs)},
        )


class WithinTimeLimit(BaseEvaluator):
    """Check if test completed within specified time limit."""

    def __init__(self, max_duration_ms: int):
        """
        Initialize the evaluator.

        Args:
            max_duration_ms: Maximum allowed duration in milliseconds
        """
        self.max_duration_ms = max_duration_ms

    @property
    def name(self) -> str:
        return "within_time_limit"

    @property
    def description(self) -> str:
        return f"Checks if test completed within {self.max_duration_ms}ms"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        start_time = context.get("start_time")
        end_time = context.get("end_time")

        if not start_time or not end_time:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason="Missing timing information",
            )

        # Calculate duration in milliseconds
        from datetime import datetime

        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        if duration_ms > self.max_duration_ms:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"Test took {duration_ms}ms, exceeding limit of {self.max_duration_ms}ms",
                details={
                    "duration_ms": duration_ms,
                    "limit_ms": self.max_duration_ms,
                    "overtime_ms": duration_ms - self.max_duration_ms,
                },
            )

        # Calculate score based on how much time was used
        score = 1.0 - (duration_ms / self.max_duration_ms * 0.5)  # Faster is better
        score = max(0.5, min(1.0, score))  # Clamp between 0.5 and 1.0

        return EvalResult(
            passed=True,
            score=score,
            evaluator_name=self.name,
            reason=f"Test completed in {duration_ms}ms (limit: {self.max_duration_ms}ms)",
            details={
                "duration_ms": duration_ms,
                "limit_ms": self.max_duration_ms,
            },
        )


class ElementVisible(BaseEvaluator):
    """Check if a specific element is visible on the page."""

    def __init__(self, selector: str, element_name: str | None = None):
        """
        Initialize the evaluator.

        Args:
            selector: CSS selector for the element
            element_name: Optional human-readable name for the element
        """
        self.selector = selector
        self.element_name = element_name or selector

    @property
    def name(self) -> str:
        return f"element_visible:{self.selector}"

    @property
    def description(self) -> str:
        return f"Checks if element '{self.element_name}' is visible"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        page_state = context.get("page_state", {})
        visible_elements = page_state.get("visible_elements", [])

        # Check if selector is in visible elements
        is_visible = self.selector in visible_elements

        if not is_visible:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"Element '{self.element_name}' is not visible",
                details={"selector": self.selector},
            )

        return EvalResult(
            passed=True,
            score=1.0,
            evaluator_name=self.name,
            reason=f"Element '{self.element_name}' is visible",
            details={"selector": self.selector},
        )


class UrlMatches(BaseEvaluator):
    """Check if the current URL matches expected pattern."""

    def __init__(self, expected_url: str | None = None, pattern: str | None = None):
        """
        Initialize the evaluator.

        Args:
            expected_url: Exact URL to match (optional)
            pattern: Regex pattern to match URL (optional)
        """
        if not expected_url and not pattern:
            raise ValueError("Either expected_url or pattern must be provided")

        self.expected_url = expected_url
        self.pattern = pattern

    @property
    def name(self) -> str:
        return "url_matches"

    @property
    def description(self) -> str:
        if self.expected_url:
            return f"Checks if URL matches: {self.expected_url}"
        return f"Checks if URL matches pattern: {self.pattern}"

    def evaluate(self, context: dict[str, Any]) -> EvalResult:
        page_state = context.get("page_state", {})
        current_url = page_state.get("url", "")

        if not current_url:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason="Current URL is not available",
            )

        # Check exact match
        if self.expected_url:
            if current_url == self.expected_url:
                return EvalResult(
                    passed=True,
                    score=1.0,
                    evaluator_name=self.name,
                    reason=f"URL matches expected: {self.expected_url}",
                    details={"current_url": current_url},
                )
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"URL does not match. Expected: {self.expected_url}, Got: {current_url}",
                details={
                    "expected_url": self.expected_url,
                    "current_url": current_url,
                },
            )

        # Check pattern match
        if self.pattern:
            if re.search(self.pattern, current_url):
                return EvalResult(
                    passed=True,
                    score=1.0,
                    evaluator_name=self.name,
                    reason=f"URL matches pattern: {self.pattern}",
                    details={"current_url": current_url, "pattern": self.pattern},
                )
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_name=self.name,
                reason=f"URL does not match pattern: {self.pattern}",
                details={"current_url": current_url, "pattern": self.pattern},
            )

        return EvalResult(
            passed=False,
            score=0.0,
            evaluator_name=self.name,
            reason="No validation criteria specified",
        )
