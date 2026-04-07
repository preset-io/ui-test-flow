"""MCP tool definitions for browser automation."""

import base64
import logging
from typing import Any, Literal

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .types import (
    BrowserError,
    ConsoleLog,
    ConsoleLogLevel,
    JavaScriptError,
    MCPTimeoutError,
    NavigationError,
    PageState,
    Screenshot,
    ScreenshotError,
    SelectorError,
    ToolResult,
)


logger = logging.getLogger(__name__)


class PlaywrightTools:
    """Collection of Playwright automation tools for MCP."""

    def __init__(self, page: Page | None = None) -> None:
        """
        Initialize Playwright tools.

        Args:
            page: Playwright page instance (optional, can be set later)
        """
        self.page = page
        self._console_logs: list[ConsoleLog] = []
        self._setup_console_listener()

    def set_page(self, page: Page) -> None:
        """
        Set the Playwright page instance.

        Args:
            page: Playwright page instance
        """
        self.page = page
        self._setup_console_listener()

    def _setup_console_listener(self) -> None:
        """Set up console message listener."""
        if self.page:
            self.page.on("console", self._handle_console_message)

    def _handle_console_message(self, msg: Any) -> None:
        """Handle console messages from the page."""
        try:
            from datetime import datetime

            level_str = msg.type.lower()
            level = ConsoleLogLevel(
                level_str if level_str in ConsoleLogLevel.__members__.values() else "log"
            )

            console_log = ConsoleLog(
                level=level,
                message=msg.text,
                timestamp=datetime.utcnow(),
                args=[str(arg) for arg in msg.args] if hasattr(msg, "args") else [],
                location=str(msg.location) if hasattr(msg, "location") else None,
            )
            self._console_logs.append(console_log)
        except Exception as e:
            logger.warning("Failed to handle console message: %s", e)

    def _ensure_page(self) -> Page:
        """Ensure page is available."""
        if not self.page:
            raise BrowserError("No page available. Browser may not be started.")
        return self.page

    async def navigate(self, url: str, timeout: int = 30000) -> ToolResult:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            timeout: Navigation timeout in milliseconds (default: 30000)

        Returns:
            ToolResult with success status and final URL

        Raises:
            NavigationError: If navigation fails
            MCPTimeoutError: If navigation times out

        Example:
            >>> result = await tools.navigate("https://example.com")
            >>> print(result.data["url"])
            "https://example.com/"
        """
        try:
            page = self._ensure_page()
            response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            final_url = page.url
            status_code = response.status if response else None

            logger.info("Navigated to %s (status: %s)", final_url, status_code)

            return ToolResult(
                success=True,
                message=f"Successfully navigated to {final_url}",
                data={
                    "url": final_url,
                    "status_code": status_code,
                    "redirected": final_url != url,
                },
            )
        except PlaywrightTimeoutError as e:
            raise MCPTimeoutError(
                f"Navigation timed out after {timeout}ms: {e}", {"url": url, "timeout": timeout}
            )
        except BrowserError:
            raise
        except Exception as e:
            raise NavigationError(f"Navigation failed: {e}", {"url": url})

    async def click(self, selector: str, timeout: int = 5000) -> ToolResult:
        """
        Click an element matching the selector.

        Args:
            selector: CSS, XPath, or text selector
            timeout: Timeout in milliseconds (default: 5000)

        Returns:
            ToolResult with success status

        Raises:
            SelectorError: If selector is not found
            MCPTimeoutError: If operation times out

        Example:
            >>> result = await tools.click("button.submit")
            >>> assert result.success
        """
        try:
            page = self._ensure_page()
            await page.click(selector, timeout=timeout)

            logger.info("Clicked element: %s", selector)

            return ToolResult(
                success=True,
                message=f"Successfully clicked element: {selector}",
                data={"selector": selector},
            )
        except PlaywrightTimeoutError as e:
            raise MCPTimeoutError(
                f"Element not found or not clickable: {selector}",
                {"selector": selector, "timeout": timeout, "error": str(e)},
            )
        except Exception as e:
            raise SelectorError(f"Click failed: {e}", {"selector": selector})

    async def fill(self, selector: str, value: str, timeout: int = 5000) -> ToolResult:
        """
        Fill an input field with a value.

        Args:
            selector: CSS, XPath, or text selector for the input field
            value: Value to fill
            timeout: Timeout in milliseconds (default: 5000)

        Returns:
            ToolResult with success status

        Raises:
            SelectorError: If selector is not found or not an input
            MCPTimeoutError: If operation times out

        Example:
            >>> result = await tools.fill("input[name='username']", "admin")
            >>> assert result.success
        """
        try:
            page = self._ensure_page()
            await page.fill(selector, value, timeout=timeout)

            logger.info("Filled element %s with value", selector)

            return ToolResult(
                success=True,
                message=f"Successfully filled element: {selector}",
                data={"selector": selector, "value_length": len(value)},
            )
        except PlaywrightTimeoutError as e:
            raise MCPTimeoutError(
                f"Input field not found: {selector}",
                {"selector": selector, "timeout": timeout, "error": str(e)},
            )
        except Exception as e:
            raise SelectorError(f"Fill failed: {e}", {"selector": selector})

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 5000,
        state: Literal["attached", "detached", "visible", "hidden"] = "visible",
    ) -> ToolResult:
        """
        Wait for an element matching the selector.

        Args:
            selector: CSS, XPath, or text selector
            timeout: Timeout in milliseconds (default: 5000)
            state: Element state to wait for: "attached", "detached", "visible", "hidden"

        Returns:
            ToolResult with success status

        Raises:
            MCPTimeoutError: If element doesn't appear within timeout

        Example:
            >>> result = await tools.wait_for_selector("#loading", state="hidden")
            >>> assert result.success
        """
        try:
            page = self._ensure_page()
            await page.wait_for_selector(selector, timeout=timeout, state=state)

            logger.info("Element found: %s (state: %s)", selector, state)

            return ToolResult(
                success=True,
                message=f"Element {selector} is {state}",
                data={"selector": selector, "state": state},
            )
        except PlaywrightTimeoutError as e:
            raise MCPTimeoutError(
                f"Element not {state}: {selector}",
                {"selector": selector, "state": state, "timeout": timeout, "error": str(e)},
            )
        except Exception as e:
            raise SelectorError(f"Wait failed: {e}", {"selector": selector})

    async def screenshot(self, full_page: bool = False) -> ToolResult:
        """
        Capture a screenshot of the current page.

        Args:
            full_page: Whether to capture the full scrollable page (default: False)

        Returns:
            ToolResult with screenshot data (base64 encoded)

        Raises:
            ScreenshotError: If screenshot capture fails

        Example:
            >>> result = await tools.screenshot(full_page=True)
            >>> image_data = result.data["screenshot"]["data"]
        """
        try:
            page = self._ensure_page()
            screenshot_bytes = await page.screenshot(full_page=full_page, type="png")

            screenshot_data = base64.b64encode(screenshot_bytes).decode("utf-8")
            size = len(screenshot_bytes)

            viewport = page.viewport_size

            screenshot = Screenshot(
                data=screenshot_data,
                size=size,
                width=viewport.get("width") if viewport else None,
                height=viewport.get("height") if viewport else None,
                full_page=full_page,
            )

            logger.info("Screenshot captured (%s bytes, full_page=%s)", size, full_page)

            return ToolResult(
                success=True,
                message=f"Screenshot captured ({size} bytes)",
                data={"screenshot": screenshot.to_dict()},
            )
        except Exception as e:
            raise ScreenshotError(f"Screenshot failed: {e}", {"full_page": full_page})

    async def get_page_state(self) -> ToolResult:
        """
        Get the current page state.

        Returns:
            ToolResult with page state information

        Raises:
            BrowserError: If unable to get page state

        Example:
            >>> result = await tools.get_page_state()
            >>> print(result.data["page_state"]["url"])
        """
        try:
            page = self._ensure_page()

            url = page.url
            title = await page.title()
            viewport_size = page.viewport_size
            # Ensure viewport is dict[str, int]
            if viewport_size:
                viewport: dict[str, int] = {
                    "width": viewport_size["width"],
                    "height": viewport_size["height"],
                }
            else:
                viewport = {"width": 0, "height": 0}

            page_state = PageState(
                url=url,
                title=title,
                viewport=viewport,
                console_log_count=len(self._console_logs),
            )

            logger.info("Retrieved page state: %s", url)

            return ToolResult(
                success=True,
                message="Page state retrieved successfully",
                data={"page_state": page_state.to_dict()},
            )
        except Exception as e:
            raise BrowserError(f"Failed to get page state: {e}")

    async def get_text(self, selector: str, timeout: int = 5000) -> ToolResult:
        """
        Extract text content from an element.

        Args:
            selector: CSS, XPath, or text selector
            timeout: Timeout in milliseconds (default: 5000)

        Returns:
            ToolResult with extracted text

        Raises:
            SelectorError: If selector is not found
            MCPTimeoutError: If operation times out

        Example:
            >>> result = await tools.get_text("h1")
            >>> print(result.data["text"])
        """
        try:
            page = self._ensure_page()

            # Wait for element and get text
            element = await page.wait_for_selector(selector, timeout=timeout)
            if not element:
                return ToolResult(
                    success=True,
                    message=f"Element not found: {selector}",
                    data={"text": "", "selector": selector},
                )

            text = await element.text_content() or ""
            text = text.strip()

            logger.info(f"Extracted text from {selector}: {text[:50]}...")

            return ToolResult(
                success=True,
                message=f"Text extracted from {selector}",
                data={"text": text, "selector": selector, "length": len(text)},
            )
        except PlaywrightTimeoutError as e:
            raise MCPTimeoutError(
                f"Element not found: {selector}",
                {"selector": selector, "timeout": timeout, "error": str(e)},
            )
        except Exception as e:
            raise SelectorError(f"Text extraction failed: {e}", {"selector": selector})

    async def evaluate_javascript(self, code: str) -> ToolResult:
        """
        Execute JavaScript code in the page context.

        Args:
            code: JavaScript code to execute

        Returns:
            ToolResult with evaluation result

        Raises:
            JavaScriptError: If JavaScript execution fails

        Example:
            >>> result = await tools.evaluate_javascript("document.title")
            >>> print(result.data["result"])
        """
        try:
            page = self._ensure_page()

            result = await page.evaluate(code)

            logger.info(f"Executed JavaScript: {code[:50]}...")

            return ToolResult(
                success=True,
                message="JavaScript executed successfully",
                data={"result": result, "code_length": len(code)},
            )
        except Exception as e:
            raise JavaScriptError(f"JavaScript execution failed: {e}", {"code": code[:100]})

    async def get_console_logs(self, level: str | None = None, clear: bool = False) -> ToolResult:
        """
        Get console logs from the browser.

        Args:
            level: Filter by log level (error, warning, log, info, debug)
            clear: Whether to clear logs after retrieving (default: False)

        Returns:
            ToolResult with console logs

        Example:
            >>> result = await tools.get_console_logs(level="error")
            >>> for log in result.data["logs"]:
            ...     print(log["message"])
        """
        try:
            logs = self._console_logs

            # Filter by level if specified
            if level:
                try:
                    log_level = ConsoleLogLevel(level.lower())
                    logs = [log for log in logs if log.level == log_level]
                except ValueError:
                    # Invalid level, return all logs
                    pass

            log_dicts = [log.to_dict() for log in logs]

            # Clear logs if requested
            if clear:
                self._console_logs.clear()

            logger.info(f"Retrieved {len(log_dicts)} console logs (level={level}, clear={clear})")

            return ToolResult(
                success=True,
                message=f"Retrieved {len(log_dicts)} console logs",
                data={"logs": log_dicts, "count": len(log_dicts), "level": level},
            )
        except Exception as e:
            raise BrowserError(f"Failed to get console logs: {e}", {"level": level})

    async def close_browser(self) -> ToolResult:
        """
        Close the browser (marks for closure, actual cleanup handled by server).

        Returns:
            ToolResult with success status

        Example:
            >>> result = await tools.close_browser()
            >>> assert result.success
        """
        try:
            logger.info("Browser close requested")

            return ToolResult(
                success=True,
                message="Browser will be closed",
                data={"closed": True},
            )
        except Exception as e:
            raise BrowserError(f"Failed to close browser: {e}")


# Tool schemas for MCP registration
TOOL_SCHEMAS = {
    "navigate": {
        "name": "navigate",
        "description": "Navigate to a URL in the browser",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Navigation timeout in milliseconds",
                    "default": 30000,
                },
            },
            "required": ["url"],
        },
    },
    "click": {
        "name": "click",
        "description": "Click an element on the page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS, XPath, or text selector for the element",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 5000,
                },
            },
            "required": ["selector"],
        },
    },
    "fill": {
        "name": "fill",
        "description": "Fill an input field with a value",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS, XPath, or text selector for the input field",
                },
                "value": {
                    "type": "string",
                    "description": "Value to fill in the input field",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 5000,
                },
            },
            "required": ["selector", "value"],
        },
    },
    "wait_for_selector": {
        "name": "wait_for_selector",
        "description": "Wait for an element to appear on the page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS, XPath, or text selector for the element",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 5000,
                },
                "state": {
                    "type": "string",
                    "description": "Element state to wait for",
                    "enum": ["attached", "detached", "visible", "hidden"],
                    "default": "visible",
                },
            },
            "required": ["selector"],
        },
    },
    "screenshot": {
        "name": "screenshot",
        "description": "Capture a screenshot of the current page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "full_page": {
                    "type": "boolean",
                    "description": "Whether to capture the full scrollable page",
                    "default": False,
                },
            },
        },
    },
    "get_page_state": {
        "name": "get_page_state",
        "description": "Get the current state of the page (URL, title, viewport, console logs)",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    "get_text": {
        "name": "get_text",
        "description": "Extract text content from an element",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS, XPath, or text selector for the element",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 5000,
                },
            },
            "required": ["selector"],
        },
    },
    "evaluate_javascript": {
        "name": "evaluate_javascript",
        "description": "Execute JavaScript code in the page context",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "JavaScript code to execute",
                },
            },
            "required": ["code"],
        },
    },
    "get_console_logs": {
        "name": "get_console_logs",
        "description": "Get console logs from the browser",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "description": "Filter by log level",
                    "enum": ["log", "info", "warn", "warning", "error", "debug"],
                },
                "clear": {
                    "type": "boolean",
                    "description": "Clear logs after retrieving",
                    "default": False,
                },
            },
        },
    },
    "close_browser": {
        "name": "close_browser",
        "description": "Close the browser",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
}
