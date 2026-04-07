#!/usr/bin/env python3
"""
UITestFlow MCP API Client Example

Demonstrates how to use the UITestFlow MCP REST API to:
1. Check MCP status
2. Generate tests from natural language
3. Execute tests with Claude guidance
4. Retrieve test results and feedback
5. Monitor execution via WebSocket (optional)

Requirements:
    pip install httpx websockets

Environment:
    ANTHROPIC_API_KEY - Your Anthropic API key
    UITESTFLOW_API_URL - UITestFlow API URL (default: http://localhost:8018)
"""

import asyncio
import json
import os
import sys
from typing import Any

import httpx


# ============================================================================
# Configuration
# ============================================================================

API_URL = os.getenv("UITESTFLOW_API_URL", "http://localhost:8018")
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Headers for API requests
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


# ============================================================================
# API Client Functions
# ============================================================================


async def check_mcp_status() -> dict[str, Any]:
    """
    Check MCP server status.

    Returns:
        Status information including available tools and configuration
    """
    print("📊 Checking MCP status...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/api/mcp/status")
        response.raise_for_status()

        status = response.json()

        print(f"  MCP Enabled: {status['mcp_enabled']}")
        print(f"  Server Available: {status['server_available']}")
        print(f"  API Key Configured: {status['api_key_configured']}")
        print(f"  Default Model: {status['default_model']}")
        print(f"  Transport: {status['transport']}")
        print(f"  Available Tools: {len(status['available_tools'])}")

        return status


async def generate_test(
    description: str,
    base_url: str | None = None,
    model: str = "claude-3-5-haiku-20241022",
    save: bool = False,
) -> dict[str, Any]:
    """
    Generate a test from natural language description.

    Args:
        description: Natural language test description
        base_url: Optional base URL for the test
        model: Claude model to use
        save: Whether to save test to database

    Returns:
        Generated test definition with metadata
    """
    print("\n🤖 Generating test from description...")
    print(f"  Description: {description}")
    print(f"  Model: {model}")

    payload = {
        "description": description,
        "model": model,
        "save": save,
    }

    if base_url:
        payload["base_url"] = base_url

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_URL}/api/mcp/generate",
            headers=HEADERS,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()

        print(f"  ✓ Test generated in {result['generation_time_ms']}ms")
        print(f"  Test ID: {result['test_id']}")
        print(f"  Test Name: {result['test_definition']['name']}")
        print(f"  Steps: {len(result['test_definition']['steps'])}")

        return result


async def execute_test(
    test_definition: dict[str, Any] | None = None,
    test_id: str | None = None,
    with_claude: bool = True,
    model: str = "claude-3-5-haiku-20241022",
    headless: bool = True,
) -> dict[str, Any]:
    """
    Execute a test with optional Claude guidance.

    Args:
        test_definition: Inline test definition (dict)
        test_id: ID of saved test to execute
        with_claude: Enable Claude guidance
        model: Claude model for guidance
        headless: Run browser in headless mode

    Returns:
        Execution response with run_id
    """
    print("\n▶️  Executing test...")
    print(f"  With Claude: {with_claude}")
    print(f"  Model: {model if with_claude else 'N/A'}")
    print(f"  Headless: {headless}")

    payload = {
        "with_claude": with_claude,
        "model": model,
        "headless": headless,
    }

    if test_definition:
        payload["test_definition"] = test_definition
    elif test_id:
        payload["test_id"] = test_id
    else:
        raise ValueError("Either test_definition or test_id must be provided")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_URL}/api/mcp/execute",
            headers=HEADERS,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()

        print("  ✓ Test queued")
        print(f"  Run ID: {result['run_id']}")
        print(f"  Status: {result['status']}")

        return result


async def get_feedback(run_id: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """
    Retrieve Claude feedback for a test run.

    Args:
        run_id: Test run ID
        page: Page number
        page_size: Items per page

    Returns:
        Feedback data with step-by-step guidance
    """
    print(f"\n💬 Retrieving feedback for run {run_id}...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/api/mcp/feedback/{run_id}",
            params={"page": page, "page_size": page_size},
        )
        response.raise_for_status()

        feedback = response.json()

        print(f"  Test: {feedback['test_name']}")
        print(f"  Total Steps: {feedback['total_steps']}")
        print(f"  Feedback Items: {len(feedback['feedback_items'])}")

        return feedback


# ============================================================================
# Example Workflows
# ============================================================================


async def workflow_simple_generation():
    """
    Simple workflow: Generate a test.
    """
    print("\n" + "=" * 60)
    print("Workflow 1: Simple Test Generation")
    print("=" * 60)

    result = await generate_test(
        description="Navigate to google.com and search for 'UITestFlow'",
        base_url="https://google.com",
        save=False,
    )

    # Display generated test
    print("\n📄 Generated Test Definition:")
    print(json.dumps(result["test_definition"], indent=2))

    return result


async def workflow_generate_and_execute():
    """
    Complete workflow: Generate test and execute it.
    """
    print("\n" + "=" * 60)
    print("Workflow 2: Generate and Execute")
    print("=" * 60)

    # Step 1: Generate test
    gen_result = await generate_test(
        description="Navigate to example.com and verify the page title",
        save=False,
    )

    test_def = gen_result["test_definition"]

    # Step 2: Execute test (without Claude to keep it simple)
    exec_result = await execute_test(
        test_definition=test_def,
        with_claude=False,
        headless=True,
    )

    run_id = exec_result["run_id"]

    # Step 3: Wait a bit for execution (in real app, use WebSocket)
    print("\n⏳ Waiting for test execution...")
    await asyncio.sleep(5)

    # Step 4: Try to get feedback (may fail if run not found in DB yet)
    try:
        feedback = await get_feedback(run_id)
        print("\n✓ Feedback retrieved successfully")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print("\n⚠️  Run not found (may not be persisted in demo mode)")
        else:
            raise

    return exec_result


async def workflow_with_claude_guidance():
    """
    Advanced workflow: Generate and execute with Claude guidance.
    """
    print("\n" + "=" * 60)
    print("Workflow 3: Execution with Claude Guidance")
    print("=" * 60)

    # Generate a more complex test
    gen_result = await generate_test(
        description=(
            "Login to the application with username 'demo' and password 'demo123', "
            "navigate to the settings page, and update the email address"
        ),
        model="claude-3-5-haiku-20241022",
        save=False,
    )

    print("\n📄 Generated Complex Test:")
    test_def = gen_result["test_definition"]
    print(f"  Name: {test_def['name']}")
    print(f"  Steps: {len(test_def['steps'])}")

    for i, step in enumerate(test_def["steps"], 1):
        print(f"    {i}. {step['action']}: {step.get('name', 'N/A')}")

    # Execute with Claude guidance
    print("\n▶️  Would execute with Claude guidance:")
    print("  (Skipping actual execution to avoid browser automation)")

    # In real usage:
    # exec_result = await execute_test(
    #     test_definition=test_def,
    #     with_claude=True,
    #     model="claude-3-5-haiku-20241022",
    # )


async def workflow_multiple_tests():
    """
    Batch workflow: Generate multiple tests.
    """
    print("\n" + "=" * 60)
    print("Workflow 4: Batch Test Generation")
    print("=" * 60)

    test_descriptions = [
        "Navigate to homepage and verify logo is visible",
        "Search for a product and add it to cart",
        "Fill out contact form and submit",
        "Navigate through multi-step checkout process",
    ]

    generated_tests = []

    for i, description in enumerate(test_descriptions, 1):
        print(f"\n[{i}/{len(test_descriptions)}] Generating test...")

        result = await generate_test(
            description=description,
            save=False,
        )

        generated_tests.append(result)

        # Rate limiting - wait between requests
        if i < len(test_descriptions):
            await asyncio.sleep(1)

    print(f"\n✓ Generated {len(generated_tests)} tests successfully")

    return generated_tests


# ============================================================================
# Main
# ============================================================================


async def main():
    """Main entry point."""
    print("=" * 60)
    print("UITestFlow MCP API Client Example")
    print("=" * 60)

    # Check prerequisites
    if not API_KEY:
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print(f"\n✓ API Key: {API_KEY[:10]}...")
    print(f"✓ API URL: {API_URL}")

    try:
        # Check if server is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{API_URL}/health", timeout=5.0)
                print(f"✓ Server Status: {response.json()['status']}")
            except httpx.ConnectError:
                print(f"\n❌ Error: Cannot connect to {API_URL}")
                print("Make sure the UITestFlow server is running:")
                print("  uitestflow serve --port 8018")
                sys.exit(1)

        # Check MCP status
        await check_mcp_status()

        # Run workflows
        await workflow_simple_generation()
        await workflow_generate_and_execute()
        await workflow_with_claude_guidance()
        await workflow_multiple_tests()

        print("\n" + "=" * 60)
        print("✓ All workflows completed successfully!")
        print("=" * 60)

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
