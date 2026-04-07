"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data sent to and received from the API.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Authentication Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Login request schema."""

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: dict = Field(..., description="User information")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")


# ============================================================================
# Test Definition Schemas
# ============================================================================


class TestStepSchema(BaseModel):
    """Test step schema."""

    name: str
    action: str
    selector: str | None = None
    value: str | dict | list | None = None
    url: str | None = None
    timeout: int | None = None
    screenshot: bool = False
    condition: str | None = None
    retry: dict | None = None
    description: str | None = None
    wait_before: int | None = None
    wait_after: int | None = None


class EvaluatorSchema(BaseModel):
    """Evaluator configuration schema."""

    name: str
    evaluator_type: str = Field(..., alias="type")
    params: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    weight: float = Field(default=1.0, ge=0.0, le=1.0)

    class Config:
        populate_by_name = True


class TestDefinitionCreate(BaseModel):
    """Schema for creating a test definition."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(default="1.0")
    url: str | None = None
    steps: list[TestStepSchema] = Field(..., min_length=1)
    evaluators: list[EvaluatorSchema] = Field(default_factory=list)
    browser_config: dict | None = None
    auth_config: dict | None = None
    timeout: int = Field(default=30000, ge=1000)
    retry_config: dict | None = None
    screenshot_strategy: str = Field(default="on_error")
    tags: list[str] = Field(default_factory=list)


class TestDefinitionUpdate(BaseModel):
    """Schema for updating a test definition."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    version: str | None = None
    url: str | None = None
    steps: list[TestStepSchema] | None = None
    evaluators: list[EvaluatorSchema] | None = None
    browser_config: dict | None = None
    auth_config: dict | None = None
    timeout: int | None = Field(None, ge=1000)
    retry_config: dict | None = None
    screenshot_strategy: str | None = None
    tags: list[str] | None = None


class TestDefinitionResponse(BaseModel):
    """Schema for test definition response."""

    id: UUID
    org_id: UUID
    name: str
    description: str | None
    version: str
    url: str | None
    steps: list[dict]
    evaluators: list[dict]
    browser_config: dict
    auth_config: dict
    timeout: int
    retry_config: dict
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None

    class Config:
        from_attributes = True


class TestDefinitionListResponse(BaseModel):
    """Schema for list of test definitions."""

    tests: list[TestDefinitionResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Test Run Schemas
# ============================================================================


class TestRunCreate(BaseModel):
    """Schema for creating a test run."""

    test_id: UUID = Field(..., description="Test definition ID")
    profile: str | None = Field(None, description="Profile to use")
    triggered_by: str = Field(default="api", description="How test was triggered")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class TestRunResponse(BaseModel):
    """Schema for test run response."""

    id: UUID
    test_id: UUID
    test_name: str
    org_id: UUID
    profile: str | None
    triggered_by: str
    context: dict
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    result: dict | None
    video_url: str | None
    trace_url: str | None
    har_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunListResponse(BaseModel):
    """Schema for list of test runs."""

    runs: list[TestRunResponse]
    total: int
    page: int
    page_size: int


class TestRunAbortRequest(BaseModel):
    """Schema for aborting a test run."""

    reason: str = Field(default="User requested abort")


# ============================================================================
# Profile Schemas
# ============================================================================


class ProfileCreate(BaseModel):
    """Schema for creating a profile."""

    id: str | None = Field(None, description="Profile ID (auto-generated if not provided)")
    name: str = Field(..., min_length=1, max_length=255, description="Profile name")
    description: str | None = Field(None, description="Profile description")
    profile_type: str = Field(
        default="environment", description="Profile type: environment, workflow, or custom"
    )
    execution_mode: str = Field(
        default="automated", description="Execution mode: automated, manual, or hybrid"
    )
    base_url: str = Field(..., description="Base URL for the environment")
    init_steps: list[dict] = Field(
        default_factory=list, description="Initialization steps to run before tests"
    )
    auth_config: dict = Field(
        default_factory=lambda: {"type": "none"}, description="Authentication configuration"
    )
    browser_config: dict = Field(
        default_factory=lambda: {
            "browser_type": "chromium",
            "framework": "playwright",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
        },
        description="Browser configuration",
    )
    llm_config: dict = Field(
        default_factory=dict, description="LLM configuration for test generation and healing"
    )
    notification_config: dict = Field(
        default_factory=dict, description="Notification configuration"
    )
    tags: list[str] = Field(default_factory=list, description="Profile tags for categorization")

    org_id: UUID | None = Field(
        None, description="Organization ID (auto-generated if not provided)"
    )


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Profile name")
    description: str | None = Field(None, description="Profile description")
    profile_type: str | None = Field(
        None, description="Profile type: environment, workflow, or custom"
    )
    execution_mode: str | None = Field(
        None, description="Execution mode: automated, manual, or hybrid"
    )
    base_url: str | None = Field(None, description="Base URL for the environment")
    init_steps: list[dict] | None = Field(
        None, description="Initialization steps to run before tests"
    )
    auth_config: dict | None = Field(None, description="Authentication configuration")
    browser_config: dict | None = Field(None, description="Browser configuration")
    llm_config: dict | None = Field(None, description="LLM configuration")
    notification_config: dict | None = Field(None, description="Notification configuration")
    tags: list[str] | None = Field(None, description="Profile tags")


class ProfileResponse(BaseModel):
    """Schema for profile response."""

    id: str
    org_id: UUID
    name: str
    description: str | None = None
    profile_type: str = "environment"  # environment, workflow, custom
    execution_mode: str = "automated"  # automated, manual, hybrid
    base_url: str
    init_steps: list[dict] = Field(default_factory=list)
    auth_config: dict
    browser_config: dict
    llm_config: dict = Field(default_factory=dict)
    notification_config: dict
    tags: list[str] = Field(default_factory=list)
    environment_status: str | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """Schema for list of profiles."""

    profiles: list[ProfileResponse]
    total: int


class ProfileTestResponse(BaseModel):
    """Schema for profile connectivity test response."""

    success: bool = Field(..., description="Whether the connection test succeeded")
    latency_ms: int | None = Field(None, description="Response latency in milliseconds")
    error: str | None = Field(None, description="Error message if test failed")
    tested_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the test was performed"
    )


class ProfileStartRequest(BaseModel):
    """Schema for starting a profile (executing init steps)."""

    execution_mode: str | None = Field(None, description="Override profile's execution mode")
    headless: bool | None = Field(None, description="Override browser headless setting")
    with_claude: bool = Field(default=True, description="Enable Claude AI guidance")


class ProfileStartResponse(BaseModel):
    """Schema for profile start response."""

    success: bool = Field(..., description="Whether profile initialization succeeded")
    session_id: str | None = Field(None, description="Browser session ID if successful")
    steps_executed: int = Field(default=0, description="Number of init steps executed")
    errors: list[str] = Field(default_factory=list, description="Errors encountered during init")
    message: str = Field(..., description="Status message")


class AIProfileGenerateRequest(BaseModel):
    """Schema for AI profile generation request."""

    description: str = Field(
        ...,
        min_length=10,
        description="Natural language description of the profile(s) to generate",
    )
    provider: str = Field(
        default="anthropic", description="AI provider to use (anthropic, openai, etc.)"
    )
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Model to use for generation",
    )
    api_key_env: str = Field(
        default="ANTHROPIC_API_KEY",
        description="Environment variable name for API key",
    )


class AIProfileGenerateResponse(BaseModel):
    """Schema for AI profile generation response."""

    success: bool = Field(..., description="Whether generation succeeded")
    profiles: list[ProfileCreate] = Field(
        default_factory=list, description="Generated profile configurations"
    )
    message: str = Field(..., description="Status or error message")
    reasoning: str | None = Field(None, description="AI reasoning about the generated profiles")


class AITestGenerateRequest(BaseModel):
    """Schema for AI test generation request from environment profile."""

    profile_id: str = Field(..., description="Profile ID to generate tests from")
    coverage_level: str = Field(
        default="medium", description="Coverage level: smoke, canary, medium, or deep"
    )
    crawl_depth: int = Field(default=1, ge=0, le=5, description="Site crawl depth (0-5)")
    provider: str = Field(default="anthropic", description="AI provider to use")
    model: str = Field(
        default="claude-sonnet-4-5-20250929", description="Model to use for generation"
    )
    api_key_env: str = Field(
        default="ANTHROPIC_API_KEY", description="Environment variable name for API key"
    )


class AITestGenerateResponse(BaseModel):
    """Schema for AI test generation response."""

    success: bool = Field(..., description="Whether generation succeeded")
    tests: list[dict] = Field(default_factory=list, description="Generated test definitions")
    count: int = Field(default=0, description="Number of tests generated")
    coverage_level: str = Field(default="", description="Coverage level used")
    site_data: dict | None = Field(None, description="Crawled site data")
    message: str = Field(..., description="Status or error message")
    reasoning: str | None = Field(None, description="AI reasoning about the generated tests")


# ============================================================================
# Analytics Schemas
# ============================================================================


class AnalyticsSummaryResponse(BaseModel):
    """Schema for analytics summary."""

    total_tests: int
    total_runs: int
    total_runs_last_7_days: int
    total_runs_last_30_days: int
    pass_rate_7_days: float
    pass_rate_30_days: float
    avg_duration_ms: float
    most_run_tests: list[dict]
    recent_failures: list[dict]
    flaky_tests: list[dict]


class TrendDataPoint(BaseModel):
    """Schema for a trend data point."""

    date: str
    total: int
    passed: int
    failed: int
    avg_duration_ms: float


class AnalyticsTrendsResponse(BaseModel):
    """Schema for analytics trends."""

    trends: list[TrendDataPoint]
    period: str


# ============================================================================
# Screenshot Schemas
# ============================================================================


class ScreenshotResponse(BaseModel):
    """Schema for screenshot response."""

    id: UUID
    test_run_id: UUID
    step_name: str | None
    step_index: int
    url: str
    thumbnail_url: str | None
    timestamp: datetime
    file_size: int | None

    class Config:
        from_attributes = True


# ============================================================================
# Generic Schemas
# ============================================================================


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str | None = None
    code: str | None = None
    request_id: str | None = Field(None, description="Request ID for tracking")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime


# ============================================================================
# WebSocket Schemas
# ============================================================================


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""

    type: str = Field(
        ..., description="Message type: status, progress, log, screenshot, complete, error"
    )
    data: dict = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestProgressUpdate(BaseModel):
    """Test progress update schema."""

    run_id: UUID
    status: str
    current_step: int | None = None
    total_steps: int | None = None
    step_name: str | None = None
    message: str | None = None
    screenshot_url: str | None = None
