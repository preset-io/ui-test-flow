"""
Custom exception classes for UITestFlow.

This module defines a hierarchy of exceptions used throughout the
uitestflow package to provide clear error handling and reporting.
"""


class UITestFlowError(Exception):
    """Base exception for all UITestFlow errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(UITestFlowError):
    """Raised when there's an issue with configuration."""


class ProfileNotFoundError(ConfigurationError):
    """Raised when a requested profile cannot be found."""

    def __init__(self, profile_id: str, available_profiles: list[str] | None = None) -> None:
        """Initialize with profile ID and optional list of available profiles.

        Args:
            profile_id: The profile ID that was not found
            available_profiles: Optional list of available profile IDs
        """
        details = {"profile_id": profile_id}
        if available_profiles:
            details["available_profiles"] = available_profiles

        message = f"Profile '{profile_id}' not found"
        if available_profiles:
            message += f". Available profiles: {', '.join(available_profiles)}"

        super().__init__(message, details)
        self.profile_id = profile_id
        self.available_profiles = available_profiles


class ProfileValidationError(ConfigurationError):
    """Raised when profile validation fails."""

    def __init__(self, profile_id: str, validation_errors: list[str]) -> None:
        """Initialize with profile ID and validation errors.

        Args:
            profile_id: The profile ID that failed validation
            validation_errors: List of validation error messages
        """
        message = f"Profile '{profile_id}' validation failed: {'; '.join(validation_errors)}"
        details = {"profile_id": profile_id, "validation_errors": validation_errors}
        super().__init__(message, details)
        self.profile_id = profile_id
        self.validation_errors = validation_errors


class TestDefinitionError(UITestFlowError):
    """Raised when there's an issue with test definition."""


class TestParseError(TestDefinitionError):
    """Raised when parsing a test definition fails."""

    def __init__(self, source: str, parse_errors: list[str]) -> None:
        """Initialize with source and parse errors.

        Args:
            source: Source of the test definition (file path, URL, etc.)
            parse_errors: List of parse error messages
        """
        message = f"Failed to parse test from '{source}': {'; '.join(parse_errors)}"
        details = {"source": source, "parse_errors": parse_errors}
        super().__init__(message, details)
        self.source = source
        self.parse_errors = parse_errors


class TestValidationError(TestDefinitionError):
    """Raised when test validation fails."""

    def __init__(self, test_name: str, validation_errors: list[str]) -> None:
        """Initialize with test name and validation errors.

        Args:
            test_name: Name of the test that failed validation
            validation_errors: List of validation error messages
        """
        message = f"Test '{test_name}' validation failed: {'; '.join(validation_errors)}"
        details = {"test_name": test_name, "validation_errors": validation_errors}
        super().__init__(message, details)
        self.test_name = test_name
        self.validation_errors = validation_errors


class TestExecutionError(UITestFlowError):
    """Raised when test execution fails."""

    def __init__(
        self,
        test_name: str,
        step_name: str | None = None,
        error_message: str | None = None,
        screenshot_path: str | None = None,
    ) -> None:
        """Initialize with test execution details.

        Args:
            test_name: Name of the test that failed
            step_name: Optional name of the step that failed
            error_message: Optional error message
            screenshot_path: Optional path to error screenshot
        """
        message = f"Test '{test_name}' failed"
        if step_name:
            message += f" at step '{step_name}'"
        if error_message:
            message += f": {error_message}"

        details = {"test_name": test_name}
        if step_name:
            details["step_name"] = step_name
        if error_message:
            details["error_message"] = error_message
        if screenshot_path:
            details["screenshot_path"] = screenshot_path

        super().__init__(message, details)
        self.test_name = test_name
        self.step_name = step_name
        self.error_message = error_message
        self.screenshot_path = screenshot_path


class BrowserError(UITestFlowError):
    """Raised when there's an issue with browser automation."""


class BrowserLaunchError(BrowserError):
    """Raised when browser fails to launch."""

    def __init__(self, browser_type: str, error_message: str) -> None:
        """Initialize with browser type and error message.

        Args:
            browser_type: Type of browser (chromium, firefox, webkit)
            error_message: Error message from browser launch
        """
        message = f"Failed to launch {browser_type} browser: {error_message}"
        details = {"browser_type": browser_type, "error_message": error_message}
        super().__init__(message, details)
        self.browser_type = browser_type


class BrowserTimeoutError(BrowserError):
    """Raised when a browser operation times out."""

    def __init__(self, operation: str, timeout_ms: int, selector: str | None = None) -> None:
        """Initialize with operation details.

        Args:
            operation: The operation that timed out
            timeout_ms: Timeout value in milliseconds
            selector: Optional selector that was being waited for
        """
        message = f"Browser operation '{operation}' timed out after {timeout_ms}ms"
        if selector:
            message += f" waiting for selector '{selector}'"

        details = {"operation": operation, "timeout_ms": timeout_ms}
        if selector:
            details["selector"] = selector

        super().__init__(message, details)
        self.operation = operation
        self.timeout_ms = timeout_ms
        self.selector = selector


class AuthenticationError(UITestFlowError):
    """Raised when authentication fails."""

    def __init__(self, auth_type: str, error_message: str) -> None:
        """Initialize with authentication type and error message.

        Args:
            auth_type: Type of authentication (form, oauth, jwt, etc.)
            error_message: Error message from authentication attempt
        """
        message = f"Authentication failed for type '{auth_type}': {error_message}"
        details = {"auth_type": auth_type, "error_message": error_message}
        super().__init__(message, details)
        self.auth_type = auth_type


class EvaluatorError(UITestFlowError):
    """Raised when an evaluator fails."""

    def __init__(self, evaluator_name: str, error_message: str) -> None:
        """Initialize with evaluator details.

        Args:
            evaluator_name: Name of the evaluator that failed
            error_message: Error message from evaluator
        """
        message = f"Evaluator '{evaluator_name}' failed: {error_message}"
        details = {"evaluator_name": evaluator_name, "error_message": error_message}
        super().__init__(message, details)
        self.evaluator_name = evaluator_name


class StorageError(UITestFlowError):
    """Raised when there's an issue with artifact storage."""

    def __init__(self, operation: str, path: str, error_message: str) -> None:
        """Initialize with storage operation details.

        Args:
            operation: The storage operation that failed (upload, download, delete)
            path: Path or key of the artifact
            error_message: Error message from storage operation
        """
        message = f"Storage {operation} failed for '{path}': {error_message}"
        details = {"operation": operation, "path": path, "error_message": error_message}
        super().__init__(message, details)
        self.operation = operation
        self.path = path


class NotificationError(UITestFlowError):
    """Raised when notification delivery fails."""

    def __init__(self, notification_type: str, error_message: str) -> None:
        """Initialize with notification details.

        Args:
            notification_type: Type of notification (slack, email, pagerduty, etc.)
            error_message: Error message from notification attempt
        """
        message = f"Failed to send {notification_type} notification: {error_message}"
        details = {"notification_type": notification_type, "error_message": error_message}
        super().__init__(message, details)
        self.notification_type = notification_type
