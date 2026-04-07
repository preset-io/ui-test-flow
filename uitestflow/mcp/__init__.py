"""MCP Playwright integration for UITestFlow.

This module provides Model Context Protocol (MCP) integration for UITestFlow,
enabling Claude-powered browser automation and test generation.

Main Components:
- PlaywrightMCPServer: MCP server that exposes browser automation tools
- PlaywrightTools: Collection of browser automation tools
- Type definitions: PageState, Screenshot, ConsoleLog, etc.
- Error classes: MCPError, BrowserError, SelectorError, etc.

Example:
    >>> from uitestflow.mcp import PlaywrightMCPServer
    >>> server = PlaywrightMCPServer()
    >>> await server.run_server()
"""

from .playwright_server import PlaywrightMCPServer, main
from .tools import TOOL_SCHEMAS, PlaywrightTools
from .types import (
    BrowserError,
    BrowserState,
    ConsoleLog,
    ConsoleLogLevel,
    JavaScriptError,
    MCPError,
    MCPErrorType,
    MCPTimeoutError,
    NavigationError,
    PageState,
    Screenshot,
    ScreenshotError,
    SelectorError,
    ToolResult,
    ValidationError,
)


__all__ = [
    # Server
    "PlaywrightMCPServer",
    "main",
    # Tools
    "PlaywrightTools",
    "TOOL_SCHEMAS",
    # Types
    "BrowserState",
    "ConsoleLog",
    "ConsoleLogLevel",
    "PageState",
    "Screenshot",
    "ToolResult",
    # Errors
    "BrowserError",
    "JavaScriptError",
    "MCPError",
    "MCPErrorType",
    "MCPTimeoutError",
    "NavigationError",
    "ScreenshotError",
    "SelectorError",
    "ValidationError",
]
