"""MCP Playwright server implementation."""

import asyncio
import importlib
import json
import logging
import sys
from typing import Any


# Import MCP using importlib to avoid namespace conflicts
_mcp_server_module = importlib.import_module("mcp.server")
FastMCP = _mcp_server_module.FastMCP

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from ..src.models import BrowserConfig
from .tools import TOOL_SCHEMAS, PlaywrightTools
from .types import BrowserState, PageState


logger = logging.getLogger(__name__)


class PlaywrightMCPServer:
    """
    MCP Server for Playwright browser automation.

    Exposes browser automation tools to Claude via the Model Context Protocol.
    """

    def __init__(
        self,
        browser_config: BrowserConfig | None = None,
        server_name: str = "playwright-mcp-server",
    ) -> None:
        """
        Initialize the MCP server.

        Args:
            browser_config: Browser configuration (uses defaults if None)
            server_name: Name of the MCP server
        """
        self.server_name = server_name
        self.browser_config = browser_config or BrowserConfig()

        # MCP server
        self.mcp = FastMCP(name=server_name)

        # Playwright instances
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Tools
        self.tools = PlaywrightTools()

        # Server state
        self._running = False

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all tools with the MCP server."""

        @self.mcp.tool()  # type: ignore[misc]
        async def navigate(url: str, timeout: int = 30000) -> str:
            """
            Navigate to a URL.

            Args:
                url: The URL to navigate to
                timeout: Navigation timeout in milliseconds (default: 30000)

            Returns:
                JSON string with navigation result
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.navigate(url, timeout)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def click(selector: str, timeout: int = 5000) -> str:
            """
            Click an element on the page.

            Args:
                selector: CSS, XPath, or text selector for the element
                timeout: Timeout in milliseconds (default: 5000)

            Returns:
                JSON string with click result
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.click(selector, timeout)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def fill(selector: str, value: str, timeout: int = 5000) -> str:
            """
            Fill an input field with a value.

            Args:
                selector: CSS, XPath, or text selector for the input field
                value: Value to fill in the input field
                timeout: Timeout in milliseconds (default: 5000)

            Returns:
                JSON string with fill result
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.fill(selector, value, timeout)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def wait_for_selector(
            selector: str, timeout: int = 5000, state: str = "visible"
        ) -> str:
            """
            Wait for an element to appear on the page.

            Args:
                selector: CSS, XPath, or text selector for the element
                timeout: Timeout in milliseconds (default: 5000)
                state: Element state to wait for (default: "visible")

            Returns:
                JSON string with wait result
            """
            if not self._page:
                await self.start_browser()
            # Cast state to correct type
            from typing import Literal, cast

            state_typed = cast("Literal['attached', 'detached', 'visible', 'hidden']", state)
            result = await self.tools.wait_for_selector(selector, timeout, state_typed)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def screenshot(full_page: bool = False) -> str:
            """
            Capture a screenshot of the current page.

            Args:
                full_page: Whether to capture the full scrollable page (default: False)

            Returns:
                JSON string with screenshot data (base64 encoded)
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.screenshot(full_page)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def get_page_state() -> str:
            """
            Get the current state of the page (URL, title, viewport, console logs).

            Returns:
                JSON string with page state
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.get_page_state()
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def get_text(selector: str, timeout: int = 5000) -> str:
            """
            Extract text content from an element.

            Args:
                selector: CSS, XPath, or text selector for the element
                timeout: Timeout in milliseconds (default: 5000)

            Returns:
                JSON string with extracted text
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.get_text(selector, timeout)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def evaluate_javascript(code: str) -> str:
            """
            Execute JavaScript code in the page context.

            Args:
                code: JavaScript code to execute

            Returns:
                JSON string with evaluation result
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.evaluate_javascript(code)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def get_console_logs(level: str | None = None, clear: bool = False) -> str:
            """
            Get console logs from the browser.

            Args:
                level: Filter by log level (error, warning, log, info, debug)
                clear: Clear logs after retrieving (default: False)

            Returns:
                JSON string with console logs
            """
            if not self._page:
                await self.start_browser()
            result = await self.tools.get_console_logs(level, clear)
            return json.dumps(result.to_dict(), indent=2)

        @self.mcp.tool()  # type: ignore[misc]
        async def close_browser() -> str:
            """
            Close the browser.

            Returns:
                JSON string with close result
            """
            result = await self.tools.close_browser()
            await self.cleanup()
            return json.dumps(result.to_dict(), indent=2)

    async def start_browser(self) -> None:
        """
        Start the browser and create page.

        Raises:
            BrowserError: If browser fails to start
        """
        if self._page:
            logger.info("Browser already started")
            return

        try:
            # Start Playwright
            if not self._playwright:
                self._playwright = await async_playwright().start()  # type: ignore[assignment]
                logger.info("Playwright started")

            # Launch browser
            browser_type = getattr(self._playwright, self.browser_config.type)
            launch_options: dict[str, Any] = {
                "headless": self.browser_config.headless,
            }

            if self.browser_config.slow_mo > 0:
                launch_options["slow_mo"] = float(self.browser_config.slow_mo)

            self._browser = await browser_type.launch(**launch_options)
            logger.info(f"Browser launched: {self.browser_config.type}")

            # Create context
            context_options: dict[str, Any] = {
                "viewport": self.browser_config.viewport,
                "locale": self.browser_config.locale,
                "ignore_https_errors": self.browser_config.ignore_https_errors,
                "accept_downloads": self.browser_config.accept_downloads,
            }

            if self.browser_config.user_agent:
                context_options["user_agent"] = self.browser_config.user_agent

            if self.browser_config.timezone:
                context_options["timezone_id"] = self.browser_config.timezone

            if self.browser_config.permissions:
                context_options["permissions"] = self.browser_config.permissions

            if self.browser_config.proxy:
                context_options["proxy"] = self.browser_config.proxy

            self._context = await self._browser.new_context(**context_options)
            logger.info("Browser context created")

            # Create page
            self._page = await self._context.new_page()
            logger.info("Page created")

            # Set page in tools
            self.tools.set_page(self._page)

        except Exception:
            logger.error("Failed to start browser", exc_info=True)
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
                logger.info("Page closed")

            if self._context:
                await self._context.close()
                self._context = None
                logger.info("Context closed")

            if self._browser:
                await self._browser.close()
                self._browser = None
                logger.info("Browser closed")

            if self._playwright:
                await self._playwright.stop()  # type: ignore[unreachable]
                self._playwright = None
                logger.info("Playwright stopped")

        except Exception:
            logger.error("Error during cleanup", exc_info=True)

    def is_running(self) -> bool:
        """
        Check if the server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running

    def is_browser_running(self) -> bool:
        """
        Check if the browser is running.

        Returns:
            True if browser is running, False otherwise
        """
        return self._browser is not None and self._page is not None

    async def get_browser_state(self) -> BrowserState:
        """
        Get current browser state.

        Returns:
            BrowserState snapshot
        """
        page_state = None
        if self._page:
            try:
                result = await self.tools.get_page_state()
                page_state_dict = result.data.get("page_state")
                if page_state_dict:
                    page_state = PageState(**page_state_dict)
            except Exception as e:
                logger.warning("Failed to get page state: %s", e)

        return BrowserState(
            is_running=self.is_browser_running(),
            page_state=page_state,
            console_logs=self.tools._console_logs,
            active_contexts=1 if self._context else 0,
            active_pages=1 if self._page else 0,
        )

    def list_tools(self) -> list[str]:
        """
        List all available tool names.

        Returns:
            List of tool names
        """
        return list(TOOL_SCHEMAS.keys())

    async def setup_tools(self) -> None:
        """Set up all tools (for testing purposes)."""
        # Tools are set up in __init__, this is a no-op

    async def start_server(self) -> None:
        """
        Start the MCP server.

        Note: This method is for testing purposes.
        For production use, call run_server() instead.
        """
        self._running = True
        logger.info(f"MCP server '{self.server_name}' started")

    async def stop_server(self) -> None:
        """Stop the MCP server."""
        self._running = False
        await self.cleanup()
        logger.info(f"MCP server '{self.server_name}' stopped")

    async def run_server(self) -> None:
        """
        Run the MCP server with stdio transport.

        This is the main entry point for running the server.
        It will run until interrupted (Ctrl+C).
        """
        try:
            self._running = True
            logger.info(f"Starting MCP server '{self.server_name}'...")

            # Run server (FastMCP handles stdio automatically)
            await self.mcp.run()

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception:
            logger.error("Server error", exc_info=True)
            raise
        finally:
            self._running = False
            await self.cleanup()
            logger.info("Server stopped")


async def main() -> None:
    """Main entry point for running the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Log to stderr to keep stdout clean for MCP
        ],
    )

    # Create and run server
    server = PlaywrightMCPServer()

    try:
        await server.run_server()
    except Exception as e:
        logger.error("Failed to run server: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
