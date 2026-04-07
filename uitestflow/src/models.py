"""Core data models for UITestFlow."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ActionType(str, Enum):
    """Supported test step actions."""

    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    WAIT = "wait"  # Simple sleep/wait action
    WAIT_FOR = "wait_for"
    EXPECT = "expect"
    ASSERT = "assert"  # Assertion action
    SCREENSHOT = "screenshot"
    EXECUTE = "execute"
    CUSTOM = "custom"


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class EvaluatorType(str, Enum):
    """Types of evaluators."""

    EXECUTION_SUCCESSFUL = "execution_successful"
    ALL_STEPS_COMPLETED = "all_steps_completed"
    NO_EXCEPTIONS = "no_exceptions"
    CONSOLE_ERRORS = "console_errors"
    CONSOLE_WARNINGS = "console_warnings"
    URL_MATCHES = "url_matches"
    TITLE_MATCHES = "title_matches"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_HAS_TEXT = "element_has_text"
    PERFORMANCE = "performance"
    PAGE_LOAD_TIME = "page_load_time"


@dataclass
class AuthConfig:
    """Authentication configuration."""

    type: str  # "form", "oauth", "basic", "bearer", "api_key", "custom"
    username: str | None = None
    password: str | None = None
    token: str | None = None
    provider: str | None = None  # For OAuth: "okta", "auth0", etc.
    client_id: str | None = None
    client_secret: str | None = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    # API Key auth
    api_key: str | None = None
    api_key_header: str = "X-API-Key"
    api_key_prefix: str | None = None  # e.g., "Bearer", "Api-Key"


@dataclass
class BrowserConfig:
    """Browser configuration."""

    type: str = "chromium"  # "chromium", "firefox", "webkit"
    headless: bool = True
    viewport: dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    device: str | None = None  # Device emulation: "iPhone 12", "Pixel 5", etc.
    locale: str = "en-US"
    timezone: str | None = None
    permissions: list[str] = field(default_factory=list)
    slow_mo: int = 0  # Slow down actions by N milliseconds
    user_agent: str | None = None
    proxy: dict[str, str] | None = None
    ignore_https_errors: bool = False
    accept_downloads: bool = False
    record_video: bool = False
    record_har: bool = False


@dataclass
class RetryConfig:
    """Retry configuration for test steps."""

    max_attempts: int = 1
    delay_ms: int = 1000
    backoff_multiplier: float = 1.5


@dataclass
class TestStep:
    """A single test step."""

    name: str
    action: ActionType | str
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    timeout: int | None = None  # milliseconds
    screenshot: bool = False
    wait_for_navigation: bool = False
    condition: str | None = None  # Conditional execution
    retry: RetryConfig | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # For multiple selectors (fill action with multiple inputs)
    selectors: list[dict[str, str]] | None = None


@dataclass
class EvaluatorConfig:
    """Configuration for a test evaluator."""

    name: str
    type: EvaluatorType | str
    selector: str | None = None
    expected_value: str | None = None
    max_errors: int | None = None
    max_warnings: int | None = None
    max_load_time: int | None = None  # milliseconds
    max_time: int | None = None  # milliseconds
    pattern: str | None = None  # For regex matching
    threshold: float | None = None


@dataclass
class TestDefinition:
    """Complete test definition."""

    name: str
    version: str = "1.0"
    description: str | None = None
    url: str | None = None
    steps: list[TestStep] = field(default_factory=list)
    evaluators: list[EvaluatorConfig] = field(default_factory=list)

    # Optional configurations
    auth: AuthConfig | None = None
    browser_config: BrowserConfig | None = None
    timeout: int = 30000  # milliseconds
    retry_config: RetryConfig | None = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StepResult:
    """Result of executing a single test step."""

    step_name: str
    step_index: int
    action: str
    success: bool
    duration_ms: int
    error_message: str | None = None
    screenshot_path: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of an evaluator."""

    passed: bool
    score: float  # 0.0 to 1.0
    evaluator_name: str
    evaluator_type: str
    reason: str | None = None
    details: dict[str, Any] | None = None
    screenshot_path: str | None = None


@dataclass
class Screenshot:
    """Screenshot metadata."""

    id: UUID
    step_name: str
    step_index: int
    file_path: str
    timestamp: datetime
    url: str | None = None
    file_size: int | None = None


@dataclass
class LogEntry:
    """Console or application log entry."""

    level: str  # "info", "warn", "error", "debug"
    message: str
    timestamp: datetime
    source: str | None = None  # "console", "app", "browser"
    metadata: dict[str, Any] | None = None


@dataclass
class TestResult:
    """Complete test execution result."""

    passed: bool
    score: float  # Overall score (average of evaluators)

    # Step results
    step_results: list[StepResult]
    steps_executed: int
    steps_passed: int
    steps_failed: int

    # Evaluator results
    evaluator_results: list[EvalResult]

    # Performance metrics
    total_duration_ms: int
    page_load_time_ms: int | None = None
    time_to_interactive_ms: int | None = None

    # Error details
    error_message: str | None = None
    error_screenshot_path: str | None = None

    # Console logs
    console_errors: list[str] = field(default_factory=list)
    console_warnings: list[str] = field(default_factory=list)


@dataclass
class TestRun:
    """Complete test run with all artifacts."""

    id: UUID
    test_definition: TestDefinition
    status: TestStatus

    # Execution context
    profile: str | None = None
    triggered_by: str = "manual"  # "manual", "ci", "scheduled", "api"
    context: dict[str, Any] = field(default_factory=dict)

    # Status and timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None

    # Results
    result: TestResult | None = None

    # Artifacts
    screenshots: list[Screenshot] = field(default_factory=list)
    video_path: str | None = None
    trace_path: str | None = None
    har_path: str | None = None
    logs: list[LogEntry] = field(default_factory=list)

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.started_at is None:
            self.started_at = datetime.utcnow()
