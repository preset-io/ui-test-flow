"""Test runner for orchestrating test execution with Playwright."""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from uitestflow.core.models import (
    ActionType,
    BrowserConfig,
    EvalResult,
    EvaluatorType,
    LogEntry,
    StepResult,
    TestDefinition,
    TestResult,
    TestRun,
    TestStatus,
    TestStep,
)

from .browser_manager import BrowserSession, BrowserSessionManager


logger = logging.getLogger(__name__)


class TestRunnerError(Exception):
    """Exception raised for test runner errors."""


class TestRunner:
    """
    Orchestrates test execution using Playwright.

    Executes test steps, captures screenshots, handles errors, and generates results.
    """

    def __init__(
        self,
        browser_manager: BrowserSessionManager | None = None,
        results_dir: str | Path = "test_results",
    ):
        """
        Initialize the test runner.

        Args:
            browser_manager: Browser session manager. If None, creates a new one.
            results_dir: Directory to store test results and artifacts
        """
        self.browser_manager = browser_manager or BrowserSessionManager()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run_test(
        self,
        test_definition: TestDefinition,
        profile: str | None = None,
        context: dict[str, Any] | None = None,
        run_id: UUID | None = None,
    ) -> TestRun:
        """
        Execute a test definition.

        Args:
            test_definition: Test definition to execute
            profile: Profile name (for context)
            context: Additional context information (e.g., PR number, commit SHA)
            run_id: Optional run ID. If not provided, a new UUID is generated.

        Returns:
            TestRun with complete results and artifacts

        Raises:
            TestRunnerError: If test execution fails critically
        """
        # Create test run - use provided run_id or generate new one
        run_id = run_id or uuid4()
        test_run = TestRun(
            id=run_id,
            test_definition=test_definition,
            profile=profile,
            context=context or {},
            status=TestStatus.PENDING,
        )

        # Create run directory for artifacts
        run_dir = self.results_dir / str(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir = run_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

        logger.info(f"Starting test run {run_id}: {test_definition.name}")

        try:
            # Update status to running
            test_run.status = TestStatus.RUNNING
            test_run.started_at = datetime.utcnow()

            # Ensure browser manager is started
            if self.browser_manager._playwright is None:
                await self.browser_manager.start()

            # Get browser config from test or use defaults
            browser_config = test_definition.browser_config or BrowserConfig()

            # Execute test in browser session
            async with self.browser_manager.create_session(browser_config) as session:
                step_results: list[StepResult] = []

                # Execute each step
                for idx, step in enumerate(test_definition.steps):
                    try:
                        step_result = await self._execute_step(
                            session, step, idx, screenshots_dir, test_definition.timeout
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
                            # Continue to evaluators with partial results
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

                # All screenshots from session
                test_run.screenshots = session.screenshots

                # Get console messages
                console_errors = session.get_console_errors()
                console_warnings = session.get_console_warnings()

                # Log console messages
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

                logger.info(
                    f"Test run {run_id} completed: "
                    f"{'PASSED' if test_passed else 'FAILED'} "
                    f"(score: {overall_score:.2f}, duration: {total_duration_ms}ms)"
                )

        except Exception as e:
            test_run.status = TestStatus.FAILED
            test_run.completed_at = datetime.utcnow()
            if test_run.started_at:
                test_run.duration_ms = int(
                    (test_run.completed_at - test_run.started_at).total_seconds() * 1000
                )

            logger.error("Test run %s failed critically: %s", run_id, e)
            raise TestRunnerError(f"Test execution failed: {e}")

        return test_run

    async def _execute_step(
        self,
        session: BrowserSession,
        step: TestStep,
        step_index: int,
        screenshots_dir: Path,
        default_timeout: int,
    ) -> StepResult:
        """
        Execute a single test step.

        Args:
            session: Browser session
            step: Test step to execute
            step_index: Index of the step
            screenshots_dir: Directory to save screenshots
            default_timeout: Default timeout in milliseconds

        Returns:
            StepResult with execution details
        """
        logger.info(f"Executing step {step_index}: {step.name} ({step.action})")

        start_time = time.time()
        success = False
        error_message = None
        screenshot_path = None

        timeout = step.timeout or default_timeout

        try:
            # Execute action based on type
            if step.action == ActionType.GOTO:
                # Use url field, or fall back to value field if url is not set
                target_url = step.url or step.value
                if not target_url:
                    raise TestRunnerError(f"Step '{step.name}': 'url' is required for goto action")
                await session.page.goto(target_url, timeout=timeout)

            elif step.action == ActionType.CLICK:
                if not step.selector:
                    raise TestRunnerError(
                        f"Step '{step.name}': 'selector' is required for click action"
                    )
                await session.page.click(step.selector, timeout=timeout)

            elif step.action == ActionType.FILL:
                # Safely check for selectors attribute (may not exist in all model types)
                selectors = getattr(step, "selectors", None)
                if selectors:
                    # Fill multiple inputs
                    for selector_data in selectors:
                        selector = selector_data.get("selector")
                        value = selector_data.get("value")
                        if selector and value is not None:
                            await session.page.fill(selector, value, timeout=timeout)
                elif step.selector and step.value is not None:
                    # Fill single input
                    await session.page.fill(step.selector, step.value, timeout=timeout)
                else:
                    raise TestRunnerError(
                        f"Step '{step.name}': 'selector' and 'value' or 'selectors' "
                        f"required for fill action"
                    )

            elif step.action == ActionType.WAIT_FOR:
                if not step.selector:
                    raise TestRunnerError(
                        f"Step '{step.name}': 'selector' is required for wait_for action"
                    )
                await session.page.wait_for_selector(step.selector, timeout=timeout)

            elif step.action == ActionType.WAIT:
                # Simple wait/sleep action
                wait_time = int(step.value) if step.value else (step.timeout or 1000)
                await asyncio.sleep(wait_time / 1000.0)

            elif step.action == ActionType.EXPECT:
                # Placeholder for expect actions (assertions)
                # This would implement various assertion types
                logger.warning(f"EXPECT action not fully implemented yet for step '{step.name}'")

            elif step.action == ActionType.ASSERT:
                # ASSERT implementation - verify element exists/visible
                if not step.selector:
                    raise TestRunnerError(
                        f"Step '{step.name}': 'selector' required for assert action"
                    )
                # Check if at least one visible element exists matching the selector
                # Filter to visible elements using Playwright's visible filter
                locator = session.page.locator(step.selector).filter(
                    has=session.page.locator("visible=true")
                )

                # Try using a simpler approach - just check if visible elements exist
                try:
                    # Count visible elements (excludes hidden elements)
                    visible_selector = f"{step.selector}:not([type='hidden']):visible"
                    visible_locator = session.page.locator(visible_selector)
                    count = await visible_locator.count()

                    if count == 0:
                        # Fallback: check if any elements exist at all
                        all_count = await session.page.locator(step.selector).count()
                        if all_count > 0:
                            raise TestRunnerError(
                                f"Assertion failed for '{step.name}': found {all_count} element(s) matching '{step.selector}' but none are visible"
                            )
                        else:
                            raise TestRunnerError(
                                f"Assertion failed for '{step.name}': no elements found matching '{step.selector}'"
                            )
                except Exception as e:
                    if "Assertion failed" in str(e):
                        raise
                    # If selector parsing fails, try simpler check
                    locator = session.page.locator(step.selector)
                    # Just wait for any matching element to be attached to DOM
                    await locator.first.wait_for(state="attached", timeout=timeout)
                    # Then verify at least one is visible
                    is_visible = await locator.first.is_visible()
                    if not is_visible:
                        raise TestRunnerError(
                            f"Assertion failed for '{step.name}': element '{step.selector}' exists but is not visible"
                        )

            elif step.action == ActionType.SCREENSHOT:
                # Explicit screenshot step
                screenshot_path = str(
                    screenshots_dir / f"step_{step_index}_{step.name.replace(' ', '_')}.png"
                )
                await session.screenshot(screenshot_path, step.name, step_index)

            elif step.action == ActionType.EXECUTE:
                # Execute custom JavaScript
                if step.value:
                    await session.page.evaluate(step.value)
                else:
                    raise TestRunnerError(
                        f"Step '{step.name}': 'value' (JavaScript code) required for execute action"
                    )

            else:
                # Custom or unknown action
                logger.warning(
                    f"Unknown action type '{step.action}' for step '{step.name}', skipping"
                )

            # Apply slow motion if configured
            if session.config.slowmo > 0:
                await asyncio.sleep(session.config.slowmo / 1000.0)

            success = True

        except PlaywrightTimeoutError as e:
            error_message = f"Timeout: {e!s}"
            logger.error(f"Step {step_index} '{step.name}' timed out: {error_message}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Step {step_index} '{step.name}' failed: {error_message}")

        # Always capture screenshot after each step for better debugging
        # This ensures we have visual proof of each step's result
        try:
            screenshot_path = str(
                screenshots_dir / f"step_{step_index}_{step.name.replace(' ', '_')}.png"
            )
            await session.screenshot(screenshot_path, step.name, step_index)
            logger.debug(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning("Failed to capture screenshot for step %s: %s", step_index, e)
            screenshot_path = None

        duration_ms = int((time.time() - start_time) * 1000)

        return StepResult(
            step_name=step.name,
            step_index=step_index,
            action=str(step.action),
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            screenshot_path=screenshot_path,
        )

    async def _run_evaluators(
        self,
        evaluators: list,
        session: BrowserSession,
        step_results: list[StepResult],
        console_errors: list[str],
        console_warnings: list[str],
        screenshots_dir: Path,
    ) -> list[EvalResult]:
        """
        Run all evaluators on test results.

        Args:
            evaluators: List of evaluator configurations
            session: Browser session
            step_results: Results of executed steps
            console_errors: List of console errors
            console_warnings: List of console warnings
            screenshots_dir: Directory for screenshots

        Returns:
            List of evaluator results
        """
        evaluator_results = []

        for evaluator in evaluators:
            logger.info(f"Running evaluator: {evaluator.name} ({evaluator.type})")

            try:
                result = await self._evaluate(
                    evaluator, session, step_results, console_errors, console_warnings
                )
                evaluator_results.append(result)

            except Exception as e:
                logger.error(f"Evaluator '{evaluator.name}' failed: {e}")
                evaluator_results.append(
                    EvalResult(
                        passed=False,
                        score=0.0,
                        evaluator_name=evaluator.name,
                        evaluator_type=str(evaluator.type),
                        reason=f"Evaluator error: {e}",
                    )
                )

        return evaluator_results

    async def _evaluate(
        self,
        evaluator,
        session: BrowserSession,
        step_results: list[StepResult],
        console_errors: list[str],
        console_warnings: list[str],
    ) -> EvalResult:
        """
        Execute a single evaluator.

        Args:
            evaluator: Evaluator configuration
            session: Browser session
            step_results: Results of executed steps
            console_errors: List of console errors
            console_warnings: List of console warnings

        Returns:
            EvalResult
        """
        evaluator_type = evaluator.type

        # All steps completed
        if evaluator_type in (
            EvaluatorType.ALL_STEPS_COMPLETED,
            EvaluatorType.NO_EXCEPTIONS,
            "all_steps_completed",
            "execution_successful",
            "steps_completed",
            "no_exceptions",
        ):
            all_passed = all(result.success for result in step_results)
            return EvalResult(
                passed=all_passed,
                score=1.0 if all_passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason="All steps completed successfully" if all_passed else "Some steps failed",
            )

        # Console errors (NO_CONSOLE_ERRORS = no errors allowed)
        if evaluator_type in (
            EvaluatorType.NO_CONSOLE_ERRORS,
            "no_console_errors",
            "console_errors",
        ):
            max_errors = (
                evaluator.params.get("max_errors", 0)
                if hasattr(evaluator, "params")
                else (evaluator.max_errors or 0)
            )
            error_count = len(console_errors)
            passed = error_count <= max_errors

            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"Found {error_count} console errors (max: {max_errors})",
                details={"error_count": error_count, "errors": console_errors},
            )

        # Console warnings (NO_CONSOLE_WARNINGS = no warnings allowed)
        if evaluator_type in (
            EvaluatorType.NO_CONSOLE_WARNINGS,
            "no_console_warnings",
            "console_warnings",
        ):
            max_warnings = (
                evaluator.params.get("max_warnings", 0)
                if hasattr(evaluator, "params")
                else (evaluator.max_warnings or 0)
            )
            warning_count = len(console_warnings)
            passed = warning_count <= max_warnings

            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"Found {warning_count} console warnings (max: {max_warnings})",
                details={"warning_count": warning_count, "warnings": console_warnings},
            )

        # URL matches
        if evaluator_type in (EvaluatorType.URL_MATCHES, "url_matches"):
            current_url = session.page.url
            pattern = (
                evaluator.params.get("pattern")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "pattern", None)
            )
            expected_value = (
                evaluator.params.get("expected_value")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "expected_value", None)
            )
            expected = pattern or expected_value
            passed = expected in current_url if expected else True

            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"URL {'matches' if passed else 'does not match'} expected pattern",
                details={"current_url": current_url, "expected": expected},
            )

        # Title matches
        if evaluator_type in (EvaluatorType.TITLE_MATCHES, "title_matches"):
            current_title = await session.page.title()
            expected = (
                evaluator.params.get("expected_value")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "expected_value", None)
            )
            passed = expected in current_title if expected else True

            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"Title {'matches' if passed else 'does not match'} expected value",
                details={"current_title": current_title, "expected": expected},
            )

        # Element visible
        if evaluator_type in (EvaluatorType.ELEMENT_VISIBLE, "element_visible"):
            # Get selector from params or direct attribute
            selector = (
                evaluator.params.get("selector")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "selector", None)
            )
            if not selector:
                raise TestRunnerError("selector required for element_visible evaluator")

            try:
                element = await session.page.query_selector(selector)
                visible = element is not None and await element.is_visible()
            except Exception:
                visible = False

            return EvalResult(
                passed=visible,
                score=1.0 if visible else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"Element {'is' if visible else 'is not'} visible",
                details={"selector": selector},
            )

        # Performance / page load time
        if evaluator_type in (
            EvaluatorType.PERFORMANCE,
            EvaluatorType.PAGE_LOAD_TIME,
            "performance",
            "page_load_time",
        ):
            max_load_time = (
                evaluator.params.get("max_load_time")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "max_load_time", None)
            )
            max_time_attr = (
                evaluator.params.get("max_time")
                if hasattr(evaluator, "params")
                else getattr(evaluator, "max_time", None)
            )
            max_time = max_load_time or max_time_attr or 5000
            total_duration = sum(result.duration_ms for result in step_results)
            passed = total_duration <= max_time

            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_name=evaluator.name,
                evaluator_type=str(evaluator_type),
                reason=f"Total duration {total_duration}ms ({'within' if passed else 'exceeds'} {max_time}ms)",
                details={"total_duration_ms": total_duration, "max_ms": max_time},
            )

        # Default: Unknown evaluator
        logger.warning("Unknown evaluator type: %s", evaluator_type)
        return EvalResult(
            passed=True,
            score=1.0,
            evaluator_name=evaluator.name,
            evaluator_type=str(evaluator_type),
            reason="Unknown evaluator type, skipped",
        )
