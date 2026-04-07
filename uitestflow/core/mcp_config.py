"""
MCP-specific configuration for UITestFlow.

This module provides configuration settings for Model Context Protocol (MCP)
integration with Claude for test generation and guided execution.
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP-specific settings for Claude integration.

    These settings control the MCP Playwright server, Claude client,
    and test generation/execution features.
    """

    model_config = SettingsConfigDict(
        env_prefix="UITESTFLOW_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Feature flags
    enabled: bool = Field(
        default=False,
        description="Enable MCP features (test generation, guided execution)",
    )

    # MCP Server configuration
    server_enabled: bool = Field(
        default=False,
        description="Enable standalone MCP server",
    )
    server_port: int = Field(
        default=3001,
        ge=1024,
        le=65535,
        description="Port for MCP server (HTTP transport)",
    )
    server_transport: Literal["stdio", "http"] = Field(
        default="stdio",
        description="MCP server transport protocol",
    )
    server_host: str = Field(
        default="localhost",
        description="Host for MCP server (HTTP transport)",
    )

    # Claude API configuration
    claude_enabled: bool = Field(
        default=True,
        description="Enable Claude integration for test generation",
    )
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model to use for test generation",
    )
    claude_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=8192,
        description="Maximum tokens for Claude responses",
    )
    claude_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for Claude generation (0=deterministic, 1=creative)",
    )
    claude_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Timeout for Claude API calls in seconds",
    )

    # Test generation configuration
    generation_enabled: bool = Field(
        default=True,
        description="Enable natural language test generation",
    )
    generation_auto_save: bool = Field(
        default=True,
        description="Automatically save generated tests to YAML files",
    )
    generation_output_dir: str = Field(
        default="./generated_tests",
        description="Directory to save generated test files",
    )
    generation_include_metadata: bool = Field(
        default=True,
        description="Include MCPMetadata in generated tests",
    )

    # Guided execution configuration
    guided_execution_enabled: bool = Field(
        default=True,
        description="Enable Claude-guided test execution",
    )
    guidance_detail_level: Literal["minimal", "standard", "verbose"] = Field(
        default="standard",
        description="Level of detail in Claude guidance",
    )
    guidance_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts with Claude guidance",
    )
    guidance_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for guidance requests in seconds",
    )

    # Selector adaptation configuration
    selector_adaptation_enabled: bool = Field(
        default=True,
        description="Enable Claude-powered selector adaptation",
    )
    selector_max_alternatives: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum alternative selectors to try",
    )

    # Error recovery configuration
    error_recovery_enabled: bool = Field(
        default=True,
        description="Enable Claude-powered error recovery",
    )
    error_recovery_max_attempts: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum error recovery attempts per step",
    )

    # Page state capture configuration
    page_state_capture_enabled: bool = Field(
        default=True,
        description="Capture page state for Claude context",
    )
    page_state_capture_console: bool = Field(
        default=True,
        description="Capture console logs in page state",
    )
    page_state_capture_cookies: bool = Field(
        default=False,
        description="Capture cookies in page state (may contain sensitive data)",
    )
    page_state_capture_storage: bool = Field(
        default=False,
        description="Capture localStorage/sessionStorage (may contain sensitive data)",
    )

    # Performance tuning
    batch_requests: bool = Field(
        default=False,
        description="Batch multiple guidance requests (experimental)",
    )
    cache_responses: bool = Field(
        default=True,
        description="Cache Claude responses for identical requests",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds",
    )

    # Logging and debugging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="MCP-specific log level",
    )
    log_guidance: bool = Field(
        default=True,
        description="Log Claude guidance to console/file",
    )
    log_selector_adaptations: bool = Field(
        default=True,
        description="Log selector adaptation events",
    )
    log_recovery_attempts: bool = Field(
        default=True,
        description="Log error recovery attempts",
    )

    @field_validator("claude_model")
    @classmethod
    def validate_claude_model(cls, v: str) -> str:
        """Validate Claude model name."""
        valid_models = [
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        if v not in valid_models:
            raise ValueError(f"Invalid Claude model: {v}. Must be one of {valid_models}")
        return v

    @field_validator("guidance_detail_level")
    @classmethod
    def validate_guidance_level(cls, v: str) -> str:
        """Validate guidance detail level."""
        valid_levels = ["minimal", "standard", "verbose"]
        if v not in valid_levels:
            raise ValueError(f"Invalid guidance detail level: {v}. Must be one of {valid_levels}")
        return v

    def validate(self) -> list[str]:
        """Validate MCP configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Check if MCP is enabled but Claude is not available
        if self.enabled and not self.claude_enabled:
            errors.append(
                "MCP is enabled but Claude integration is disabled. "
                "Enable claude_enabled or disable MCP features."
            )

        # Check if guided execution requires Claude
        if self.guided_execution_enabled and not self.claude_enabled:
            errors.append(
                "Guided execution requires Claude integration. "
                "Enable claude_enabled or disable guided_execution_enabled."
            )

        # Check if selector adaptation requires guided execution
        if self.selector_adaptation_enabled and not self.guided_execution_enabled:
            errors.append(
                "Selector adaptation requires guided execution. "
                "Enable guided_execution_enabled or disable selector_adaptation_enabled."
            )

        # Check if error recovery requires guided execution
        if self.error_recovery_enabled and not self.guided_execution_enabled:
            errors.append(
                "Error recovery requires guided execution. "
                "Enable guided_execution_enabled or disable error_recovery_enabled."
            )

        return errors
