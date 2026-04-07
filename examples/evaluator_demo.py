"""
Demo script showing how to use UITestFlow evaluators.
"""

from datetime import datetime, timedelta

from uitestflow.evals import (
    AllStepsCompleted,
    ElementVisible,
    ExecutionSuccessful,
    NoConsoleErrors,
    UrlMatches,
    WithinTimeLimit,
)


def demo_execution_successful():
    """Demonstrate ExecutionSuccessful evaluator."""
    print("\n=== ExecutionSuccessful Evaluator ===")

    evaluator = ExecutionSuccessful()

    # Test case 1: Successful execution
    context = {
        "steps": [
            {"name": "Step 1", "status": "passed"},
            {"name": "Step 2", "status": "passed"},
        ],
        "errors": [],
    }
    result = evaluator.evaluate(context)
    print(f"✓ Success case: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test case 2: Failed execution
    context = {
        "steps": [
            {"name": "Step 1", "status": "passed"},
            {"name": "Step 2", "status": "failed"},
        ],
        "errors": ["Step 2 failed: Element not found"],
    }
    result = evaluator.evaluate(context)
    print(f"✗ Failure case: {result.passed}, Score: {result.score}, Reason: {result.reason}")


def demo_all_steps_completed():
    """Demonstrate AllStepsCompleted evaluator."""
    print("\n=== AllStepsCompleted Evaluator ===")

    evaluator = AllStepsCompleted()

    # Test case: All steps completed
    context = {
        "test_definition": {
            "steps": [
                {"name": "Step 1"},
                {"name": "Step 2"},
                {"name": "Step 3"},
            ]
        },
        "steps": [
            {"name": "Step 1", "status": "passed"},
            {"name": "Step 2", "status": "passed"},
            {"name": "Step 3", "status": "passed"},
        ],
    }
    result = evaluator.evaluate(context)
    print(f"✓ All steps: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test case: Partial completion
    context["steps"] = [
        {"name": "Step 1", "status": "passed"},
        {"name": "Step 2", "status": "passed"},
    ]
    result = evaluator.evaluate(context)
    print(f"✗ Partial: {result.passed}, Score: {result.score}, Reason: {result.reason}")


def demo_no_console_errors():
    """Demonstrate NoConsoleErrors evaluator."""
    print("\n=== NoConsoleErrors Evaluator ===")

    evaluator = NoConsoleErrors(max_errors=0)

    # Test case: No errors
    context = {
        "console_logs": [
            {"level": "info", "message": "Page loaded"},
            {"level": "log", "message": "User logged in"},
        ]
    }
    result = evaluator.evaluate(context)
    print(f"✓ No errors: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test case: With errors
    context = {
        "console_logs": [
            {"level": "info", "message": "Page loaded"},
            {"level": "error", "message": "Failed to load resource"},
            {"level": "error", "message": "Network error"},
        ]
    }
    result = evaluator.evaluate(context)
    print(f"✗ With errors: {result.passed}, Score: {result.score}, Reason: {result.reason}")


def demo_within_time_limit():
    """Demonstrate WithinTimeLimit evaluator."""
    print("\n=== WithinTimeLimit Evaluator ===")

    evaluator = WithinTimeLimit(max_duration_ms=5000)

    # Test case: Within limit
    start = datetime.now()
    end = start + timedelta(milliseconds=3000)
    context = {"start_time": start, "end_time": end}
    result = evaluator.evaluate(context)
    print(f"✓ Within limit: {result.passed}, Score: {result.score:.2f}, Reason: {result.reason}")

    # Test case: Exceeds limit
    end = start + timedelta(milliseconds=6000)
    context = {"start_time": start, "end_time": end}
    result = evaluator.evaluate(context)
    print(f"✗ Exceeds limit: {result.passed}, Score: {result.score}, Reason: {result.reason}")


def demo_element_visible():
    """Demonstrate ElementVisible evaluator."""
    print("\n=== ElementVisible Evaluator ===")

    evaluator = ElementVisible(".dashboard-content", "Dashboard Content")

    # Test case: Element visible
    context = {"page_state": {"visible_elements": [".dashboard-content", ".user-menu", ".navbar"]}}
    result = evaluator.evaluate(context)
    print(f"✓ Visible: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test case: Element not visible
    context = {"page_state": {"visible_elements": [".user-menu", ".navbar"]}}
    result = evaluator.evaluate(context)
    print(f"✗ Not visible: {result.passed}, Score: {result.score}, Reason: {result.reason}")


def demo_url_matches():
    """Demonstrate UrlMatches evaluator."""
    print("\n=== UrlMatches Evaluator ===")

    # Test with exact URL
    evaluator = UrlMatches(expected_url="https://app.example.com/dashboard")
    context = {"page_state": {"url": "https://app.example.com/dashboard"}}
    result = evaluator.evaluate(context)
    print(f"✓ Exact match: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test with pattern
    evaluator = UrlMatches(pattern=r"/dashboard/\d+")
    context = {"page_state": {"url": "https://app.example.com/dashboard/123"}}
    result = evaluator.evaluate(context)
    print(f"✓ Pattern match: {result.passed}, Score: {result.score}, Reason: {result.reason}")

    # Test mismatch
    context = {"page_state": {"url": "https://app.example.com/login"}}
    result = evaluator.evaluate(context)
    print(f"✗ No match: {result.passed}, Score: {result.score}, Reason: {result.reason}")


if __name__ == "__main__":
    print("UITestFlow Evaluators Demo")
    print("=" * 50)

    demo_execution_successful()
    demo_all_steps_completed()
    demo_no_console_errors()
    demo_within_time_limit()
    demo_element_visible()
    demo_url_matches()

    print("\n" + "=" * 50)
    print("Demo completed!")
