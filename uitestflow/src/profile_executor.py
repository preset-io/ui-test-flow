"""Profile executor for running profile initialization steps."""

import asyncio
import logging
import os
import re
from pathlib import Path

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from uitestflow.core.models import (
    ActionType,
    BrowserConfig,
    InitStep,
    Profile,
    ProfileExecutionMode,
)

from .browser_manager import BrowserSession, BrowserSessionManager


logger = logging.getLogger(__name__)


class ProfileExecutorError(Exception):
    """Exception raised for profile executor errors."""


class ProfileExecutionResult:
    """Result of profile execution."""

    def __init__(self):
        """Initialize execution result."""
        self.success = True
        self.steps_executed = 0
        self.errors: list[str] = []
        self.screenshots: list[Path] = []
        self.message = ""
        self.session: BrowserSession | None = None


class ProfileExecutor:
    """
    Executes profile initialization steps.

    Handles:
    - Environment variable substitution
    - Critical vs non-critical step handling
    - Screenshot capture
    - Manual/automated/hybrid execution modes
    """

    def __init__(
        self,
        browser_manager: BrowserSessionManager | None = None,
        results_dir: str | Path = "profile_results",
    ):
        """
        Initialize profile executor.

        Args:
            browser_manager: Browser session manager
            results_dir: Directory to store screenshots and artifacts
        """
        self.browser_manager = browser_manager or BrowserSessionManager()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def substitute_env_vars(self, value: str) -> str:
        """
        Substitute environment variables in string values.

        Args:
            value: String potentially containing ${VAR_NAME} patterns

        Returns:
            String with environment variables substituted

        Example:
            Input: "user-${USERNAME}"
            Output: "user-john" (if USERNAME=john)
        """
        if not isinstance(value, str):
            return value

        # Find all ${VAR_NAME} patterns
        pattern = r"\$\{([^}]+)\}"

        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                logger.warning(f"Environment variable {var_name} not found, leaving as-is")
                return match.group(0)
            return env_value

        return re.sub(pattern, replace_var, value)

    async def execute_init_step(
        self,
        step: InitStep,
        page: Page,
        screenshots_dir: Path,
        step_index: int,
    ) -> tuple[bool, str | None]:
        """
        Execute a single initialization step.

        Args:
            step: Initialization step to execute
            page: Playwright page object
            screenshots_dir: Directory to save screenshots
            step_index: Index of this step (for screenshot naming)

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Executing init step {step_index + 1}: {step.name} ({step.action})")

        try:
            # Substitute environment variables in values
            if step.value and isinstance(step.value, str):
                step.value = self.substitute_env_vars(step.value)
            if step.url:
                step.url = self.substitute_env_vars(step.url)
            if step.selector:
                step.selector = self.substitute_env_vars(step.selector)

            # Execute action based on type
            if step.action == ActionType.GOTO or step.action == "goto":
                # Use url field, or fall back to value field if url is not set
                target_url = step.url or step.value
                if not target_url:
                    return False, f"Step '{step.name}': goto action requires url"
                await page.goto(target_url, timeout=step.timeout or 30000)

            elif step.action == ActionType.CLICK or step.action == "click":
                if not step.selector:
                    return False, f"Step '{step.name}': click action requires selector"
                await page.click(step.selector, timeout=step.timeout or 30000)

            elif step.action == ActionType.FILL or step.action == "fill":
                if not step.selector:
                    return False, f"Step '{step.name}': fill action requires selector"
                if step.value is None:
                    return False, f"Step '{step.name}': fill action requires value"
                await page.fill(step.selector, str(step.value), timeout=step.timeout or 30000)

            elif step.action == ActionType.WAIT_FOR or step.action == "wait_for":
                if not step.selector:
                    return False, f"Step '{step.name}': wait_for action requires selector"
                await page.wait_for_selector(step.selector, timeout=step.timeout or 30000)

            elif step.action == ActionType.WAIT or step.action == "wait":
                wait_time = step.timeout or 1000
                await asyncio.sleep(wait_time / 1000.0)

            else:
                return False, f"Step '{step.name}': unknown action type '{step.action}'"

            # Wait after step if specified
            if step.wait_after and step.wait_after > 0:
                await asyncio.sleep(step.wait_after / 1000.0)

            # Capture screenshot if requested
            if step.screenshot:
                screenshot_path = (
                    screenshots_dir / f"step_{step_index}_{step.name.replace(' ', '_')}.png"
                )
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved: {screenshot_path}")

            return True, None

        except PlaywrightTimeoutError as e:
            error_msg = f"Step '{step.name}' timed out: {e}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Step '{step.name}' failed: {e}"
            logger.error(error_msg)
            return False, error_msg

    async def execute_profile(
        self,
        profile: Profile,
        execution_mode: ProfileExecutionMode | None = None,
        headless: bool | None = None,
        with_claude: bool = True,
    ) -> ProfileExecutionResult:
        """
        Execute a profile's initialization steps.

        Args:
            profile: Profile to execute
            execution_mode: Override profile's execution mode
            headless: Override browser headless setting
            with_claude: Enable Claude AI guidance

        Returns:
            ProfileExecutionResult with execution details
        """
        result = ProfileExecutionResult()

        try:
            # Use override or profile defaults
            exec_mode = execution_mode or profile.execution_mode or ProfileExecutionMode.AUTOMATED

            # Create a copy of browser config to avoid mutating the original
            if profile.browser_config:
                browser_config = BrowserConfig(**profile.browser_config.model_dump())
            else:
                browser_config = BrowserConfig()

            # Override headless if specified
            if headless is not None:
                browser_config.headless = headless

            # For manual mode, force headed mode and add slowmo
            if exec_mode == ProfileExecutionMode.MANUAL:
                browser_config.headless = False
                if not browser_config.slowmo:
                    browser_config.slowmo = 500  # Add delay for visibility

            # Create screenshots directory
            screenshots_dir = self.results_dir / profile.id / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            # Start browser manager if not already started
            await self.browser_manager.start()

            # Start browser session using context manager
            logger.info(f"Starting browser session for profile: {profile.name}")

            # For manual/hybrid mode, we want to keep the browser open
            # Create session but don't auto-close it
            # Pass profile_id so session can be looked up by profile
            session_ctx = self.browser_manager.create_session(browser_config, profile_id=profile.id)
            session = await session_ctx.__aenter__()

            try:
                result.session = session

                # Get the page
                page = session.page

                # Execute initialization steps
                init_steps = profile.init_steps or []
                for index, step in enumerate(init_steps):
                    success, error = await self.execute_init_step(
                        step, page, screenshots_dir, index
                    )

                    result.steps_executed += 1

                    if not success:
                        if step.critical:
                            # Critical step failed - abort
                            result.success = False
                            result.errors.append(error or f"Critical step '{step.name}' failed")
                            result.message = (
                                f"Profile initialization failed at critical step: {step.name}"
                            )
                            logger.error(result.message)
                            break
                        else:
                            # Non-critical step failed - log warning and continue
                            warning = error or f"Step '{step.name}' failed (non-critical)"
                            result.errors.append(warning)
                            logger.warning(warning)

                # If successful
                if result.success:
                    if (
                        exec_mode == ProfileExecutionMode.MANUAL
                        or exec_mode == ProfileExecutionMode.HYBRID
                    ):
                        result.message = (
                            f"Profile '{profile.name}' initialized successfully. "
                            f"Browser is ready for manual testing. "
                            f"Executed {result.steps_executed} steps. "
                            f"Browser will remain open - close manually when done."
                        )
                        # Keep browser open for manual/hybrid mode - don't close the context
                        logger.info(result.message)
                        logger.info(
                            f"Session {session.session_id} will remain open for manual testing"
                        )
                    else:
                        result.message = (
                            f"Profile '{profile.name}' initialized successfully. "
                            f"Executed {result.steps_executed} steps. "
                            f"Session ready for automated testing."
                        )
                        logger.info(result.message)
                        # Close session for automated mode
                        await session_ctx.__aexit__(None, None, None)

            except Exception as step_error:
                # If error during steps, always close
                await session_ctx.__aexit__(type(step_error), step_error, step_error.__traceback__)
                raise

        except Exception as e:
            result.success = False
            result.errors.append(f"Profile execution failed: {e}")
            result.message = f"Failed to initialize profile: {e}"
            logger.error(result.message, exc_info=True)

        return result

    async def close_session(self, profile_id: str):
        """
        Close browser session for a profile.

        Args:
            profile_id: Profile ID whose session to close
        """
        try:
            await self.browser_manager.close_session(profile_id)
            logger.info(f"Closed browser session for profile: {profile_id}")
        except Exception as e:
            logger.error(f"Error closing session for profile {profile_id}: {e}")

    async def close_all_sessions(self):
        """Close all browser sessions."""
        try:
            await self.browser_manager.close_all()
            logger.info("Closed all browser sessions")
        except Exception as e:
            logger.error(f"Error closing all sessions: {e}")
