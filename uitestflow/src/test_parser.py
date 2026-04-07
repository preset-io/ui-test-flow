"""YAML test parser for UITestFlow."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from .models import (
    ActionType,
    AuthConfig,
    BrowserConfig,
    EvaluatorConfig,
    EvaluatorType,
    RetryConfig,
    TestDefinition,
    TestStep,
)


class TestParserError(Exception):
    """Exception raised for test parsing errors."""


class YAMLTestParser:
    """Parse YAML test definitions into TestDefinition objects."""

    def __init__(self, env_vars: dict[str, str] | None = None):
        """
        Initialize the YAML test parser.

        Args:
            env_vars: Optional dictionary of environment variables for substitution.
                     If None, uses os.environ.
        """
        self.env_vars = env_vars if env_vars is not None else dict(os.environ)

    def parse_file(self, file_path: str | Path) -> TestDefinition:
        """
        Parse a YAML test file.

        Args:
            file_path: Path to the YAML file

        Returns:
            TestDefinition object

        Raises:
            TestParserError: If the file cannot be parsed or is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise TestParserError(f"Test file not found: {file_path}")

        if not file_path.is_file():
            raise TestParserError(f"Not a file: {file_path}")

        try:
            with Path(file_path).open("r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise TestParserError(f"Failed to read file {file_path}: {e}")

        return self.parse_string(content)

    def parse_string(self, yaml_content: str) -> TestDefinition:
        """
        Parse a YAML test definition from a string.

        Args:
            yaml_content: YAML content as string

        Returns:
            TestDefinition object

        Raises:
            TestParserError: If the YAML is malformed or invalid
        """
        # Substitute environment variables
        yaml_content = self._substitute_env_vars(yaml_content)

        # Parse YAML
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise TestParserError(f"Invalid YAML: {e}")

        if not isinstance(data, dict):
            raise TestParserError("YAML must be a dictionary at the root level")

        return self._parse_test_definition(data)

    def _substitute_env_vars(self, content: str) -> str:
        """
        Substitute environment variables in the content.

        Supports formats:
        - ${VAR_NAME}
        - $VAR_NAME
        - {{ env.VAR_NAME }}

        Args:
            content: String content with potential env var references

        Returns:
            Content with environment variables substituted
        """

        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2) or match.group(3)
            return self.env_vars.get(var_name, match.group(0))

        # Pattern matches ${VAR}, $VAR, or {{ env.VAR }}
        pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)|\{\{\s*env\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}"
        return re.sub(pattern, replace_env_var, content)

    def _parse_test_definition(self, data: dict[str, Any]) -> TestDefinition:
        """
        Parse test definition from parsed YAML data.

        Args:
            data: Parsed YAML dictionary

        Returns:
            TestDefinition object

        Raises:
            TestParserError: If required fields are missing or invalid
        """
        # Validate required fields
        self._validate_required_fields(data, ["name", "version"])

        # Parse steps
        if "steps" not in data:
            raise TestParserError("Test definition must have 'steps' field")

        if not isinstance(data["steps"], list):
            raise TestParserError("'steps' must be a list")

        steps = [self._parse_step(step, idx) for idx, step in enumerate(data["steps"])]

        # Parse evaluators
        evaluators = []
        if "evaluators" in data:
            if not isinstance(data["evaluators"], list):
                raise TestParserError("'evaluators' must be a list")
            evaluators = [self._parse_evaluator(evaluator) for evaluator in data["evaluators"]]

        # Parse auth config
        auth = None
        if "auth" in data:
            auth = self._parse_auth_config(data["auth"])

        # Parse browser config
        browser_config = None
        if "browser" in data or "browser_config" in data:
            browser_data = data.get("browser") or data.get("browser_config")
            browser_config = self._parse_browser_config(browser_data)

        # Parse retry config
        retry_config = None
        if "retry" in data or "retry_config" in data:
            retry_data = data.get("retry") or data.get("retry_config")
            retry_config = self._parse_retry_config(retry_data)

        return TestDefinition(
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            url=data.get("url"),
            steps=steps,
            evaluators=evaluators,
            auth=auth,
            browser_config=browser_config,
            timeout=data.get("timeout", 30000),
            retry_config=retry_config,
            tags=data.get("tags", []),
        )

    def _parse_step(self, step_data: dict[str, Any], index: int) -> TestStep:
        """
        Parse a test step.

        Args:
            step_data: Step dictionary from YAML
            index: Step index for error reporting

        Returns:
            TestStep object

        Raises:
            TestParserError: If step is invalid
        """
        if not isinstance(step_data, dict):
            raise TestParserError(f"Step {index} must be a dictionary")

        # Validate required fields
        self._validate_required_fields(step_data, ["name", "action"], context=f"Step {index}")

        action_str = step_data["action"]

        # Validate action type
        try:
            action = ActionType(action_str.lower())
        except ValueError:
            # Allow custom actions
            action = action_str

        # Parse retry config for this step
        retry = None
        if "retry" in step_data:
            retry = self._parse_retry_config(step_data["retry"])

        return TestStep(
            name=step_data["name"],
            action=action,
            selector=step_data.get("selector"),
            value=step_data.get("value"),
            url=step_data.get("url"),
            timeout=step_data.get("timeout"),
            screenshot=step_data.get("screenshot", False),
            wait_for_navigation=step_data.get("wait_for_navigation", False),
            condition=step_data.get("condition"),
            retry=retry,
            selectors=step_data.get("selectors"),
            metadata=step_data.get("metadata", {}),
        )

    def _parse_evaluator(self, evaluator_data: dict[str, Any]) -> EvaluatorConfig:
        """
        Parse an evaluator configuration.

        Args:
            evaluator_data: Evaluator dictionary from YAML

        Returns:
            EvaluatorConfig object

        Raises:
            TestParserError: If evaluator is invalid
        """
        if not isinstance(evaluator_data, dict):
            raise TestParserError("Evaluator must be a dictionary")

        # Validate required fields
        self._validate_required_fields(evaluator_data, ["name", "type"])

        evaluator_type_str = evaluator_data["type"]

        # Validate evaluator type
        try:
            evaluator_type = EvaluatorType(evaluator_type_str)
        except ValueError:
            # Allow custom evaluator types
            evaluator_type = evaluator_type_str

        return EvaluatorConfig(
            name=evaluator_data["name"],
            type=evaluator_type,
            selector=evaluator_data.get("selector"),
            expected_value=evaluator_data.get("expected_value"),
            max_errors=evaluator_data.get("max_errors"),
            max_warnings=evaluator_data.get("max_warnings"),
            max_load_time=evaluator_data.get("max_load_time"),
            max_time=evaluator_data.get("max_time"),
            pattern=evaluator_data.get("pattern"),
            threshold=evaluator_data.get("threshold"),
        )

    def _parse_auth_config(self, auth_data: dict[str, Any]) -> AuthConfig:
        """
        Parse authentication configuration.

        Args:
            auth_data: Auth dictionary from YAML

        Returns:
            AuthConfig object

        Raises:
            TestParserError: If auth config is invalid
        """
        if not isinstance(auth_data, dict):
            raise TestParserError("Auth configuration must be a dictionary")

        self._validate_required_fields(auth_data, ["type"])

        return AuthConfig(
            type=auth_data["type"],
            username=auth_data.get("username"),
            password=auth_data.get("password"),
            token=auth_data.get("token"),
            provider=auth_data.get("provider"),
            client_id=auth_data.get("client_id"),
            client_secret=auth_data.get("client_secret"),
            headers=auth_data.get("headers"),
            cookies=auth_data.get("cookies"),
        )

    def _parse_browser_config(self, browser_data: dict[str, Any]) -> BrowserConfig:
        """
        Parse browser configuration.

        Args:
            browser_data: Browser dictionary from YAML

        Returns:
            BrowserConfig object

        Raises:
            TestParserError: If browser config is invalid
        """
        if not isinstance(browser_data, dict):
            raise TestParserError("Browser configuration must be a dictionary")

        viewport = browser_data.get("viewport", {"width": 1920, "height": 1080})
        if isinstance(viewport, dict):
            if "width" not in viewport or "height" not in viewport:
                raise TestParserError("Viewport must have 'width' and 'height' fields")
        else:
            raise TestParserError("Viewport must be a dictionary")

        return BrowserConfig(
            type=browser_data.get("type", "chromium"),
            headless=browser_data.get("headless", True),
            viewport=viewport,
            device=browser_data.get("device"),
            locale=browser_data.get("locale", "en-US"),
            timezone=browser_data.get("timezone"),
            permissions=browser_data.get("permissions", []),
            slow_mo=browser_data.get("slow_mo", 0),
            user_agent=browser_data.get("user_agent"),
            proxy=browser_data.get("proxy"),
            ignore_https_errors=browser_data.get("ignore_https_errors", False),
            accept_downloads=browser_data.get("accept_downloads", False),
            record_video=browser_data.get("record_video", False),
            record_har=browser_data.get("record_har", False),
        )

    def _parse_retry_config(self, retry_data: dict[str, Any]) -> RetryConfig:
        """
        Parse retry configuration.

        Args:
            retry_data: Retry dictionary from YAML

        Returns:
            RetryConfig object

        Raises:
            TestParserError: If retry config is invalid
        """
        # Handle various retry formats:
        # retry: null/None -> no retry
        # retry: true -> use defaults with max_attempts=3
        # retry: 5 -> max_attempts=5 with defaults
        # retry: {max_attempts: 3, delay_ms: 500} -> use specified values
        if retry_data is None:
            return None
        if isinstance(retry_data, bool):
            if retry_data:
                return RetryConfig(max_attempts=3, delay_ms=1000, backoff_multiplier=1.5)
            else:
                return None
        elif isinstance(retry_data, int):
            return RetryConfig(max_attempts=retry_data, delay_ms=1000, backoff_multiplier=1.5)
        elif not isinstance(retry_data, dict):
            raise TestParserError(
                f"Retry configuration must be a boolean, integer, or dictionary, got {type(retry_data).__name__}"
            )

        return RetryConfig(
            max_attempts=retry_data.get("max_attempts", 1),
            delay_ms=retry_data.get("delay_ms", 1000),
            backoff_multiplier=retry_data.get("backoff_multiplier", 1.5),
        )

    def _validate_required_fields(
        self, data: dict[str, Any], fields: list[str], context: str = ""
    ) -> None:
        """
        Validate that required fields are present in data.

        Args:
            data: Dictionary to validate
            fields: List of required field names
            context: Context string for error messages

        Raises:
            TestParserError: If any required field is missing
        """
        missing_fields = [field for field in fields if field not in data]
        if missing_fields:
            context_str = f" in {context}" if context else ""
            raise TestParserError(
                f"Missing required field(s){context_str}: {', '.join(missing_fields)}"
            )


def parse_yaml_test(file_path: str | Path) -> TestDefinition:
    """
    Convenience function to parse a YAML test file.

    Args:
        file_path: Path to the YAML test file

    Returns:
        TestDefinition object

    Raises:
        TestParserError: If parsing fails
    """
    parser = YAMLTestParser()
    return parser.parse_file(file_path)
