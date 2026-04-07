"""
Example: Guided Test Execution with Claude

This example demonstrates the Enhanced Test Runner with Claude-powered guidance
for intelligent test execution including:
- Pre-step guidance
- Adaptive selector resolution
- Error recovery
- Post-step validation

Usage:
    # Set your API key
    export ANTHROPIC_API_KEY="sk-ant-..."

    # Run the example
    python examples/guided_test_execution.py

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - Internet connection for Claude API
"""

import asyncio
import logging
import os
from pathlib import Path

from uitestflow.core.models import (
    ActionType,
    BrowserConfig,
    EvaluatorConfig,
    EvaluatorType,
    TestDefinition,
    TestStep,
)
from uitestflow.llm.executor import ClaudeExecutor
from uitestflow.src.browser_manager import BrowserSessionManager
from uitestflow.src.enhanced_test_runner import EnhancedTestRunner


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_login_test() -> TestDefinition:
    """Create a login test definition."""
    return TestDefinition(
        name="guided_login_test",
        description="Login test with Claude guidance",
        url="https://the-internet.herokuapp.com/login",
        steps=[
            TestStep(
                name="Navigate to login page",
                action=ActionType.GOTO,
                url="https://the-internet.herokuapp.com/login",
                screenshot=True,
            ),
            TestStep(
                name="Fill username",
                action=ActionType.FILL,
                selector="#username",
                value="tomsmith",
            ),
            TestStep(
                name="Fill password",
                action=ActionType.FILL,
                selector="#password",
                value="SuperSecretPassword!",
            ),
            TestStep(
                name="Click login button",
                action=ActionType.CLICK,
                selector="button[type='submit']",
            ),
            TestStep(
                name="Wait for success message",
                action=ActionType.WAIT_FOR,
                selector=".flash.success",
                timeout=5000,
                screenshot=True,
            ),
        ],
        evaluators=[
            EvaluatorConfig(
                name="All steps completed",
                evaluator_type=EvaluatorType.ALL_STEPS_COMPLETED,
            ),
            EvaluatorConfig(
                name="Success message visible",
                evaluator_type=EvaluatorType.ELEMENT_VISIBLE,
                params={"selector": ".flash.success"},
            ),
        ],
        browser_config=BrowserConfig(
            headless=False,  # Show browser for demo
            slow_mo=500,  # Slow down for visibility
        ),
    )


def create_selector_adaptation_test() -> TestDefinition:
    """Create a test that demonstrates selector adaptation."""
    return TestDefinition(
        name="selector_adaptation_demo",
        description="Test with intentionally wrong selector to show adaptation",
        steps=[
            TestStep(
                name="Navigate to page",
                action=ActionType.GOTO,
                url="https://example.com",
            ),
            TestStep(
                name="Try wrong selector first",
                action=ActionType.CLICK,
                selector="button.wrong-selector",  # This will fail
                timeout=2000,
            ),
        ],
        evaluators=[],
        browser_config=BrowserConfig(headless=False),
    )


def create_error_recovery_test() -> TestDefinition:
    """Create a test that demonstrates error recovery."""
    return TestDefinition(
        name="error_recovery_demo",
        description="Test with errors to show recovery suggestions",
        steps=[
            TestStep(
                name="Navigate to dynamic page",
                action=ActionType.GOTO,
                url="https://the-internet.herokuapp.com/dynamic_loading/1",
            ),
            TestStep(
                name="Click start button",
                action=ActionType.CLICK,
                selector="#start button",
            ),
            TestStep(
                name="Try to click hidden element (will fail initially)",
                action=ActionType.CLICK,
                selector="#finish",
                timeout=1000,  # Short timeout to trigger error quickly
            ),
        ],
        evaluators=[],
        browser_config=BrowserConfig(headless=False, slow_mo=1000),
    )


async def run_guided_test(test_def: TestDefinition, api_key: str):
    """
    Run a test with Claude guidance.

    Args:
        test_def: Test definition to execute
        api_key: Anthropic API key
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Running test: {test_def.name}")
    logger.info(f"Description: {test_def.description}")
    logger.info(f"{'=' * 60}\n")

    # Create Claude executor
    executor = ClaudeExecutor(
        api_key=api_key,
        model="claude-3-5-haiku-20241022",
        temperature=0.3,
    )

    # Create browser manager
    browser_manager = BrowserSessionManager()
    await browser_manager.start()

    try:
        # Create enhanced test runner
        runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=Path("test_results") / "guided_examples",
            claude_executor=executor,
        )

        # Run test with guidance
        logger.info("Starting guided execution...")
        test_run = await runner.run_test(test_def, guided=True)

        # Print results
        logger.info(f"\n{'=' * 60}")
        logger.info("TEST RESULTS")
        logger.info(f"{'=' * 60}")
        logger.info(f"Status: {test_run.status}")
        logger.info(f"Passed: {test_run.result.passed if test_run.result else 'N/A'}")
        logger.info(f"Duration: {test_run.duration_ms}ms")

        if test_run.guidance_metadata:
            logger.info("\nGUIDANCE STATISTICS:")
            logger.info(
                f"  Steps with guidance: {test_run.guidance_metadata.get('steps_with_guidance', 0)}"
            )
            logger.info(
                f"  Selectors adapted: {test_run.guidance_metadata.get('selectors_adapted', 0)}"
            )
            logger.info(
                f"  Errors recovered: {test_run.guidance_metadata.get('errors_recovered', 0)}"
            )

        logger.info("\nSTEP RESULTS:")
        for i, step_result in enumerate(test_run.result.step_results):
            logger.info(f"\n  Step {i}: {step_result.step_name}")
            logger.info(f"    Success: {step_result.success}")
            logger.info(f"    Duration: {step_result.duration_ms}ms")

            if step_result.claude_guidance:
                logger.info(f"    Claude Guidance: {step_result.claude_guidance[:100]}...")

            if step_result.adapted_selector:
                logger.info(f"    Adapted Selector: {step_result.adapted_selector}")

            if step_result.error_recovery_attempted:
                logger.info(f"    Recovery Action: {step_result.recovery_action}")

            if step_result.error_message:
                logger.info(f"    Error: {step_result.error_message}")

        logger.info(f"\n{'=' * 60}\n")

        return test_run

    finally:
        await browser_manager.stop()


async def run_comparison(test_def: TestDefinition, api_key: str):
    """
    Run test with and without guidance for comparison.

    Args:
        test_def: Test definition
        api_key: Anthropic API key
    """
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON: Standard vs Guided Execution")
    logger.info("=" * 60 + "\n")

    browser_manager = BrowserSessionManager()
    await browser_manager.start()

    try:
        # Run without guidance
        logger.info("1. Running WITHOUT guidance...")
        standard_runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=Path("test_results") / "comparison",
        )
        standard_run = await standard_runner.run_test(test_def, guided=False)

        # Run with guidance
        logger.info("\n2. Running WITH guidance...")
        executor = ClaudeExecutor(api_key=api_key)
        guided_runner = EnhancedTestRunner(
            browser_manager=browser_manager,
            results_dir=Path("test_results") / "comparison",
            claude_executor=executor,
        )
        guided_run = await guided_runner.run_test(test_def, guided=True)

        # Compare results
        logger.info("\n" + "=" * 60)
        logger.info("COMPARISON RESULTS")
        logger.info("=" * 60)
        logger.info("Standard Execution:")
        logger.info(f"  Status: {standard_run.status}")
        logger.info(f"  Duration: {standard_run.duration_ms}ms")
        logger.info(f"  Passed: {standard_run.result.passed if standard_run.result else 'N/A'}")

        logger.info("\nGuided Execution:")
        logger.info(f"  Status: {guided_run.status}")
        logger.info(f"  Duration: {guided_run.duration_ms}ms")
        logger.info(f"  Passed: {guided_run.result.passed if guided_run.result else 'N/A'}")
        logger.info(
            f"  Steps with guidance: {guided_run.guidance_metadata.get('steps_with_guidance', 0)}"
        )
        logger.info(
            f"  Selectors adapted: {guided_run.guidance_metadata.get('selectors_adapted', 0)}"
        )

        # Show guidance overhead
        if standard_run.duration_ms and guided_run.duration_ms:
            overhead = guided_run.duration_ms - standard_run.duration_ms
            overhead_pct = (overhead / standard_run.duration_ms) * 100
            logger.info(f"\nGuidance Overhead: {overhead}ms ({overhead_pct:.1f}%)")

        logger.info("=" * 60 + "\n")

    finally:
        await browser_manager.stop()


async def main():
    """Main function to run examples."""
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set!")
        logger.error("Please set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    logger.info("=" * 60)
    logger.info("Enhanced Test Runner - Guided Execution Examples")
    logger.info("=" * 60 + "\n")

    # Example 1: Basic login test with guidance
    logger.info("EXAMPLE 1: Login Test with Guidance")
    login_test = create_login_test()
    await run_guided_test(login_test, api_key)

    await asyncio.sleep(2)  # Pause between tests

    # Example 2: Selector adaptation demo
    logger.info("\nEXAMPLE 2: Selector Adaptation")
    selector_test = create_selector_adaptation_test()
    await run_guided_test(selector_test, api_key)

    await asyncio.sleep(2)

    # Example 3: Error recovery demo
    logger.info("\nEXAMPLE 3: Error Recovery")
    error_test = create_error_recovery_test()
    await run_guided_test(error_test, api_key)

    await asyncio.sleep(2)

    # Example 4: Comparison
    logger.info("\nEXAMPLE 4: Standard vs Guided Comparison")
    await run_comparison(login_test, api_key)

    logger.info("\n" + "=" * 60)
    logger.info("All examples completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
