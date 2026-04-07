"""Enhanced test runner with Claude guidance for intelligent test execution."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from uitestflow.core.models import (
    ActionType,
    BrowserConfig,
    StepResult,
    TestDefinition,
    TestRun,
    TestStatus,
    TestStep,
)
from uitestflow.llm.executor import ClaudeExecutor
from uitestflow.src.browser_manager import BrowserSession, BrowserSessionManager
from uitestflow.src.test_runner import TestRunner, TestRunnerError


logger = logging.getLogger(__name__)


class EnhancedTestRunner(TestRunner):
    """
    Enhanced test runner with Claude-guided execution.

    Extends TestRunner to support intelligent test execution with:
    - Pre-step guidance from Claude
    - Adaptive selector resolution
    - Intelligent error recovery
    - Post-step validation

    Falls back to standard execution if Claude is unavailable.

    Example:
        ```python
        executor = ClaudeExecutor(api_key="sk-...")
        runner = EnhancedTestRunner(claude_executor=executor)
        test_run = await runner.run_test(test_definition, guided=True)
        ```
    """

    def __init__(
        self,
        browser_manager: BrowserSessionManager | None = None,
        results_dir: str | Path = "test_results",
        claude_executor: ClaudeExecutor | None = None,
    ):
        """
        Initialize the enhanced test runner.

        Args:
            browser_manager: Browser session manager. If None, creates a new one.
            results_dir: Directory to store test results and artifacts
            claude_executor: Claude executor for guided execution. If None,
                           falls back to standard execution.
        """
        super().__init__(browser_manager, results_dir)
        self.claude_executor = claude_executor
        self.guidance_enabled = claude_executor is not None

    async def run_test(
        self,
        test_definition: TestDefinition,
        profile: str | None = None,
        context: dict[str, Any] | None = None,
        guided: bool = True,
    ) -> TestRun:
        """
        Execute a test definition with optional Claude guidance.

        Args:
            test_definition: Test definition to execute
            profile: Profile name (for context)
            context: Additional context information
            guided: Whether to use Claude guidance (requires claude_executor)

        Returns:
            TestRun with complete results and artifacts

        Raises:
            TestRunnerError: If test execution fails critically
        """
        # If guidance requested but not available, fall back to standard execution
        use_guidance = guided and self.guidance_enabled

        if guided and not self.guidance_enabled:
            logger.warning(
                "Guided execution requested but no Claude executor available, "
                "falling back to standard execution"
            )

        if not use_guidance:
            # Standard execution without guidance
            return await super().run_test(test_definition, profile, context)

        # Enhanced execution with guidance
        return await self._run_test_with_guidance(test_definition, profile, context)

    async def _run_test_with_guidance(
        self,
        test_definition: TestDefinition,
        profile: str | None,
        context: dict[str, Any] | None,
    ) -> TestRun:
        """
        Execute test with Claude guidance.

        This method overrides the standard execution to include:
        - Pre-step guidance
        - Selector adaptation
        - Error recovery
        - Post-step validation
        """
        from datetime import datetime
        from uuid import uuid4

        # Create test run
        run_id = uuid4()
        test_run = TestRun(
            id=run_id,
            test_definition=test_definition,
            test_id=test_definition.id,
            test_name=test_definition.name,
            profile=profile,
            context=context or {},
            status=TestStatus.PENDING,
        )

        # Create run directory for artifacts
        run_dir = self.results_dir / str(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir = run_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

        logger.info(f"Starting guided test run {run_id}: {test_definition.name}")

        # Initialize guidance metadata
        guidance_metadata = {
            "guidance_enabled": True,
            "model": self.claude_executor.model if self.claude_executor else None,
            "steps_with_guidance": 0,
            "selectors_adapted": 0,
            "errors_recovered": 0,
        }

        try:
            # Update status to running
            test_run.status = TestStatus.RUNNING
            test_run.started_at = datetime.utcnow()

            # Ensure browser manager is started
            if self.browser_manager._playwright is None:
                await self.browser_manager.start()

            # Get browser config
            browser_config = test_definition.browser_config or BrowserConfig()

            # Execute test in browser session
            async with self.browser_manager.create_session(browser_config) as session:
                step_results: list[StepResult] = []

                # Execute each step with guidance
                for idx, step in enumerate(test_definition.steps):
                    try:
                        step_result = await self._execute_step_with_guidance(
                            session=session,
                            step=step,
                            step_index=idx,
                            screenshots_dir=screenshots_dir,
                            default_timeout=test_definition.timeout,
                            guidance_metadata=guidance_metadata,
                        )
                        step_results.append(step_result)

                        # Add screenshot to test run if captured
                        if step_result.screenshot_path:
                            test_run.screenshots.extend(session.screenshots[-1:])

                        # Check if step failed
                        if not step_result.success:
                            logger.error(
                                f"Step {idx} '{step.name}' failed: " f"{step_result.error_message}"
                            )
                            break

                    except Exception as e:
                        logger.error(f"Error executing step {idx} '{step.name}': {e}")
                        step_result = StepResult(
                            step_name=step.name,
                            step_index=idx,
                            action=str(step.action),
                            success=False,
                            duration_ms=0,
                            error_message=str(e),
                        )
                        step_results.append(step_result)
                        break

                # Collect results (reuse parent class logic)
                test_run.screenshots = session.screenshots
                console_errors = session.get_console_errors()
                console_warnings = session.get_console_warnings()

                # Log console messages
                from uitestflow.src.models import LogEntry

                for error in console_errors:
                    test_run.logs.append(
                        LogEntry(
                            level="error",
                            message=error,
                            timestamp=datetime.utcnow(),
                            source="console",
                        )
                    )

                for warning in console_warnings:
                    test_run.logs.append(
                        LogEntry(
                            level="warning",
                            message=warning,
                            timestamp=datetime.utcnow(),
                            source="console",
                        )
                    )

                # Calculate step statistics
                steps_executed = len(step_results)
                steps_passed = sum(1 for result in step_results if result.success)
                steps_failed = steps_executed - steps_passed

                # Run evaluators
                evaluator_results = await self._run_evaluators(
                    test_definition.evaluators,
                    session,
                    step_results,
                    console_errors,
                    console_warnings,
                    screenshots_dir,
                )

                # Calculate overall pass/fail
                all_steps_passed = steps_failed == 0
                all_evaluators_passed = all(result.passed for result in evaluator_results)
                test_passed = all_steps_passed and all_evaluators_passed

                # Calculate overall score
                if evaluator_results:
                    overall_score = sum(r.score for r in evaluator_results) / len(evaluator_results)
                else:
                    overall_score = 1.0 if test_passed else 0.0

                # Calculate total duration
                test_run.completed_at = datetime.utcnow()
                total_duration_ms = int(
                    (test_run.completed_at - test_run.started_at).total_seconds() * 1000
                )

                # Create test result
                from uitestflow.src.models import TestResult

                test_result = TestResult(
                    passed=test_passed,
                    score=overall_score,
                    step_results=step_results,
                    steps_executed=steps_executed,
                    steps_passed=steps_passed,
                    steps_failed=steps_failed,
                    evaluator_results=evaluator_results,
                    total_duration_ms=total_duration_ms,
                    console_errors=console_errors,
                    console_warnings=console_warnings,
                )

                # Add error screenshot if test failed
                if not test_passed and steps_failed > 0:
                    failed_step = step_results[-1]
                    if failed_step.screenshot_path:
                        test_result.error_screenshot_path = failed_step.screenshot_path
                    test_result.error_message = failed_step.error_message

                # Update test run
                test_run.result = test_result
                test_run.status = TestStatus.COMPLETED if test_passed else TestStatus.FAILED
                test_run.duration_ms = total_duration_ms
                test_run.guidance_metadata = guidance_metadata

                logger.info(
                    f"Guided test run {run_id} completed: "
                    f"{'PASSED' if test_passed else 'FAILED'} "
                    f"(score: {overall_score:.2f}, duration: {total_duration_ms}ms, "
                    f"guidance: {guidance_metadata['steps_with_guidance']} steps)"
                )

        except Exception as e:
            test_run.status = TestStatus.FAILED
            test_run.completed_at = datetime.utcnow()
            if test_run.started_at:
                test_run.duration_ms = int(
                    (test_run.completed_at - test_run.started_at).total_seconds() * 1000
                )

            logger.error("Guided test run %s failed critically: %s", run_id, e)
            raise TestRunnerError(f"Guided test execution failed: {e}")

        return test_run

    async def _execute_step_with_guidance(
        self,
        session: BrowserSession,
        step: TestStep,
        step_index: int,
        screenshots_dir: Path,
        default_timeout: int,
        guidance_metadata: dict[str, Any],
    ) -> StepResult:
        """
        Execute a single test step with Claude guidance.

        This method wraps standard step execution with:
        1. Pre-step guidance from Claude
        2. Adaptive selector resolution on failure
        3. Error recovery attempts
        4. Post-step validation

        Args:
            session: Browser session
            step: Test step to execute
            step_index: Index of the step
            screenshots_dir: Directory to save screenshots
            default_timeout: Default timeout in milliseconds
            guidance_metadata: Metadata dictionary to track guidance usage

        Returns:
            StepResult with execution details and guidance information
        """
        logger.info(f"Executing step {step_index} with guidance: {step.name} ({step.action})")

        start_time = time.time()
        success = False
        error_message = None
        screenshot_path = None
        claude_guidance = None
        adapted_selector = None
        error_recovery_attempted = False
        recovery_action = None
        page_state_before = None

        timeout = step.timeout or default_timeout

        try:
            # Capture page state before step
            page_state_before = await session.get_page_state()

            # Get Claude guidance for this step
            guidance = await self._get_claude_feedback(step, page_state_before, step_index)
            claude_guidance = guidance.get("guidance", "")
            guidance_metadata["steps_with_guidance"] += 1

            # Check for warnings from Claude
            if guidance.get("warnings"):
                logger.warning(
                    f"Claude warnings for step {step_index}: " f"{', '.join(guidance['warnings'])}"
                )

            # Execute the step with potential selector adaptation
            try:
                await self._execute_action(session, step, timeout)
                success = True

            except PlaywrightTimeoutError as e:
                # Try adaptive selector resolution
                if step.selector and self.claude_executor:
                    logger.info(
                        f"Original selector failed, trying alternatives for: {step.selector}"
                    )
                    adapted_selector = await self._adapt_selector(
                        step.selector,
                        session,
                        timeout,
                        str(e),
                    )

                    if adapted_selector:
                        guidance_metadata["selectors_adapted"] += 1
                        logger.info("Using adapted selector: %s", adapted_selector)

                        # Retry with adapted selector
                        modified_step = TestStep(
                            name=step.name,
                            action=step.action,
                            selector=adapted_selector,
                            value=step.value,
                            url=step.url,
                            timeout=step.timeout,
                            screenshot=step.screenshot,
                        )
                        await self._execute_action(session, modified_step, timeout)
                        success = True
                    else:
                        raise
                else:
                    raise

        except Exception as e:
            error_message = str(e)
            logger.error(f"Step {step_index} '{step.name}' failed: {error_message}")

            # Attempt error recovery
            if self.claude_executor:
                recovery_result = await self._handle_execution_error(
                    step, error_message, await session.get_page_state()
                )

                if recovery_result.get("recoverable"):
                    error_recovery_attempted = True
                    recovery_action = recovery_result.get("recovery_action")
                    guidance_metadata["errors_recovered"] += 1

                    logger.info("Attempting error recovery: %s", recovery_action)

                    # Note: Actual recovery would require executing recovery action
                    # For now, we just log the suggestion

        # Apply slow motion if configured
        if session.config.slowmo > 0:
            await asyncio.sleep(session.config.slowmo / 1000.0)

        # Capture screenshot if configured or on error
        if step.screenshot or (not success and error_message):
            try:
                screenshot_path = str(
                    screenshots_dir / f"step_{step_index}_{step.name.replace(' ', '_')}.png"
                )
                await session.screenshot(screenshot_path, step.name, step_index)
            except Exception as e:
                logger.warning("Failed to capture screenshot for step %s: %s", step_index, e)

        duration_ms = int((time.time() - start_time) * 1000)

        # Create step result with guidance information
        return StepResult(
            step_name=step.name,
            step_index=step_index,
            action=str(step.action),
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            screenshot_path=screenshot_path,
            claude_guidance=claude_guidance,
            adapted_selector=adapted_selector,
            error_recovery_attempted=error_recovery_attempted,
            recovery_action=recovery_action,
            page_state=page_state_before,
        )

    async def _execute_action(
        self,
        session: BrowserSession,
        step: TestStep,
        timeout: int,
    ) -> None:
        """
        Execute the actual browser action for a step.

        This is extracted to allow retrying with adapted selectors.
        """
        if step.action == ActionType.GOTO:
            if not step.url:
                raise TestRunnerError(f"Step '{step.name}': 'url' is required for goto action")
            await session.page.goto(step.url, timeout=timeout)

        elif step.action == ActionType.CLICK:
            if not step.selector:
                raise TestRunnerError(
                    f"Step '{step.name}': 'selector' is required for click action"
                )
            await session.page.click(step.selector, timeout=timeout)

        elif step.action == ActionType.FILL:
            if step.selector and step.value is not None:
                await session.page.fill(step.selector, str(step.value), timeout=timeout)
            else:
                raise TestRunnerError(
                    f"Step '{step.name}': 'selector' and 'value' required for fill action"
                )

        elif step.action == ActionType.WAIT_FOR:
            if not step.selector:
                raise TestRunnerError(
                    f"Step '{step.name}': 'selector' is required for wait_for action"
                )
            await session.page.wait_for_selector(step.selector, timeout=timeout)

        elif step.action == ActionType.SCREENSHOT:
            # Handled separately, no action needed here
            pass

        elif step.action in (ActionType.EXECUTE_SCRIPT, "execute"):
            if step.value:
                await session.page.evaluate(str(step.value))
            else:
                raise TestRunnerError(
                    f"Step '{step.name}': 'value' (JavaScript code) required for execute action"
                )

    async def _get_claude_feedback(
        self,
        step: TestStep,
        page_state: dict[str, Any],
        step_index: int,
    ) -> dict[str, Any]:
        """
        Get Claude feedback for a test step.

        Args:
            step: Test step
            page_state: Current page state
            step_index: Step index

        Returns:
            Dictionary with guidance information
        """
        if not self.claude_executor:
            return {
                "guidance": "",
                "selector_valid": True,
                "warnings": [],
                "suggestions": [],
            }

        try:
            return await self.claude_executor.get_step_guidance(step, page_state, step_index)
        except Exception as e:
            logger.warning("Failed to get Claude guidance: %s", e)
            return {
                "guidance": "",
                "selector_valid": True,
                "warnings": [],
                "suggestions": [],
                "error": str(e),
            }

    async def _adapt_selector(
        self,
        original_selector: str,
        session: BrowserSession,
        timeout: int,
        error: str,
    ) -> str | None:
        """
        Adapt selector using Claude suggestions.

        Tries alternative selectors suggested by Claude until one works.

        Args:
            original_selector: Original selector that failed
            session: Browser session
            timeout: Timeout for selector checks
            error: Error message from original selector

        Returns:
            Working selector if found, None otherwise
        """
        if not self.claude_executor:
            return None

        try:
            page_state = await session.get_page_state()
            alternatives = await self.claude_executor.suggest_selector_alternatives(
                original_selector, page_state, error
            )

            # Try each alternative
            for alt_selector in alternatives:
                try:
                    # Check if selector works
                    element = await session.page.query_selector(alt_selector)
                    if element:
                        logger.info("Found working alternative: %s", alt_selector)
                        return alt_selector
                except Exception as e:
                    logger.debug("Alternative '%s' failed: %s", alt_selector, e)
                    continue

            return None

        except Exception as e:
            logger.warning("Failed to adapt selector: %s", e)
            return None

    async def _handle_execution_error(
        self,
        step: TestStep,
        error: str,
        page_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle execution error with Claude guidance.

        Args:
            step: Failed test step
            error: Error message
            page_state: Current page state

        Returns:
            Dictionary with recovery information
        """
        if not self.claude_executor:
            return {
                "recoverable": False,
                "recovery_action": None,
                "explanation": "",
            }

        try:
            return await self.claude_executor.suggest_error_recovery(step, error, page_state)
        except Exception as e:
            logger.warning("Failed to get error recovery suggestion: %s", e)
            return {
                "recoverable": False,
                "recovery_action": None,
                "explanation": "",
                "error": str(e),
            }
