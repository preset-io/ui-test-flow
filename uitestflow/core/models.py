"""
Core data models for UITestFlow.

This module defines the primary data structures used throughout the
application using Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TestStatus(str, Enum):
    """Status of a test run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ActionType(str, Enum):
    """Types of actions that can be performed in a test step."""

    GOTO = "goto"
    NAVIGATE = "navigate"  # Alias for GOTO
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    TYPE = "type"
    PRESS = "press"
    WAIT = "wait"  # Simple sleep/wait action
    WAIT_FOR = "wait_for"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    WAIT_FOR_TIMEOUT = "wait_for_timeout"
    EXPECT = "expect"
    ASSERT = "assert"  # Assertion action
    SCREENSHOT = "screenshot"
    HOVER = "hover"
    DRAG = "drag"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    EXECUTE_SCRIPT = "execute_script"
    GET_TEXT = "get_text"
    GET_PAGE_STATE = "get_page_state"
    EVALUATE_JAVASCRIPT = "evaluate_javascript"
    GET_CONSOLE_LOGS = "get_console_logs"
    CUSTOM = "custom"


class AuthType(str, Enum):
    """Types of authentication methods."""

    NONE = "none"
    FORM = "form"
    BASIC = "basic"
    BEARER = "bearer"
    JWT = "jwt"
    OAUTH = "oauth"
    API_KEY = "api_key"
    CUSTOM = "custom"


class BrowserType(str, Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    CHROME = "chrome"  # Google Chrome (branded)
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserFramework(str, Enum):
    """Browser automation frameworks."""

    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"  # Future support
    PUPPETEER = "puppeteer"  # Future support


class ProfileType(str, Enum):
    """Profile categorization types."""

    ENVIRONMENT = "environment"  # dev, staging, prod
    WORKFLOW = "workflow"  # pre-auth, authenticated, admin
    CUSTOM = "custom"


class ProfileExecutionMode(str, Enum):
    """Profile execution/startup modes."""

    AUTOMATED = "automated"  # Ready for automated testing
    MANUAL = "manual"  # Ready for manual testing (headed mode, paused)
    HYBRID = "hybrid"  # Mix of automated + manual verification steps


class LLMProvider(str, Enum):
    """LLM provider types."""

    CLAUDE_CODE_CLI = "claude-code-cli"  # Claude Code CLI
    CLAUDE_SDK = "claude-sdk"  # Claude Agent SDK
    CLAUDE_API = "claude-api"  # Direct Claude API
    OPENAI = "openai"  # OpenAI API
    OLLAMA = "ollama"  # Ollama local models
    CUSTOM = "custom"  # Custom LLM endpoint


class EvaluatorType(str, Enum):
    """Types of evaluators."""

    # Execution evaluators
    ALL_STEPS_COMPLETED = "all_steps_completed"
    NO_EXCEPTIONS = "no_exceptions"
    WITHIN_TIME_LIMIT = "within_time_limit"

    # Visual evaluators
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_HAS_TEXT = "element_has_text"
    ELEMENT_HAS_ATTRIBUTE = "element_has_attribute"
    SCREENSHOT_MATCHES = "screenshot_matches"

    # Functional evaluators
    URL_MATCHES = "url_matches"
    TITLE_MATCHES = "title_matches"
    NETWORK_REQUEST_MADE = "network_request_made"
    NETWORK_RESPONSE_STATUS = "network_response_status"
    LOCAL_STORAGE_CONTAINS = "local_storage_contains"

    # Performance evaluators
    PERFORMANCE = "performance"  # Alias for page load performance
    PAGE_LOAD_TIME = "page_load_time"
    TIME_TO_INTERACTIVE = "time_to_interactive"
    CORE_WEB_VITALS = "core_web_vitals"

    # Accessibility evaluators
    NO_A11Y_VIOLATIONS = "no_a11y_violations"
    COLOR_CONTRAST_SUFFICIENT = "color_contrast_sufficient"
    KEYBOARD_NAVIGABLE = "keyboard_navigable"

    # Console evaluators
    NO_CONSOLE_ERRORS = "no_console_errors"
    NO_CONSOLE_WARNINGS = "no_console_warnings"
    CONSOLE_CONTAINS = "console_contains"


class ScreenshotStrategy(str, Enum):
    """When to capture screenshots."""

    ALWAYS = "always"
    ON_ERROR = "on_error"
    KEY_POINTS = "key_points"
    BEFORE_AFTER = "before_after"
    NEVER = "never"


# ============================================================================
# MCP and LLM Configuration Models
# ============================================================================


class MCPMetadata(BaseModel):
    """Metadata for MCP-generated tests.

    Tracks information about how a test was generated using Claude/MCP.
    """

    generated_by: Literal["claude", "mcp"] = Field(
        default="claude",
        description="System that generated the test",
    )
    generation_model: str = Field(
        ...,
        description="Model used for generation (e.g., claude-3-5-haiku-20241022)",
    )
    generation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the test was generated",
    )
    generation_prompt: str = Field(
        ...,
        description="Original natural language description",
    )
    generation_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature used for generation",
    )
    tokens_used: int | None = Field(
        default=None,
        description="Total tokens used in generation",
    )
    generation_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional generation configuration",
    )

    def __str__(self) -> str:
        """String representation of MCP metadata."""
        return (
            f"MCPMetadata(model={self.generation_model}, "
            f"timestamp={self.generation_timestamp}, "
            f"tokens={self.tokens_used or 'N/A'})"
        )


class LLMConfig(BaseModel):
    """LLM configuration for test generation and execution.

    Defines settings for using LLMs with tests.
    """

    enabled: bool = Field(
        default=False,
        description="Whether LLM features are enabled",
    )
    provider: Literal["anthropic", "openai"] = Field(
        default="anthropic",
        description="LLM provider to use",
    )
    model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Model to use for generation",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens in response",
    )
    api_key: str | None = Field(
        default=None,
        description="API key (prefer environment variable)",
    )

    def __str__(self) -> str:
        """String representation of LLM config."""
        return f"LLMConfig(provider={self.provider}, model={self.model}, enabled={self.enabled})"


# ============================================================================
# Browser and Authentication Configuration Models
# ============================================================================


class DeviceEmulationConfig(BaseModel):
    """Device emulation configuration."""

    device_name: str | None = Field(
        default=None,
        description="Predefined device name (e.g., 'iPhone 12', 'Pixel 5', 'iPad Pro')",
    )
    viewport: dict[str, int] | None = Field(
        default=None, description="Custom viewport size {width, height}"
    )
    user_agent: str | None = Field(default=None, description="Custom user agent string")
    device_scale_factor: float = Field(
        default=1.0, ge=0.5, le=5.0, description="Device pixel ratio"
    )
    is_mobile: bool = Field(default=False, description="Whether to emulate mobile device")
    has_touch: bool = Field(default=False, description="Whether device has touch support")
    locale: str = Field(default="en-US", description="Device locale")
    timezone: str = Field(default="America/Los_Angeles", description="Device timezone")
    geolocation: dict[str, float] | None = Field(
        default=None, description="Geolocation {latitude, longitude, accuracy}"
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="Permissions to grant (e.g., ['geolocation', 'notifications'])",
    )


class InitStep(BaseModel):
    """Initialization step to run before tests."""

    name: str = Field(..., description="Step name")
    action: ActionType | str = Field(..., description="Action type")
    selector: str | None = Field(default=None, description="Element selector")
    value: str | dict[str, Any] | None = Field(default=None, description="Input value")
    url: str | None = Field(default=None, description="URL for navigation")
    timeout: int = Field(default=30000, description="Step timeout in milliseconds")
    wait_after: int = Field(default=0, description="Wait after step in milliseconds")
    screenshot: bool = Field(default=False, description="Capture screenshot")
    description: str | None = Field(default=None, description="Step description")
    critical: bool = Field(default=True, description="If true, init fails if this step fails")
    condition: str | None = Field(
        default=None, description="Conditional execution (e.g., 'element_visible(.login-button)')"
    )


class LLMProfileConfig(BaseModel):
    """Enhanced LLM configuration for profiles."""

    enabled: bool = Field(default=True, description="Enable LLM features")
    provider: LLMProvider = Field(default=LLMProvider.CLAUDE_CODE_CLI, description="LLM provider")
    model: str = Field(default="claude-sonnet-4-5", description="Model name/identifier")
    api_key_env: str | None = Field(
        default=None,
        description="Environment variable name for API key (e.g., 'ANTHROPIC_API_KEY')",
    )
    api_key: str | None = Field(default=None, description="Direct API key (prefer api_key_env)")
    base_url: str | None = Field(
        default=None, description="Custom API base URL (for Ollama, custom endpoints)"
    )
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Max tokens")
    timeout: int = Field(default=60, ge=1, description="Request timeout in seconds")

    # Claude Code CLI specific
    cli_command: str = Field(
        default="claude", description="CLI command (e.g., 'claude', 'claude-code')"
    )
    cli_args: list[str] = Field(
        default_factory=lambda: ["-p"],
        description="CLI arguments (e.g., ['-p', '--dangerously-allow-all-tools'])",
    )

    # Generation settings
    use_for_test_generation: bool = Field(default=True, description="Use LLM for test generation")
    use_for_selector_healing: bool = Field(
        default=True, description="Use LLM for selector healing when elements not found"
    )
    use_for_error_recovery: bool = Field(default=True, description="Use LLM for error recovery")


class ViewportConfig(BaseModel):
    """Browser viewport configuration."""

    width: int = Field(default=1920, ge=320, le=3840, description="Viewport width in pixels")
    height: int = Field(default=1080, ge=240, le=2160, description="Viewport height in pixels")


class BrowserConfig(BaseModel):
    """Browser configuration for test execution."""

    model_config = {"populate_by_name": True}

    browser_type: BrowserType = Field(
        default=BrowserType.CHROMIUM, description="Type of browser to use", alias="type"
    )
    framework: BrowserFramework = Field(
        default=BrowserFramework.PLAYWRIGHT, description="Browser automation framework"
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    viewport: ViewportConfig = Field(
        default_factory=ViewportConfig, description="Viewport dimensions"
    )
    device: str | None = Field(
        default=None, description="Device emulation (e.g., 'iPhone 12', 'Pixel 5')"
    )
    device_emulation: DeviceEmulationConfig | None = Field(
        default=None, description="Advanced device emulation configuration"
    )
    locale: str = Field(default="en-US", description="Browser locale")
    timezone: str = Field(default="America/Los_Angeles", description="Browser timezone")
    geolocation: dict[str, float] | None = Field(
        default=None, description="Geolocation override (latitude, longitude, accuracy)"
    )
    permissions: list[str] = Field(
        default_factory=list, description="Permissions to grant (e.g., 'geolocation')"
    )
    slowmo: int = Field(default=0, ge=0, description="Slow down actions by milliseconds")
    timeout: int = Field(default=30000, ge=1000, description="Default timeout in milliseconds")
    user_agent: str | None = Field(default=None, description="Custom user agent string")
    ignore_https_errors: bool = Field(default=False, description="Ignore HTTPS certificate errors")
    accept_downloads: bool = Field(default=False, description="Enable automatic download accepting")
    proxy: dict[str, str] | None = Field(
        default=None, description="Proxy configuration (server, username, password)"
    )
    record_video: bool = Field(default=False, description="Record video of test execution")
    record_har: bool = Field(default=False, description="Record HAR (HTTP Archive) file")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    model_config = {"populate_by_name": True}

    auth_type: AuthType = Field(
        default=AuthType.NONE, description="Authentication method", alias="type"
    )

    # Form/Basic auth
    username: str | None = Field(default=None, description="Username for form/basic auth")
    password: str | None = Field(default=None, description="Password for form/basic auth")

    # Bearer token
    token: str | None = Field(default=None, description="Bearer token")

    # JWT
    api_url: str | None = Field(default=None, description="JWT API URL")
    api_token: str | None = Field(default=None, description="JWT API token")
    api_secret: str | None = Field(default=None, description="JWT API secret")

    # OAuth
    client_id: str | None = Field(default=None, description="OAuth client ID")
    client_secret: str | None = Field(default=None, description="OAuth client secret")
    token_url: str | None = Field(default=None, description="OAuth token URL")
    scopes: list[str] = Field(default_factory=list, description="OAuth scopes")

    # API Key
    api_key: str | None = Field(default=None, description="API key value")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key")
    api_key_prefix: str | None = Field(
        default=None, description="Prefix for API key value (e.g., 'Bearer', 'Api-Key')"
    )

    # Custom auth
    custom_headers: dict[str, str] = Field(
        default_factory=dict, description="Custom headers for authentication"
    )


class NotificationConfig(BaseModel):
    """Notification configuration for test results."""

    on_failure: list[dict[str, str]] = Field(
        default_factory=list, description="Notifications to send on test failure"
    )
    on_success: list[dict[str, str]] = Field(
        default_factory=list, description="Notifications to send on test success"
    )
    on_always: list[dict[str, str]] = Field(
        default_factory=list, description="Notifications to always send"
    )


# ============================================================================
# Test Definition Models
# ============================================================================


class RetryConfig(BaseModel):
    """Retry configuration for test steps."""

    max_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    delay_ms: int = Field(default=1000, ge=0, description="Delay between retries in milliseconds")
    exponential_backoff: bool = Field(
        default=True, description="Use exponential backoff for retries"
    )


class TestStep(BaseModel):
    """Individual test step definition."""

    name: str = Field(..., description="Human-readable step name")
    action: ActionType | str = Field(..., description="Action to perform")
    selector: str | None = Field(default=None, description="CSS/XPath selector for element")
    value: str | dict[str, Any] | list | None = Field(
        default=None, description="Value for action (text to type, option to select, etc.)"
    )
    url: str | None = Field(default=None, description="URL for goto action")
    timeout: int | None = Field(default=None, description="Step-specific timeout in milliseconds")
    screenshot: bool = Field(default=False, description="Capture screenshot after this step")
    condition: str | None = Field(
        default=None, description="Conditional execution (e.g., 'element_visible(.warning)')"
    )
    retry: RetryConfig | None = Field(default=None, description="Retry configuration for step")
    description: str | None = Field(default=None, description="Detailed step description")
    wait_before: int | None = Field(
        default=None, description="Wait before executing step (milliseconds)"
    )
    wait_after: int | None = Field(
        default=None, description="Wait after executing step (milliseconds)"
    )


class EvaluatorConfig(BaseModel):
    """Evaluator configuration for test validation."""

    name: str = Field(..., description="Evaluator name")
    evaluator_type: EvaluatorType | str = Field(..., description="Type of evaluator")
    params: dict[str, Any] = Field(default_factory=dict, description="Evaluator parameters")
    required: bool = Field(
        default=True, description="Whether this evaluator must pass for test to pass"
    )
    weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Weight of this evaluator in overall score"
    )

    @property
    def type(self) -> EvaluatorType | str:
        """Alias for evaluator_type for backward compatibility."""
        return self.evaluator_type


class TestDefinition(BaseModel):
    """Complete test definition."""

    id: UUID = Field(default_factory=uuid4, description="Unique test ID")
    name: str = Field(..., description="Test name")
    description: str | None = Field(default=None, description="Test description")
    version: str = Field(default="1.0", description="Test definition version")

    # Test configuration
    url: str | None = Field(default=None, description="Base URL (can be overridden by profile)")
    steps: list[TestStep] = Field(..., description="Test steps to execute")
    evaluators: list[EvaluatorConfig] = Field(
        default_factory=list, description="Evaluators to validate test results"
    )

    # Execution settings
    browser_config: BrowserConfig | None = Field(default=None, description="Browser configuration")
    auth_config: AuthConfig | None = Field(default=None, description="Authentication configuration")
    timeout: int = Field(
        default=30000, ge=1000, description="Default timeout for actions in milliseconds"
    )
    retry_config: RetryConfig | None = Field(
        default=None, description="Default retry configuration"
    )

    # Screenshot settings
    screenshot_strategy: ScreenshotStrategy = Field(
        default=ScreenshotStrategy.ON_ERROR, description="Screenshot capture strategy"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Test tags for categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # MCP/LLM metadata
    mcp_metadata: MCPMetadata | None = Field(
        default=None, description="Metadata if test was generated via MCP/Claude"
    )
    llm_config: LLMConfig | None = Field(
        default=None, description="LLM configuration for this test"
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, steps: list[TestStep]) -> list[TestStep]:
        """Validate that test has at least one step."""
        if not steps:
            raise ValueError("Test must have at least one step")
        return steps


# ============================================================================
# Test Execution Models
# ============================================================================


class Screenshot(BaseModel):
    """Screenshot metadata."""

    id: UUID = Field(default_factory=uuid4, description="Screenshot ID")
    step_name: str | None = Field(default=None, description="Step name when screenshot was taken")
    step_index: int = Field(..., description="Step index (0-based)")
    url: str = Field(..., description="URL of screenshot file")
    thumbnail_url: str | None = Field(default=None, description="URL of thumbnail")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Capture timestamp")
    file_size: int | None = Field(default=None, description="File size in bytes")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")


class LogEntry(BaseModel):
    """Console log entry."""

    level: str = Field(..., description="Log level (log, info, warn, error)")
    message: str = Field(..., description="Log message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    source: str | None = Field(default=None, description="Log source (URL, line number)")
    stack_trace: str | None = Field(default=None, description="Stack trace for errors")


class StepResult(BaseModel):
    """Result of a test step execution."""

    step_name: str = Field(..., description="Name of the step")
    step_index: int = Field(..., description="Index of the step (0-based)")
    action: str = Field(..., description="Action performed")
    success: bool = Field(..., description="Whether the step succeeded")
    duration_ms: int = Field(..., description="Step duration in milliseconds")
    error_message: str | None = Field(default=None, description="Error message if step failed")
    screenshot_path: str | None = Field(default=None, description="Path to screenshot")

    # Phase 3: Claude guidance fields
    claude_guidance: str | None = Field(default=None, description="Claude's guidance for this step")
    adapted_selector: str | None = Field(
        default=None, description="Selector adapted by Claude if original failed"
    )
    error_recovery_attempted: bool = Field(
        default=False, description="Whether error recovery with Claude was attempted"
    )
    recovery_action: str | None = Field(default=None, description="Recovery action taken if any")
    page_state: dict[str, Any] | None = Field(
        default=None, description="Page state captured before step execution"
    )


class EvalResult(BaseModel):
    """Result of an evaluator execution."""

    evaluator_name: str = Field(..., description="Name of evaluator")
    passed: bool = Field(..., description="Whether evaluator passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0 (1.0 = perfect)")
    reason: str | None = Field(default=None, description="Reason for pass/fail")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    screenshot_path: str | None = Field(default=None, description="Path to related screenshot")
    duration_ms: int | None = Field(default=None, description="Evaluator execution time")
    evaluator_type: str = Field(..., description="Type of evaluator")


class TestResult(BaseModel):
    """Result of a test execution."""

    passed: bool = Field(..., description="Whether test passed overall")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall score (average of evaluators)")

    # Step results
    step_results: list[StepResult] = Field(
        default_factory=list, description="Detailed results for each step"
    )
    steps_executed: int = Field(..., description="Number of steps executed")
    steps_passed: int = Field(..., description="Number of steps that passed")
    steps_failed: int = Field(..., description="Number of steps that failed")

    # Evaluator results
    evaluator_results: list[EvalResult] = Field(
        default_factory=list, description="Results from all evaluators"
    )

    # Performance metrics
    total_duration_ms: int = Field(..., description="Total test duration in milliseconds")
    page_load_time_ms: int | None = Field(default=None, description="Initial page load time")
    time_to_interactive_ms: int | None = Field(default=None, description="Time to interactive")

    # Console logs
    console_errors: list[str] = Field(default_factory=list, description="Console error messages")
    console_warnings: list[str] = Field(
        default_factory=list, description="Console warning messages"
    )

    # Error details
    error_message: str | None = Field(default=None, description="Error message if test failed")
    error_step: str | None = Field(default=None, description="Step name where error occurred")
    error_screenshot_path: str | None = Field(
        default=None, description="Path to screenshot at error"
    )
    error_screenshot_url: str | None = Field(default=None, description="URL of screenshot at error")


class TestRun(BaseModel):
    """Test run instance with execution context and results."""

    id: UUID = Field(default_factory=uuid4, description="Unique run ID")
    test_definition: TestDefinition = Field(..., description="Test definition being executed")
    test_id: UUID | None = Field(default=None, description="ID of test definition")
    test_name: str | None = Field(default=None, description="Name of test (denormalized)")

    # Execution context
    profile: str | None = Field(default=None, description="Profile used for execution")
    triggered_by: str = Field(
        default="manual", description="How test was triggered (manual, ci, scheduled, api)"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context (PR number, commit SHA, etc.)"
    )

    # Status and timing
    status: TestStatus = Field(default=TestStatus.PENDING, description="Current run status")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    duration_ms: int | None = Field(default=None, description="Total duration in milliseconds")

    # Results
    result: TestResult | None = Field(default=None, description="Test results")

    # Artifacts
    screenshots: list[Screenshot] = Field(default_factory=list, description="Screenshots captured")
    video_url: str | None = Field(default=None, description="URL of video recording")
    trace_url: str | None = Field(default=None, description="URL of Playwright trace")
    logs: list[LogEntry] = Field(default_factory=list, description="Console logs")
    har_url: str | None = Field(default=None, description="URL of HAR file (network logs)")

    # Phase 3: Claude guidance metadata
    guidance_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata about Claude guidance during execution"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    def mark_started(self) -> None:
        """Mark the test run as started."""
        self.status = TestStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: TestResult) -> None:
        """Mark the test run as completed with results."""
        self.status = TestStatus.COMPLETED if result.passed else TestStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.result = result
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def mark_aborted(self, reason: str) -> None:
        """Mark the test run as aborted."""
        self.status = TestStatus.ABORTED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        if not self.result:
            self.result = TestResult(
                passed=False,
                score=0.0,
                steps_executed=0,
                steps_passed=0,
                steps_failed=0,
                total_duration_ms=self.duration_ms or 0,
                error_message=f"Test aborted: {reason}",
            )


# ============================================================================
# Profile Models
# ============================================================================


class Profile(BaseModel):
    """
    Profile configuration for environment setup and testing.

    Supports multi-layered profiles with init steps, LLM integration,
    and flexible execution modes for automated/manual testing.
    """

    id: str = Field(..., description="Profile identifier")
    name: str = Field(..., description="Profile name")
    description: str | None = Field(default=None, description="Profile description")
    profile_type: ProfileType = Field(
        default=ProfileType.ENVIRONMENT, description="Profile categorization type"
    )
    execution_mode: ProfileExecutionMode = Field(
        default=ProfileExecutionMode.AUTOMATED, description="Execution/startup mode"
    )
    base_url: str = Field(..., description="Base URL for the environment")
    init_steps: list[InitStep] = Field(
        default_factory=list, description="Initialization steps to run before tests"
    )
    auth_config: dict[str, Any] = Field(
        default_factory=dict, description="Authentication configuration"
    )
    browser_config: BrowserConfig = Field(
        default_factory=BrowserConfig, description="Browser configuration"
    )
    llm_config: LLMProfileConfig | None = Field(
        default=None, description="LLM configuration for test generation and healing"
    )
    notification_config: dict[str, Any] = Field(
        default_factory=dict, description="Notification configuration"
    )
    tags: list[str] = Field(default_factory=list, description="Profile tags for categorization")
