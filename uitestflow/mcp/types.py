"""Type definitions and error classes for MCP Playwright integration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ConsoleLogLevel(str, Enum):
    """Console log levels."""

    LOG = "log"
    INFO = "info"
    WARN = "warn"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class MCPErrorType(str, Enum):
    """Types of MCP errors."""

    BROWSER_ERROR = "browser_error"
    SELECTOR_ERROR = "selector_error"
    TIMEOUT_ERROR = "timeout_error"
    NAVIGATION_ERROR = "navigation_error"
    JAVASCRIPT_ERROR = "javascript_error"
    SCREENSHOT_ERROR = "screenshot_error"
    VALIDATION_ERROR = "validation_error"
    SERVER_ERROR = "server_error"


@dataclass
class ConsoleLog:
    """Console log message from browser."""

    level: ConsoleLogLevel
    message: str
    timestamp: datetime
    args: list[str] = field(default_factory=list)
    location: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "args": self.args,
            "location": self.location,
        }


@dataclass
class PageState:
    """Current state of the browser page."""

    url: str
    title: str
    viewport: dict[str, int]
    console_log_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cookies: list[dict[str, Any]] = field(default_factory=list)
    local_storage: dict[str, str] = field(default_factory=dict)
    session_storage: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "viewport": self.viewport,
            "console_log_count": self.console_log_count,
            "timestamp": self.timestamp.isoformat(),
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
        }


@dataclass
class Screenshot:
    """Screenshot metadata and data."""

    data: str  # Base64 encoded image
    size: int  # File size in bytes
    width: int | None = None
    height: int | None = None
    format: str = "png"
    full_page: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self.data,
            "size": self.size,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "full_page": self.full_page,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BrowserState:
    """Complete browser state snapshot."""

    is_running: bool
    page_state: PageState | None = None
    console_logs: list[ConsoleLog] = field(default_factory=list)
    active_contexts: int = 0
    active_pages: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_running": self.is_running,
            "page_state": self.page_state.to_dict() if self.page_state else None,
            "console_logs": [log.to_dict() for log in self.console_logs],
            "active_contexts": self.active_contexts,
            "active_pages": self.active_pages,
        }


@dataclass
class ToolResult:
    """Generic result from a tool execution."""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    error_type: MCPErrorType | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_type": self.error_type.value if self.error_type else None,
            "timestamp": self.timestamp.isoformat(),
        }


class MCPError(Exception):
    """Base exception for MCP errors."""

    def __init__(
        self,
        message: str,
        error_type: MCPErrorType = MCPErrorType.SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize MCP error.

        Args:
            message: Error message
            error_type: Type of error
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class BrowserError(MCPError):
    """Browser-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize browser error."""
        super().__init__(message, MCPErrorType.BROWSER_ERROR, details)


class SelectorError(MCPError):
    """Selector-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize selector error."""
        super().__init__(message, MCPErrorType.SELECTOR_ERROR, details)


class MCPTimeoutError(MCPError):
    """Timeout errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize timeout error."""
        super().__init__(message, MCPErrorType.TIMEOUT_ERROR, details)


class NavigationError(MCPError):
    """Navigation-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize navigation error."""
        super().__init__(message, MCPErrorType.NAVIGATION_ERROR, details)


class JavaScriptError(MCPError):
    """JavaScript execution errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize JavaScript error."""
        super().__init__(message, MCPErrorType.JAVASCRIPT_ERROR, details)


class ScreenshotError(MCPError):
    """Screenshot-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize screenshot error."""
        super().__init__(message, MCPErrorType.SCREENSHOT_ERROR, details)


class ValidationError(MCPError):
    """Validation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize validation error."""
        super().__init__(message, MCPErrorType.VALIDATION_ERROR, details)
