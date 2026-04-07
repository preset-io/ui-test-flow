"""
Comprehensive examples of MCP-powered test generation.

This script demonstrates various scenarios for generating tests from
natural language descriptions using Claude and the MCP Playwright integration.

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - uitestflow installed with MCP support
    - Playwright browsers installed

Usage:
    python examples/mcp_test_generation.py
"""

import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Import UITestFlow components
from uitestflow.llm.claude_client import ClaudeTestGenerator


console = Console()


async def example_1_simple_login():
    """Example 1: Generate a simple login test."""
    console.print("\n[bold cyan]Example 1: Simple Login Test[/bold cyan]")
    console.print("Description: Basic form authentication flow\n")

    description = """
    Test login functionality:
    1. Navigate to http://example.com/login
    2. Fill username field with 'admin'
    3. Fill password field with 'password123'
    4. Click the login button
    5. Verify successful login by checking for dashboard element
    """

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description=description,
            base_url="http://example.com",
            model="claude-3-5-haiku-20241022",
            temperature=0.3,
        )

        console.print("[green]Test generated successfully![/green]\n")
        console.print(f"Test Name: {test_def.name}")
        console.print(f"Steps: {len(test_def.steps)}")
        console.print(f"Evaluators: {len(test_def.evaluators)}\n")

        # Show YAML representation
        yaml_content = test_def.model_dump_json(indent=2)
        syntax = Syntax(yaml_content, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Generated Test Definition"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_2_complex_form():
    """Example 2: Generate a complex form submission test."""
    console.print("\n[bold cyan]Example 2: Complex Form Submission[/bold cyan]")
    console.print("Description: Multi-field form with validation\n")

    description = """
    Test user registration form:
    1. Navigate to registration page
    2. Fill in first name: 'John'
    3. Fill in last name: 'Doe'
    4. Fill in email: 'john.doe@example.com'
    5. Fill in password: 'SecurePass123!'
    6. Fill in confirm password: 'SecurePass123!'
    7. Select country from dropdown: 'United States'
    8. Check the 'Accept Terms' checkbox
    9. Click submit button
    10. Wait for success message
    11. Verify URL changes to /dashboard
    """

    try:
        generator = ClaudeTestGenerator(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-5-haiku-20241022",
        )

        test_def = await generator.generate_test(
            description=description,
            base_url="http://example.com",
        )

        console.print("[green]Complex form test generated![/green]\n")
        console.print(f"Steps generated: {len(test_def.steps)}")

        # Show step actions
        console.print("\n[bold]Step Actions:[/bold]")
        for i, step in enumerate(test_def.steps, 1):
            console.print(f"  {i}. {step.action}: {step.name}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_3_search_workflow():
    """Example 3: Generate a search and filter test."""
    console.print("\n[bold cyan]Example 3: Search Workflow[/bold cyan]")
    console.print("Description: Search with filters and result validation\n")

    description = """
    Test search functionality:
    1. Go to the home page
    2. Enter 'laptop' in the search box
    3. Click the search button
    4. Wait for search results to load
    5. Apply filter: Price range $500-$1000
    6. Apply filter: Brand - 'Dell'
    7. Verify at least 5 results are displayed
    8. Click on the first result
    9. Verify product detail page loads
    10. Check that product title contains 'laptop'
    """

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description=description,
            base_url="http://shop.example.com",
            temperature=0.3,
        )

        console.print("[green]Search workflow test generated![/green]\n")

        # Show evaluators
        console.print("[bold]Evaluators:[/bold]")
        for evaluator in test_def.evaluators:
            console.print(f"  - {evaluator.name} ({evaluator.evaluator_type})")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_4_multi_page_navigation():
    """Example 4: Generate a multi-page navigation test."""
    console.print("\n[bold cyan]Example 4: Multi-Page Navigation[/bold cyan]")
    console.print("Description: Navigate through multiple pages\n")

    description = """
    Test dashboard navigation:
    1. Login to the application
    2. Navigate to Settings page
    3. Verify Settings page title
    4. Navigate to Profile page
    5. Verify Profile page has user information
    6. Navigate to Reports page
    7. Verify Reports page has at least one chart
    8. Return to Dashboard
    9. Verify Dashboard URL is correct
    """

    try:
        generator = ClaudeTestGenerator(
            model="claude-3-5-haiku-20241022",
        )

        test_def = await generator.generate_test(
            description=description,
            base_url="http://app.example.com",
        )

        console.print("[green]Navigation test generated![/green]\n")
        console.print(f"Total steps: {len(test_def.steps)}")

        # Check if MCP metadata is included
        if test_def.mcp_metadata:
            console.print("\n[bold]MCP Metadata:[/bold]")
            console.print(f"  Model: {test_def.mcp_metadata.generation_model}")
            console.print(f"  Temperature: {test_def.mcp_metadata.generation_temperature}")
            console.print(f"  Timestamp: {test_def.mcp_metadata.generation_timestamp}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_5_e2e_shopping():
    """Example 5: Generate an end-to-end shopping flow."""
    console.print("\n[bold cyan]Example 5: E2E Shopping Flow[/bold cyan]")
    console.print("Description: Complete shopping journey\n")

    description = """
    Test complete shopping flow:
    1. Navigate to the shop homepage
    2. Search for 'wireless mouse'
    3. Select the first product from results
    4. Click 'Add to Cart' button
    5. Continue shopping - search for 'keyboard'
    6. Add second product to cart
    7. Click cart icon to view cart
    8. Verify cart has 2 items
    9. Click 'Proceed to Checkout'
    10. Fill shipping information
    11. Select shipping method
    12. Fill payment information (test mode)
    13. Review order summary
    14. Click 'Place Order'
    15. Wait for confirmation page
    16. Verify order number is displayed
    17. Verify confirmation email message
    """

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description=description,
            base_url="http://shop.example.com",
            model="claude-3-5-sonnet-20241022",  # Use Sonnet for complex flows
            temperature=0.2,  # Lower temperature for more deterministic output
        )

        console.print("[green]E2E shopping test generated![/green]\n")
        console.print(f"Total steps: {len(test_def.steps)}")
        console.print(f"Evaluators: {len(test_def.evaluators)}")

        # Save to file
        output_dir = Path("generated_tests")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "e2e_shopping_flow.yaml"

        # This would save the test definition to YAML
        console.print(f"\n[yellow]Would save to: {output_file}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_6_error_handling():
    """Example 6: Generate a test with error handling."""
    console.print("\n[bold cyan]Example 6: Error Handling Test[/bold cyan]")
    console.print("Description: Test with intentional errors and recovery\n")

    description = """
    Test form validation and error handling:
    1. Navigate to registration form
    2. Try to submit empty form
    3. Verify error messages appear
    4. Fill only email field incorrectly (invalid format)
    5. Try to submit
    6. Verify email validation error
    7. Fill email correctly
    8. Fill password field (too short)
    9. Verify password validation error
    10. Fill password correctly
    11. Submit form successfully
    12. Verify success message
    """

    try:
        generator = ClaudeTestGenerator()
        test_def = await generator.generate_test(
            description=description,
            base_url="http://example.com",
        )

        console.print("[green]Error handling test generated![/green]\n")

        # Show steps with wait_for actions
        wait_steps = [s for s in test_def.steps if s.action == "wait_for"]
        console.print(f"[bold]Wait/Verification steps: {len(wait_steps)}[/bold]")
        for step in wait_steps:
            console.print(f"  - {step.name}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_7_configuration_options():
    """Example 7: Demonstrate configuration options."""
    console.print("\n[bold cyan]Example 7: Configuration Options[/bold cyan]")
    console.print("Description: Show various configuration options\n")

    description = "Simple test: Navigate to homepage and verify title"

    try:
        # Example with custom configuration
        generator = ClaudeTestGenerator(
            model="claude-3-5-haiku-20241022",
            temperature=0.5,
            max_tokens=2048,
            timeout=30,
        )

        test_def = await generator.generate_test(
            description=description,
            base_url="http://example.com",
        )

        console.print("[green]Test generated with custom config![/green]\n")

        # Show configuration used
        if test_def.mcp_metadata:
            console.print("[bold]Generation Configuration:[/bold]")
            console.print(f"  Model: {test_def.mcp_metadata.generation_model}")
            console.print(f"  Temperature: {test_def.mcp_metadata.generation_temperature}")
            for key, value in test_def.mcp_metadata.generation_config.items():
                console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def main():
    """Run all examples."""
    console.print(
        Panel.fit(
            "[bold]UITestFlow MCP Test Generation Examples[/bold]\n"
            "Demonstrating Claude-powered test generation from natural language",
            border_style="cyan",
        )
    )

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print(
            "\n[bold red]ERROR:[/bold red] ANTHROPIC_API_KEY environment variable not set!\n"
            "Get your API key from: https://console.anthropic.com/settings/keys\n"
            "Set it with: export ANTHROPIC_API_KEY='your-key-here'\n"
        )
        return

    examples = [
        ("Simple Login", example_1_simple_login),
        ("Complex Form", example_2_complex_form),
        ("Search Workflow", example_3_search_workflow),
        ("Multi-Page Navigation", example_4_multi_page_navigation),
        ("E2E Shopping", example_5_e2e_shopping),
        ("Error Handling", example_6_error_handling),
        ("Configuration Options", example_7_configuration_options),
    ]

    console.print("\n[bold]Available Examples:[/bold]")
    for i, (name, _) in enumerate(examples, 1):
        console.print(f"  {i}. {name}")

    console.print("\n[dim]Running all examples...[/dim]\n")

    for name, example_func in examples:
        try:
            await example_func()
            await asyncio.sleep(1)  # Brief pause between examples
        except KeyboardInterrupt:
            console.print("\n[yellow]Examples interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Failed to run {name}: {e}[/red]")
            continue

    console.print("\n[bold green]All examples completed![/bold green]")
    console.print("\n[dim]Note: These are demonstrations. Actual test generation")
    console.print("may vary based on Claude model and configuration.[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
