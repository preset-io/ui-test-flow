"""Example script demonstrating how to use UITestFlow components."""

import asyncio
import logging
from pathlib import Path

from uitestflow.src.browser_manager import BrowserSessionManager
from uitestflow.src.test_parser import YAMLTestParser
from uitestflow.src.test_runner import TestRunner


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Run a test from a YAML file."""
    # Path to the test file
    test_file = Path(__file__).parent / "simple_login_test.yaml"

    logger.info("Loading test from %s", test_file)

    # Parse the test definition
    parser = YAMLTestParser()
    test_definition = parser.parse_file(test_file)

    logger.info(f"Loaded test: {test_definition.name}")
    logger.info(f"Steps: {len(test_definition.steps)}")
    logger.info(f"Evaluators: {len(test_definition.evaluators)}")

    # Create browser manager and test runner
    browser_manager = BrowserSessionManager()
    await browser_manager.start()

    try:
        test_runner = TestRunner(browser_manager=browser_manager)

        # Run the test
        logger.info("Starting test execution...")
        test_run = await test_runner.run_test(
            test_definition, profile="local", context={"example": "run"}
        )

        # Print results
        print("\n" + "=" * 80)
        print(f"Test Run ID: {test_run.id}")
        print(f"Status: {test_run.status.value}")
        print(f"Duration: {test_run.duration_ms}ms")

        if test_run.result:
            result = test_run.result
            print(f"\nOverall Result: {'PASSED' if result.passed else 'FAILED'}")
            print(f"Score: {result.score:.2f}")
            print(f"\nSteps Executed: {result.steps_executed}")
            print(f"Steps Passed: {result.steps_passed}")
            print(f"Steps Failed: {result.steps_failed}")

            print(f"\nScreenshots: {len(test_run.screenshots)}")
            for screenshot in test_run.screenshots:
                print(f"  - {screenshot.step_name}: {screenshot.file_path}")

            print(f"\nConsole Errors: {len(result.console_errors)}")
            for error in result.console_errors[:5]:  # Show first 5
                print(f"  - {error}")

            print("\nEvaluator Results:")
            for eval_result in result.evaluator_results:
                status = "PASS" if eval_result.passed else "FAIL"
                print(f"  [{status}] {eval_result.evaluator_name}: {eval_result.reason}")

            if result.error_message:
                print(f"\nError: {result.error_message}")

        print("=" * 80 + "\n")

    finally:
        # Cleanup
        await browser_manager.stop()
        logger.info("Browser manager stopped")


if __name__ == "__main__":
    asyncio.run(main())
