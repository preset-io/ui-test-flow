"""
Configuration management for UITestFlow.

This module handles loading and managing configuration from multiple sources
with a clear hierarchy: CLI > profile > .env > defaults.

Priority order (highest to lowest):
1. Command-line options (--profile, --base-url, --headless, etc.)
2. Profile from .uitest_profiles.yaml
3. .env file in current directory
4. ~/.uitestflow (user config file)
5. Environment variables
6. Built-in defaults
"""

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError
from .mcp_config import MCPSettings


class UITestFlowSettings(BaseSettings):
    """Global UITestFlow settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_prefix="UITESTFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API key for Claude integration"
    )
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key (optional alternative)"
    )

    # Default settings
    default_profile: str = Field(default="local", description="Default profile to use")
    default_browser: str = Field(default="chromium", description="Default browser type")
    default_headless: bool = Field(default=True, description="Default headless mode")
    default_timeout: int = Field(default=30000, description="Default timeout in milliseconds")

    # Storage settings
    storage_backend: str = Field(
        default="local", description="Storage backend (local, s3, gcs, azure)"
    )
    storage_path: str = Field(
        default="./uitestflow-data", description="Local storage path for artifacts"
    )
    s3_bucket: str | None = Field(default=None, description="S3 bucket name for artifacts")
    s3_region: str | None = Field(default=None, description="S3 region")
    aws_access_key_id: str | None = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: str | None = Field(default=None, description="AWS secret access key")

    # Database settings (for web/API mode)
    database_url: str = Field(
        default="sqlite:///./uitestflow.db", description="Database connection URL"
    )

    # Redis settings (for async task queue)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Server settings
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8018, description="Server port")
    server_workers: int = Field(default=1, description="Number of server workers")

    # Security settings
    secret_key: str = Field(
        default="changeme-in-production", description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(
        default=60 * 24, description="JWT expiration time in minutes"
    )

    # Feature flags
    enable_video_recording: bool = Field(
        default=False, description="Enable video recording by default"
    )
    enable_tracing: bool = Field(default=True, description="Enable Playwright tracing")
    enable_har_recording: bool = Field(default=True, description="Enable HAR recording")

    # Logging
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    log_format: str = Field(default="json", description="Log format (json, text)")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Max requests per rate limit window")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")

    # MCP-specific settings (loaded from MCPSettings)
    mcp: MCPSettings = Field(
        default_factory=MCPSettings,
        description="MCP integration settings for Claude-powered features",
    )


class Config:
    """Manages UITestFlow configuration from multiple sources."""

    def __init__(self, profile: str | None = None, **overrides: Any) -> None:
        """Initialize configuration.

        Args:
            profile: Profile ID to load
            **overrides: Configuration overrides from CLI or other sources
        """
        self._settings: UITestFlowSettings | None = None
        self._profile_id = profile
        self._overrides = overrides
        self._config: dict[str, Any] = {}
        self._sources: dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources in priority order."""
        # 1. Load global settings from environment and .env files
        self._settings = UITestFlowSettings()

        # 2. Load from user config file (~/.uitestflow)
        user_config_file = Path.home() / ".uitestflow"
        if user_config_file.exists():
            self._load_env_file(user_config_file, "~/.uitestflow")

        # 3. Load from .env in current directory (already loaded by pydantic-settings)
        cwd_env_file = Path.cwd() / ".env"
        if cwd_env_file.exists():
            self._load_env_file(cwd_env_file, ".env (current dir)")

        # 4. Load from profile if specified
        if self._profile_id:
            try:
                from .profiles import load_profile

                profile = load_profile(self._profile_id)
                self._config["profile"] = profile
                self._sources["profile"] = f"Profile '{self._profile_id}'"

                # Extract profile settings into config
                self._config["base_url"] = profile.base_url
                self._sources["base_url"] = f"Profile '{self._profile_id}'"

                self._config["auth"] = profile.auth
                self._sources["auth"] = f"Profile '{self._profile_id}'"

                self._config["browser"] = profile.browser
                self._sources["browser"] = f"Profile '{self._profile_id}'"

                if profile.notifications:
                    self._config["notifications"] = profile.notifications
                    self._sources["notifications"] = f"Profile '{self._profile_id}'"

            except Exception as e:
                raise ConfigurationError(f"Failed to load profile '{self._profile_id}': {e}") from e

        # 5. Apply CLI overrides (highest priority)
        for key, value in self._overrides.items():
            if value is not None:
                self._config[key] = value
                self._sources[key] = "CLI override"

        # 6. Apply defaults from settings for keys not yet set
        for field_name, field_info in UITestFlowSettings.model_fields.items():
            if field_name not in self._config:
                value = getattr(self._settings, field_name)
                if value is not None:
                    self._config[field_name] = value
                    self._sources[field_name] = "Default/Environment"

    def _load_env_file(self, file_path: Path, source_name: str) -> None:
        """Load configuration from an env file.

        Args:
            file_path: Path to env file
            source_name: Human-readable source name for tracking
        """
        try:
            with Path(file_path).open() as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]

                        # Store in config if not already set
                        if key not in self._config:
                            self._config[key] = value
                            self._sources[key] = source_name
        except Exception:
            # Silently ignore errors reading config files
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def get_source(self, key: str) -> str:
        """Get the source of a configuration value.

        Args:
            key: Configuration key

        Returns:
            Human-readable source description
        """
        return self._sources.get(key, "Not set")

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary of all configuration values
        """
        return self._config.copy()

    def get_all_with_sources(self) -> dict[str, tuple[Any, str]]:
        """Get all configuration values with their sources.

        Returns:
            Dictionary mapping keys to (value, source) tuples
        """
        result: dict[str, tuple[Any, str]] = {}
        for key in self._config:
            result[key] = (self._config[key], self._sources.get(key, "Unknown"))
        return result

    @property
    def settings(self) -> UITestFlowSettings:
        """Get the global settings object.

        Returns:
            UITestFlowSettings instance
        """
        if self._settings is None:
            self._settings = UITestFlowSettings()
        return self._settings

    @property
    def profile_id(self) -> str | None:
        """Get the current profile ID.

        Returns:
            Profile ID or None
        """
        return self._profile_id

    @property
    def profile(self) -> Any:
        """Get the current profile object.

        Returns:
            Profile instance or None
        """
        return self._config.get("profile")

    @property
    def base_url(self) -> str | None:
        """Get base URL from configuration.

        Returns:
            Base URL or None
        """
        return self.get("base_url")

    @property
    def anthropic_api_key(self) -> str | None:
        """Get Anthropic API key.

        Returns:
            API key or None
        """
        return (
            self._config.get("anthropic_api_key")
            or self._config.get("ANTHROPIC_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
        )

    @property
    def openai_api_key(self) -> str | None:
        """Get OpenAI API key.

        Returns:
            API key or None
        """
        return (
            self._config.get("openai_api_key")
            or self._config.get("OPENAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

    @property
    def mcp(self) -> MCPSettings:
        """Get MCP settings.

        Returns:
            MCPSettings instance
        """
        return self.settings.mcp

    def validate(self) -> list[str]:
        """Validate the current configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Check for required configuration based on usage mode
        if self.profile:
            # Validate profile-specific requirements
            if not self.base_url:
                errors.append("base_url is required when using a profile")

        # Validate API keys if MCP/LLM features are needed
        if self.settings.mcp.enabled and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY must be set when MCP features are enabled")

        # Validate MCP configuration
        if self.settings.mcp.enabled:
            mcp_errors = self.settings.mcp.validate()
            errors.extend(mcp_errors)

        # Validate storage configuration
        storage_backend = self.get("storage_backend", "local")
        if storage_backend == "s3":
            if not self.settings.s3_bucket:
                errors.append("s3_bucket is required when using S3 storage backend")
            if not self.settings.s3_region:
                errors.append("s3_region is required when using S3 storage backend")

        return errors


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global config instance, creating it if necessary.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def init_config(profile: str | None = None, **overrides: Any) -> Config:
    """Initialize global configuration with specific profile and overrides.

    Args:
        profile: Profile ID to load
        **overrides: Configuration overrides

    Returns:
        Config instance
    """
    global _config
    _config = Config(profile=profile, **overrides)
    return _config


def reload_config() -> Config:
    """Reload configuration from all sources.

    Returns:
        New Config instance
    """
    global _config
    _config = Config()
    return _config
