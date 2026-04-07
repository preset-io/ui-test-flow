"""
Core business logic for UITestFlow.

This package contains shared components including:
- Configuration and profile management
- Core data models
- Test parser (NLP + Structured)
- Test execution engine
- Browser session manager (Playwright)
- LLM integration (Claude via MCP)
- Screenshot & recording manager
- Evaluators
"""

from .config import Config, UITestFlowSettings, get_config, init_config, reload_config
from .exceptions import (
    AuthenticationError,
    BrowserError,
    BrowserLaunchError,
    BrowserTimeoutError,
    ConfigurationError,
    EvaluatorError,
    NotificationError,
    ProfileNotFoundError,
    ProfileValidationError,
    StorageError,
    TestDefinitionError,
    TestExecutionError,
    TestParseError,
    TestValidationError,
    UITestFlowError,
)
from .models import (
    ActionType,
    AuthConfig,
    AuthType,
    BrowserConfig,
    BrowserType,
    EvalResult,
    EvaluatorConfig,
    EvaluatorType,
    LogEntry,
    NotificationConfig,
    RetryConfig,
    Screenshot,
    ScreenshotStrategy,
    TestDefinition,
    TestResult,
    TestRun,
    TestStatus,
    TestStep,
    ViewportConfig,
)
from .profiles import (
    Profile,
    ProfileManager,
    get_profile_manager,
    list_available_profiles,
    load_profile,
    reload_profile_manager,
)


__all__ = [
    # Configuration
    "Config",
    "UITestFlowSettings",
    "get_config",
    "init_config",
    "reload_config",
    # Exceptions
    "UITestFlowError",
    "ConfigurationError",
    "ProfileNotFoundError",
    "ProfileValidationError",
    "TestDefinitionError",
    "TestParseError",
    "TestValidationError",
    "TestExecutionError",
    "BrowserError",
    "BrowserLaunchError",
    "BrowserTimeoutError",
    "AuthenticationError",
    "EvaluatorError",
    "StorageError",
    "NotificationError",
    # Models - Enums
    "TestStatus",
    "ActionType",
    "AuthType",
    "BrowserType",
    "EvaluatorType",
    "ScreenshotStrategy",
    # Models - Configuration
    "ViewportConfig",
    "BrowserConfig",
    "AuthConfig",
    "NotificationConfig",
    "RetryConfig",
    # Models - Test Definition
    "TestStep",
    "EvaluatorConfig",
    "TestDefinition",
    # Models - Test Execution
    "Screenshot",
    "LogEntry",
    "EvalResult",
    "TestResult",
    "TestRun",
    # Profiles
    "Profile",
    "ProfileManager",
    "get_profile_manager",
    "load_profile",
    "list_available_profiles",
    "reload_profile_manager",
]
