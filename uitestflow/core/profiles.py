"""
Profile and configuration management for UITestFlow.

This module handles loading and managing test profiles from .uitest_profiles.yaml
files, supporting multiple environments with environment variable substitution.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from .exceptions import ProfileNotFoundError, ProfileValidationError
from .models import AuthConfig, BrowserConfig, NotificationConfig


class Profile(BaseModel):
    """Test profile containing environment-specific configuration."""

    id: str = Field(..., description="Profile identifier (e.g., 'local', 'staging', 'prod')")
    name: str = Field(..., description="Human-readable profile name")
    description: str | None = Field(default=None, description="Profile description")
    base_url: str = Field(..., description="Base URL for the application")
    auth: AuthConfig = Field(default_factory=AuthConfig, description="Authentication configuration")
    browser: BrowserConfig = Field(
        default_factory=BrowserConfig, description="Browser configuration"
    )
    notifications: NotificationConfig | None = Field(
        default=None, description="Notification configuration"
    )
    timeout: int = Field(default=30000, ge=1000, description="Default timeout in milliseconds")
    rate_limit_rpm: int = Field(default=60, ge=1, description="Rate limit in requests per minute")
    is_default: bool = Field(default=False, description="Whether this is the default profile")
    custom_config: dict[str, Any] = Field(
        default_factory=dict, description="Custom configuration values"
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, url: str) -> str:
        """Validate that base_url is not empty."""
        if not url or not url.strip():
            raise ValueError("base_url cannot be empty")
        return url.strip()


class ProfileManager:
    """Manages loading and accessing test profiles from YAML configuration."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize profile manager.

        Args:
            config_path: Path to profile configuration file. If None, searches for
                        .uitest_profiles.yaml in current directory and parent directories.
        """
        self.config_path = self._find_config_file(config_path)
        self.profiles: dict[str, Profile] = {}
        self.default_profile_id: str | None = None
        self.global_config: dict[str, Any] = {}
        self.raw_config: dict[str, Any] = {}

        if self.config_path:
            self._load_config()

    def _find_config_file(self, config_path: str | Path | None = None) -> Path | None:
        """Find profile configuration file.

        Searches in order:
        1. Provided config_path
        2. .uitest_profiles.yaml in current directory
        3. .uitest_profiles.yaml in parent directories (up to 5 levels)

        Args:
            config_path: Optional explicit path to config file

        Returns:
            Path to configuration file, or None if not found
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            return None

        # Check current directory and parents
        current = Path.cwd()
        for _ in range(5):
            config_file = current / ".uitest_profiles.yaml"
            if config_file.exists():
                return config_file
            if current.parent == current:
                break
            current = current.parent

        return None

    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in config values.

        Supports ${VAR_NAME} and ${VAR_NAME:-default_value} syntax.

        Args:
            value: Value to process (can be str, dict, list, or other)

        Returns:
            Value with environment variables substituted
        """
        if isinstance(value, str):
            # Match ${VAR_NAME} or ${VAR_NAME:-default}
            pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

            def replace_var(match: re.Match[str]) -> str:
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.environ.get(var_name, default_value)

            return re.sub(pattern, replace_var, value)

        if isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]

        return value

    def _load_config(self) -> None:
        """Load and parse YAML configuration file."""
        if not self.config_path:
            return

        try:
            with Path(self.config_path).open() as f:
                raw_config = yaml.safe_load(f)

            if not raw_config:
                return

            # Store raw config
            self.raw_config = raw_config

            # Substitute environment variables
            config = self._substitute_env_vars(raw_config)

            # Load default profile ID
            self.default_profile_id = config.get("default", "local")

            # Load global settings
            self.global_config = config.get("global", {})

            # Load profiles
            profiles_config = config.get("profiles", {})
            for profile_id, profile_data in profiles_config.items():
                try:
                    profile = self._parse_profile(profile_id, profile_data)
                    self.profiles[profile_id] = profile
                except Exception as e:
                    print(f"Warning: Failed to parse profile '{profile_id}': {e}")

        except Exception as e:
            print(f"Warning: Failed to load profile config from {self.config_path}: {e}")

    def _parse_auth(self, auth_data: dict[str, Any]) -> AuthConfig:
        """Parse authentication configuration from dict.

        Args:
            auth_data: Authentication configuration dictionary

        Returns:
            AuthConfig instance
        """
        return AuthConfig(
            auth_type=auth_data.get("type", "none"),
            username=auth_data.get("username"),
            password=auth_data.get("password"),
            token=auth_data.get("token"),
            api_url=auth_data.get("api_url"),
            api_token=auth_data.get("api_token"),
            api_secret=auth_data.get("api_secret"),
            client_id=auth_data.get("client_id"),
            client_secret=auth_data.get("client_secret"),
            token_url=auth_data.get("token_url"),
            scopes=auth_data.get("scopes", []),
            custom_headers=auth_data.get("custom_headers", {}),
        )

    def _parse_browser(self, browser_data: dict[str, Any]) -> BrowserConfig:
        """Parse browser configuration from dict.

        Args:
            browser_data: Browser configuration dictionary

        Returns:
            BrowserConfig instance
        """
        viewport_data = browser_data.get("viewport", {})

        return BrowserConfig(
            browser_type=browser_data.get("type", "chromium"),
            headless=browser_data.get("headless", True),
            viewport={
                "width": viewport_data.get("width", 1920),
                "height": viewport_data.get("height", 1080),
            },
            device=browser_data.get("device"),
            locale=browser_data.get("locale", "en-US"),
            timezone=browser_data.get("timezone", "America/Los_Angeles"),
            geolocation=browser_data.get("geolocation"),
            permissions=browser_data.get("permissions", []),
            slowmo=browser_data.get("slowmo", 0),
            timeout=browser_data.get("timeout", 30000),
            user_agent=browser_data.get("user_agent"),
            ignore_https_errors=browser_data.get("ignore_https_errors", False),
        )

    def _parse_notifications(self, notifications_data: dict[str, Any]) -> NotificationConfig | None:
        """Parse notification configuration from dict.

        Args:
            notifications_data: Notification configuration dictionary

        Returns:
            NotificationConfig instance or None if empty
        """
        if not notifications_data:
            return None

        return NotificationConfig(
            on_failure=notifications_data.get("on_failure", []),
            on_success=notifications_data.get("on_success", []),
            on_always=notifications_data.get("on_always", []),
        )

    def _parse_profile(self, profile_id: str, data: dict[str, Any]) -> Profile:
        """Parse a single profile from configuration.

        Args:
            profile_id: Profile identifier
            data: Profile configuration dictionary

        Returns:
            Profile instance

        Raises:
            ProfileValidationError: If profile data is invalid
        """
        try:
            # Get timeout from profile or global config
            timeout = data.get("timeout", self.global_config.get("timeout", 30000))

            # Get rate limit from profile or global config
            rate_limit = data.get("rate_limit", self.global_config.get("rate_limit", {}))
            rate_limit_rpm = (
                rate_limit.get("requests_per_minute", 60) if isinstance(rate_limit, dict) else 60
            )

            # Parse sub-configurations
            auth = self._parse_auth(data.get("auth", {}))
            browser = self._parse_browser(data.get("browser", {}))
            notifications = self._parse_notifications(data.get("notifications", {}))

            # Check if this is marked as default
            is_default = data.get("default", False) or profile_id == self.default_profile_id

            return Profile(
                id=profile_id,
                name=data.get("name", profile_id),
                description=data.get("description"),
                base_url=data["base_url"],
                auth=auth,
                browser=browser,
                notifications=notifications,
                timeout=timeout,
                rate_limit_rpm=rate_limit_rpm,
                is_default=is_default,
                custom_config=data.get("custom", {}),
            )

        except KeyError as e:
            raise ProfileValidationError(profile_id, [f"Missing required field: {e}"]) from e
        except Exception as e:
            raise ProfileValidationError(profile_id, [str(e)]) from e

    def get_profile(self, profile_id: str | None = None) -> Profile:
        """Get a profile by ID.

        Args:
            profile_id: Profile ID to retrieve. If None, returns default profile.

        Returns:
            Profile instance

        Raises:
            ProfileNotFoundError: If profile is not found
        """
        if not profile_id:
            profile_id = self.default_profile_id

        if not profile_id:
            raise ProfileNotFoundError("No default profile configured", list(self.profiles.keys()))

        profile = self.profiles.get(profile_id)
        if not profile:
            raise ProfileNotFoundError(profile_id, list(self.profiles.keys()))

        return profile

    def list_profiles(self) -> list[str]:
        """Get list of available profile IDs.

        Returns:
            List of profile IDs
        """
        return list(self.profiles.keys())

    def has_profiles(self) -> bool:
        """Check if any profiles are configured.

        Returns:
            True if at least one profile is configured
        """
        return len(self.profiles) > 0

    def get_default_profile_id(self) -> str | None:
        """Get the default profile ID.

        Returns:
            Default profile ID, or None if not configured

        The default profile is determined by:
        1. Profile with `default: true` in its configuration
        2. Top-level `default` field in configuration file
        3. None if neither is set
        """
        # First check for profile-level default flag
        for profile_id, profile in self.profiles.items():
            if profile.is_default:
                return profile_id

        # Fall back to top-level default
        return self.default_profile_id

    def validate_profile(self, profile_id: str) -> list[str]:
        """Validate a profile configuration.

        Args:
            profile_id: Profile ID to validate

        Returns:
            List of validation error messages (empty if valid)

        Raises:
            ProfileNotFoundError: If profile is not found
        """
        profile = self.get_profile(profile_id)
        errors: list[str] = []

        # Validate base_url
        if not profile.base_url or not profile.base_url.strip():
            errors.append("base_url is required and cannot be empty")

        # Validate auth configuration based on type
        if profile.auth.auth_type.value == "form":
            if not profile.auth.username or not profile.auth.password:
                errors.append("Form auth requires username and password")
        elif profile.auth.auth_type.value == "basic":
            if not profile.auth.username or not profile.auth.password:
                errors.append("Basic auth requires username and password")
        elif profile.auth.auth_type.value == "bearer":
            if not profile.auth.token:
                errors.append("Bearer auth requires token")
        elif profile.auth.auth_type.value == "jwt":
            if not profile.auth.api_url or not profile.auth.api_token:
                errors.append("JWT auth requires api_url and api_token")
        elif profile.auth.auth_type.value == "oauth":
            if not profile.auth.client_id or not profile.auth.client_secret:
                errors.append("OAuth requires client_id and client_secret")
        elif profile.auth.auth_type.value == "api_key":
            if not profile.auth.api_key:
                errors.append("API key auth requires api_key")

        # Validate browser configuration
        if profile.browser.timeout < 1000:
            errors.append("Browser timeout must be at least 1000ms")

        if profile.browser.viewport.width < 320 or profile.browser.viewport.height < 240:
            errors.append("Viewport dimensions are too small")

        return errors


# Global instance
_profile_manager: ProfileManager | None = None


def get_profile_manager() -> ProfileManager:
    """Get or create global profile manager instance.

    Returns:
        ProfileManager instance
    """
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


def reload_profile_manager() -> ProfileManager:
    """Force reload of profile manager.

    Returns:
        New ProfileManager instance
    """
    global _profile_manager
    _profile_manager = ProfileManager()
    return _profile_manager


def load_profile(profile_id: str | None = None) -> Profile:
    """Load a profile by ID.

    Args:
        profile_id: Profile ID to load. If None, loads default profile.

    Returns:
        Profile instance

    Raises:
        ProfileNotFoundError: If profile is not found
    """
    manager = get_profile_manager()
    return manager.get_profile(profile_id)


def list_available_profiles() -> list[str]:
    """Get list of available profile IDs.

    Returns:
        List of profile IDs
    """
    manager = get_profile_manager()
    return manager.list_profiles()
