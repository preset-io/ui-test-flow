"""Browser session manager using Playwright for UITestFlow."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from uitestflow.core.models import BrowserConfig, Screenshot


logger = logging.getLogger(__name__)


class BrowserManagerError(Exception):
    """Exception raised for browser manager errors."""


class BrowserSession:
    """Represents an active browser session with context and page."""

    def __init__(
        self,
        browser: Browser,
        context: BrowserContext,
        page: Page,
        session_id: str,
        config: BrowserConfig,
    ):
        """
        Initialize a browser session.

        Args:
            browser: Playwright browser instance
            context: Browser context
            page: Page instance
            session_id: Unique session identifier
            config: Browser configuration
        """
        self.browser = browser
        self.context = context
        self.page = page
        self.session_id = session_id
        self.config = config
        self.screenshots: list[Screenshot] = []
        self.console_messages: list[dict] = []
        self.created_at = datetime.utcnow()
        self.closed = False
        self._cleanup_callback = None

        # Set up console message listener
        self.page.on("console", self._handle_console_message)

        # Set up close listener to detect when browser window is closed
        self.context.on("close", self._handle_context_close)

    def _handle_context_close(self):
        """Handle browser context close event."""
        self.closed = True
        logger.info(f"Browser context closed for session {self.session_id}")
        if self._cleanup_callback:
            # Schedule cleanup callback (will run in event loop)
            asyncio.create_task(self._cleanup_callback(self.session_id))

    def set_cleanup_callback(self, callback):
        """Set callback to be called when context is closed."""
        self._cleanup_callback = callback

    def _handle_console_message(self, msg):
        """Handle console messages from the page."""
        self.console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.utcnow(),
        })

    async def screenshot(
        self,
        path: str | Path,
        step_name: str,
        step_index: int,
        full_page: bool = False,
    ) -> Screenshot:
        """
        Capture a screenshot of the current page.

        Args:
            path: File path to save the screenshot
            step_name: Name of the test step
            step_index: Index of the test step
            full_page: Whether to capture the full scrollable page

        Returns:
            Screenshot metadata object

        Raises:
            BrowserManagerError: If screenshot capture fails
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            await self.page.screenshot(path=str(path), full_page=full_page)

            screenshot = Screenshot(
                id=uuid4(),
                step_name=step_name,
                step_index=step_index,
                file_path=str(path),
                url=self.page.url,
                timestamp=datetime.utcnow(),
                file_size=path.stat().st_size if path.exists() else None,
            )

            self.screenshots.append(screenshot)
            logger.info(
                f"Screenshot captured for step '{step_name}' at {path} "
                f"({screenshot.file_size} bytes)"
            )

            return screenshot

        except Exception as e:
            raise BrowserManagerError(f"Failed to capture screenshot: {e}")

    async def close(self) -> None:
        """Close the browser session."""
        if self.closed:
            return
        try:
            self.closed = True
            await self.context.close()
            logger.info(f"Closed browser session {self.session_id}")
        except Exception as e:
            logger.error(f"Error closing browser session {self.session_id}: {e}")

    async def is_alive(self) -> bool:
        """Check if the browser context is still alive."""
        if self.closed:
            return False
        try:
            # Try to get the page title as a health check
            await self.page.title()
            return True
        except Exception:
            self.closed = True
            return False

    def get_console_errors(self) -> list[str]:
        """Get all console error messages."""
        return [msg["text"] for msg in self.console_messages if msg["type"] == "error"]

    def get_console_warnings(self) -> list[str]:
        """Get all console warning messages."""
        return [msg["text"] for msg in self.console_messages if msg["type"] == "warning"]

    async def get_page_state(self) -> dict:
        """
        Get the current page state for Claude guidance.

        Captures comprehensive page state including URL, title, viewport,
        cookies, localStorage, and console logs.

        Returns:
            Dictionary containing page state information

        Raises:
            BrowserManagerError: If unable to capture page state
        """
        try:
            state = {
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport": self.page.viewport_size or {"width": 0, "height": 0},
                "console_errors": self.get_console_errors(),
                "console_warnings": self.get_console_warnings(),
            }

            # Capture cookies (safely)
            try:
                cookies = await self.context.cookies()
                state["cookies"] = [
                    {
                        "name": c.get("name"),
                        "domain": c.get("domain"),
                        "path": c.get("path"),
                    }
                    for c in cookies
                ]
            except Exception as e:
                logger.debug("Could not capture cookies: %s", e)
                state["cookies"] = []

            # Capture localStorage (safely)
            try:
                local_storage = await self.page.evaluate(
                    """() => {
                    const items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key) {
                            items[key] = localStorage.getItem(key);
                        }
                    }
                    return items;
                }"""
                )
                state["local_storage"] = local_storage
            except Exception as e:
                logger.debug("Could not capture localStorage: %s", e)
                state["local_storage"] = {}

            # Capture simplified DOM snapshot (just key elements)
            try:
                dom_summary = await self.page.evaluate(
                    """() => {
                    return {
                        forms: document.forms.length,
                        links: document.links.length,
                        images: document.images.length,
                        buttons: document.querySelectorAll('button').length,
                        inputs: document.querySelectorAll('input').length,
                    };
                }"""
                )
                state["dom_summary"] = dom_summary
            except Exception as e:
                logger.debug("Could not capture DOM summary: %s", e)
                state["dom_summary"] = {}

            return state

        except Exception as e:
            raise BrowserManagerError(f"Failed to capture page state: {e}")


class BrowserSessionManager:
    """
    Manages browser lifecycle and session pooling using Playwright.

    Provides async context managers for browser sessions with automatic cleanup.
    """

    def __init__(self):
        """Initialize the browser session manager."""
        self._playwright: Playwright | None = None
        self._browsers: dict[str, Browser] = {}  # browser_type -> Browser
        self._active_sessions: dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """
        Start the Playwright instance.

        Should be called before creating any browser sessions.
        """
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            logger.info("Playwright started")

    async def stop(self) -> None:
        """
        Stop the Playwright instance and close all browsers.

        Should be called when done with all browser operations.
        """
        # Close all active sessions
        for session in list(self._active_sessions.values()):
            await session.close()
        self._active_sessions.clear()

        # Close all browsers
        for browser_type, browser in self._browsers.items():
            try:
                await browser.close()
                logger.info("Closed %s browser", browser_type)
            except Exception as e:
                logger.error("Error closing %s browser: %s", browser_type, e)

        self._browsers.clear()

        # Stop Playwright
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright stopped")

    async def _get_browser(
        self, browser_type: str, headless: bool = True, slowmo: int = 0
    ) -> Browser:
        """
        Get or create a browser instance.

        Args:
            browser_type: Type of browser ("chromium", "firefox", "webkit")
            headless: Run browser in headless mode
            slowmo: Slow down actions by N milliseconds

        Returns:
            Browser instance

        Raises:
            BrowserManagerError: If browser type is invalid
        """
        async with self._lock:
            # Cache key includes headless mode to support both headed and headless browsers
            cache_key = f"{browser_type}_{headless}"
            if cache_key in self._browsers:
                return self._browsers[cache_key]

            if self._playwright is None:
                raise BrowserManagerError("Playwright not started. Call start() first.")

            # Prepare launch options
            launch_options: dict = {
                "headless": headless,
            }
            if slowmo > 0:
                launch_options["slow_mo"] = slowmo

            # Launch browser
            try:
                if browser_type == "chromium":
                    browser = await self._playwright.chromium.launch(**launch_options)
                elif browser_type == "firefox":
                    browser = await self._playwright.firefox.launch(**launch_options)
                elif browser_type == "webkit":
                    browser = await self._playwright.webkit.launch(**launch_options)
                else:
                    raise BrowserManagerError(
                        f"Invalid browser type: {browser_type}. "
                        f"Must be one of: chromium, firefox, webkit"
                    )

                self._browsers[cache_key] = browser
                logger.info(
                    "Launched %s browser (headless=%s, slowmo=%s)",
                    browser_type.upper(),
                    headless,
                    slowmo,
                )
                return browser

            except Exception as e:
                raise BrowserManagerError(f"Failed to launch {browser_type}: {e}")

    @asynccontextmanager
    async def create_session(
        self, config: BrowserConfig | None = None, profile_id: str | None = None
    ) -> AsyncIterator[BrowserSession]:
        """
        Create a new browser session with context and page.

        Args:
            config: Browser configuration. If None, uses default config.
            profile_id: Optional profile ID to include in session_id for tracking

        Yields:
            BrowserSession instance

        Example:
            async with manager.create_session(config) as session:
                await session.page.goto("https://example.com")
                await session.screenshot("example.png", "Navigate", 0)
        """
        if config is None:
            config = BrowserConfig()

        # Include profile_id in session_id if provided for easier lookup
        if profile_id:
            session_id = f"{profile_id}-{uuid4()!s}"
        else:
            session_id = str(uuid4())
        browser = await self._get_browser(config.browser_type, config.headless, config.slowmo)

        # Prepare context options
        context_options: dict = {
            "viewport": config.viewport.model_dump()
            if hasattr(config.viewport, "model_dump")
            else config.viewport,
            "locale": config.locale,
            "ignore_https_errors": config.ignore_https_errors,
            "accept_downloads": config.accept_downloads,
        }

        if config.timezone:
            context_options["timezone_id"] = config.timezone

        if config.user_agent:
            context_options["user_agent"] = config.user_agent

        if config.permissions:
            context_options["permissions"] = config.permissions

        if config.proxy:
            context_options["proxy"] = config.proxy

        # Device emulation
        if config.device:
            try:
                device = self._playwright.devices.get(config.device)
                if device:
                    context_options.update(device)
                else:
                    logger.warning(f"Device '{config.device}' not found, ignoring")
            except Exception as e:
                logger.warning("Failed to apply device emulation: %s", e)

        # Video recording
        if config.record_video:
            videos_dir = Path("test_results") / "videos" / session_id
            videos_dir.mkdir(parents=True, exist_ok=True)
            context_options["record_video_dir"] = str(videos_dir)

        # HAR recording
        if config.record_har:
            har_dir = Path("test_results") / "har" / session_id
            har_dir.mkdir(parents=True, exist_ok=True)
            context_options["record_har_path"] = str(har_dir / "network.har")

        try:
            # Create context
            context = await browser.new_context(**context_options)

            # Apply slow motion if configured
            if config.slowmo > 0:
                # Note: slowmo is applied at browser launch, not context
                # We'll use page.wait_for_timeout() in the test runner instead
                pass

            # Create page
            page = await context.new_page()

            # Create session
            session = BrowserSession(browser, context, page, session_id, config)
            self._active_sessions[session_id] = session

            # Set cleanup callback so session removes itself when browser window is closed
            session.set_cleanup_callback(self._handle_session_close)

            logger.info(
                f"Created browser session {session_id} "
                f"(type={config.browser_type}, headless={config.headless})"
            )

            try:
                yield session
            finally:
                # Cleanup
                await session.close()
                self._active_sessions.pop(session_id, None)

        except Exception as e:
            raise BrowserManagerError(f"Failed to create browser session: {e}")

    async def _handle_session_close(self, session_id: str):
        """Handle cleanup when a browser context is closed externally."""
        session = self._active_sessions.pop(session_id, None)
        if session:
            logger.info(f"Auto-cleaned up session {session_id} after browser window closed")

    async def get_active_sessions(self) -> list[BrowserSession]:
        """
        Get all active browser sessions.

        Returns:
            List of active BrowserSession instances
        """
        return list(self._active_sessions.values())

    async def cleanup_session(self, session_id: str) -> None:
        """
        Manually cleanup a specific session.

        Args:
            session_id: Session ID to cleanup
        """
        session = self._active_sessions.get(session_id)
        if session:
            await session.close()
            self._active_sessions.pop(session_id, None)
            logger.info("Cleaned up session %s", session_id)

    async def cleanup_all_sessions(self) -> None:
        """Close all active sessions."""
        for session in list(self._active_sessions.values()):
            await session.close()
        self._active_sessions.clear()
        logger.info("All browser sessions cleaned up")

    async def cleanup_dead_sessions(self) -> int:
        """
        Check all active sessions and cleanup any that are no longer alive.

        Returns:
            Number of dead sessions cleaned up
        """
        dead_sessions = []
        for session_id, session in list(self._active_sessions.items()):
            if not await session.is_alive():
                dead_sessions.append(session_id)

        for session_id in dead_sessions:
            self._active_sessions.pop(session_id, None)
            logger.info(f"Cleaned up dead session {session_id}")

        return len(dead_sessions)

    def get_session_info(self) -> list[dict]:
        """
        Get information about all active sessions.

        Returns:
            List of session info dictionaries
        """
        return [
            {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "browser_type": session.config.browser_type,
                "headless": session.config.headless,
                "closed": session.closed,
                "url": session.page.url if not session.closed else None,
            }
            for session in self._active_sessions.values()
        ]


# Global manager instance (optional, for convenience)
_global_manager: BrowserSessionManager | None = None


async def get_browser_manager() -> BrowserSessionManager:
    """
    Get or create the global browser manager instance.

    Returns:
        Global BrowserSessionManager instance
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = BrowserSessionManager()
        await _global_manager.start()
    return _global_manager


async def cleanup_browser_manager() -> None:
    """Cleanup the global browser manager instance."""
    global _global_manager
    if _global_manager is not None:
        await _global_manager.stop()
        _global_manager = None
