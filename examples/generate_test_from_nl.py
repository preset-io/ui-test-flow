#!/usr/bin/env python3
"""
Example: Generate Test Definitions from Natural Language

This example demonstrates how to use the ClaudeTestGenerator to create
test definitions from natural language descriptions.

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- anthropic>=0.28.0 installed

Usage:
    python examples/generate_test_from_nl.py
"""

import asyncio
import os
import sys
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import GenerationConfig, LLMError


async def generate_login_test() -> None:
    """Generate a simple login test."""
    print("\n" + "=" * 80)
    print("Example 1: Simple Login Test")
    print("=" * 80)

    description = "Login with username 'admin' and password 'password123'"
    print(f"\nDescription: {description}\n")

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(description)

        print(f"Generated test: {test_def.name}")
        print(f"Number of steps: {len(test_def.steps)}")
        print(f"Number of evaluators: {len(test_def.evaluators)}")

        print("\nSteps:")
        for i, step in enumerate(test_def.steps, 1):
            print(f"  {i}. {step.name} ({step.action})")
            if step.selector:
                print(f"     Selector: {step.selector}")
            if step.value:
                print(f"     Value: {step.value}")

        print("\nEvaluators:")
        for evaluator in test_def.evaluators:
            print(f"  - {evaluator.name} ({evaluator.type})")

    except LLMError as e:
        print(f"Error: {e.message}")
        if e.details:
            print(f"Details: {e.details}")


async def generate_form_test() -> None:
    """Generate a form submission test."""
    print("\n" + "=" * 80)
    print("Example 2: Form Submission Test")
    print("=" * 80)

    description = """
    Fill out a contact form with the following information:
    - Name: John Doe
    - Email: john.doe@example.com
    - Subject: Website Feedback
    - Message: Great website! Keep up the good work.
    Then submit the form and verify a success message appears.
    """
    print(f"\nDescription: {description.strip()}\n")

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description,
            base_url="https://example.com/contact",
        )

        print(f"Generated test: {test_def.name}")
        print(f"Base URL: {test_def.url}")
        print(f"Number of steps: {len(test_def.steps)}")

        print("\nSteps:")
        for i, step in enumerate(test_def.steps, 1):
            print(f"  {i}. {step.name} ({step.action})")

    except LLMError as e:
        print(f"Error: {e.message}")


async def generate_search_test() -> None:
    """Generate a search test."""
    print("\n" + "=" * 80)
    print("Example 3: Search Test")
    print("=" * 80)

    description = "Search for 'playwright automation' and verify at least 5 results appear"
    print(f"\nDescription: {description}\n")

    try:
        # Use custom configuration for faster generation
        config = GenerationConfig(
            model="claude-3-5-haiku-20241022",
            temperature=0.2,
            max_tokens=2048,
        )

        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description,
            base_url="https://www.google.com",
            config_override=config,
        )

        print(f"Generated test: {test_def.name}")
        print(f"Model used: {config.model}")
        print(f"Temperature: {config.temperature}")

        print("\nSteps:")
        for i, step in enumerate(test_def.steps, 1):
            action_str = str(step.action)
            print(f"  {i}. {step.name} ({action_str})")

    except LLMError as e:
        print(f"Error: {e.message}")


async def generate_multi_page_workflow() -> None:
    """Generate a multi-page workflow test."""
    print("\n" + "=" * 80)
    print("Example 4: Multi-Page Workflow")
    print("=" * 80)

    description = """
    1. Navigate to the login page
    2. Login with valid credentials
    3. Go to the user profile page
    4. Update the user's email address to 'newemail@example.com'
    5. Save the changes
    6. Verify a success message appears
    7. Logout
    """
    print(f"\nDescription: {description.strip()}\n")

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(description)

        print(f"Generated test: {test_def.name}")
        print(f"Number of steps: {len(test_def.steps)}")
        print(f"Tags: {', '.join(test_def.tags) if test_def.tags else 'None'}")

        print("\nWorkflow Steps:")
        for i, step in enumerate(test_def.steps, 1):
            print(f"  {i}. {step.name}")

    except LLMError as e:
        print(f"Error: {e.message}")


async def demonstrate_error_handling() -> None:
    """Demonstrate error handling."""
    print("\n" + "=" * 80)
    print("Example 5: Error Handling")
    print("=" * 80)

    # Test with empty description
    print("\nTesting with empty description...")
    try:
        generator = ClaudeTestGenerator()
        await generator.generate_test("")
    except LLMError as e:
        print(f"✓ Correctly caught error: {e.message}")

    # Test with invalid API key
    print("\nTesting with invalid API key...")
    try:
        from uitestflow.llm.types import APIKeyError

        generator = ClaudeTestGenerator(api_key="invalid-key")
        # Don't actually call API
        print("✓ Generator created (would fail on actual API call)")
    except APIKeyError as e:
        print(f"✓ Correctly caught error: {e.message}")


async def save_test_to_yaml() -> None:
    """Generate test and save to YAML file."""
    print("\n" + "=" * 80)
    print("Example 6: Save Test to YAML")
    print("=" * 80)

    description = "Login test for e-commerce application"
    print(f"\nDescription: {description}\n")

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description,
            base_url="https://shop.example.com",
        )

        # Convert to dict for YAML export
        from dataclasses import asdict

        import yaml

        test_dict = asdict(test_def)

        # Save to file
        output_file = Path(__file__).parent / "generated_login_test.yaml"
        with Path(output_file).open("w") as f:
            yaml.dump(test_dict, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Test saved to: {output_file}")
        print(f"  Test name: {test_def.name}")
        print(f"  Steps: {len(test_def.steps)}")
        print(f"  Evaluators: {len(test_def.evaluators)}")

    except LLMError as e:
        print(f"Error: {e.message}")
    except Exception as e:
        print(f"Error saving YAML: {e}")


async def main() -> None:
    """Run all examples."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    print("Claude Test Generation Examples")
    print("=" * 80)
    print("\nThis script demonstrates generating test definitions from")
    print("natural language using Claude AI.\n")

    try:
        # Run examples
        await generate_login_test()
        await generate_form_test()
        await generate_search_test()
        await generate_multi_page_workflow()
        await demonstrate_error_handling()
        await save_test_to_yaml()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
