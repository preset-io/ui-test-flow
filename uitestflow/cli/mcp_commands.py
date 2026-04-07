"""
MCP-specific CLI commands for UITestFlow.

Provides commands for test generation, guided execution, and MCP server management.
"""

import asyncio
import os
from dataclasses import asdict
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import APIKeyError, GenerationConfig
from uitestflow.mcp.playwright_server import PlaywrightMCPServer
from uitestflow.src.browser_manager import BrowserSessionManager
from uitestflow.src.enhanced_test_runner import EnhancedTestRunner
from uitestflow.src.models import BrowserConfig, TestDefinition
from uitestflow.src.test_parser import YAMLTestParser


console = Console()


# ============================================================================
# Helper Functions
# ============================================================================


def get_api_key() -> str:
    """
    Get Anthropic API key from environment or config.

    Returns:
        API key string

    Raises:
        typer.Exit: If API key not found
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[red]Error:[/red] ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it with: export ANTHROPIC_API_KEY='your-api-key-here'"
        )
        raise typer.Exit(1)
    return api_key


def save_test_yaml(test_def: TestDefinition, output_path: Path) -> None:
    """
    Save test definition to YAML file.

    Args:
        test_def: Test definition to save
        output_path: Path to save file
    """
    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and save as YAML
    test_dict = asdict(test_def)

    with Path(output_path).open("w") as f:
        yaml.dump(test_dict, f, default_flow_style=False, sort_keys=False)


# ============================================================================
# Generate Command
# ============================================================================


def generate_command(
    description: str = typer.Argument(
        ..., help="Natural language description of the test to generate"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Path to save generated test YAML file"
    ),
    model: str = typer.Option(
        "claude-3-5-haiku-20241022",
        "--model",
        "-m",
        help="Claude model to use (haiku or sonnet)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview test without saving to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed generation process"),
    base_url: str | None = typer.Option(None, "--base-url", help="Base URL for the test"),
    temperature: float = typer.Option(
        0.0, "--temperature", "-t", help="Model temperature (0.0-1.0)", min=0.0, max=1.0
    ),
) -> None:
    """
    Generate a test definition from natural language description.

    Uses Claude AI to convert your description into a structured test definition
    that can be executed by UITestFlow.

    Examples:
        uitestflow generate "Login with admin credentials" --output login.yaml

        uitestflow generate "Search for 'playwright' and verify results" \\
            --model claude-3-5-sonnet-20241022 --dry-run

        uitestflow generate "Fill registration form and submit" \\
            --base-url https://example.com --verbose
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Generating Test from Description[/bold cyan]\n"
            f"Model: {model}\n"
            f"Temperature: {temperature}\n"
            f"Dry Run: {dry_run}",
            border_style="cyan",
        )
    )

    if verbose:
        console.print(f"\n[dim]Description:[/dim] {description}\n")

    # Get API key
    try:
        api_key = get_api_key()
    except typer.Exit:
        return

    # Create generator with configuration
    config = GenerationConfig(
        model=model,
        temperature=temperature,
        max_tokens=4000,
    )

    try:
        generator = ClaudeTestGenerator(api_key=api_key, config=config)
    except APIKeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Generate test with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating test definition...", total=None)

        try:
            test_def = asyncio.run(
                generator.generate_test(description=description, base_url=base_url)
            )
        except Exception as e:
            progress.stop()
            console.print(f"\n[red]Generation failed:[/red] {e}")
            raise typer.Exit(1)

    # Display generated test
    console.print("\n[green]✓[/green] Test generated successfully!\n")

    # Show test details
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Test Name", test_def.name)
    table.add_row("Description", test_def.description or "N/A")
    table.add_row("Version", test_def.version)
    table.add_row("Steps", str(len(test_def.steps)))
    table.add_row("Evaluators", str(len(test_def.evaluators)))

    console.print(table)

    if verbose:
        console.print("\n[bold]Test Steps:[/bold]")
        for i, step in enumerate(test_def.steps, 1):
            console.print(f"  {i}. {step.action}: {step.name}")

    # Show YAML preview
    test_yaml = yaml.dump(
        asdict(test_def),
        default_flow_style=False,
        sort_keys=False,
    )
    console.print("\n[bold]Generated YAML:[/bold]")
    syntax = Syntax(test_yaml, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)

    # Save to file unless dry run
    if not dry_run:
        if not output:
            # Generate default filename from test name
            safe_name = test_def.name.lower().replace(" ", "_")
            output = Path(f"{safe_name}.yaml")

        save_test_yaml(test_def, output)
        console.print(f"\n[green]✓[/green] Test saved to: [bold]{output}[/bold]")
    else:
        console.print("\n[yellow]Dry run mode:[/yellow] Test not saved to file")


# ============================================================================
# Run with Claude Command
# ============================================================================


def run_with_claude_command(
    test_file: Path = typer.Argument(..., help="Path to test file (YAML)", exists=True),
    model: str = typer.Option(
        "claude-3-5-haiku-20241022", "--model", "-m", help="Claude model for guidance"
    ),
    guided_only: bool = typer.Option(
        False, "--guided-only", help="Show guidance without executing test"
    ),
    headless: bool = typer.Option(True, "--headless/--headed", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed execution output"),
) -> None:
    """
    Run a test with Claude AI guidance.

    Executes test with real-time guidance from Claude, including adaptive
    selector resolution and error recovery.

    Examples:
        uitestflow run-with-claude login.yaml

        uitestflow run-with-claude test.yaml --model claude-3-5-sonnet-20241022

        uitestflow run-with-claude test.yaml --guided-only --verbose
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Running Test with Claude Guidance[/bold cyan]\n"
            f"Test: {test_file.name}\n"
            f"Model: {model}\n"
            f"Mode: {'guidance only' if guided_only else 'full execution'}",
            border_style="cyan",
        )
    )

    # Get API key
    try:
        api_key = get_api_key()
    except typer.Exit:
        return

    # Parse test definition
    parser = YAMLTestParser()
    try:
        with Path(test_file).open() as f:
            test_def = parser.parse_string(f.read())
    except Exception as e:
        console.print(f"[red]Error parsing test file:[/red] {e}")
        raise typer.Exit(1)

    # Create Claude client
    config = GenerationConfig(model=model)
    try:
        claude_client = ClaudeTestGenerator(api_key=api_key, config=config)
    except APIKeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if guided_only:
        console.print("\n[yellow]Guidance-only mode:[/yellow] Test will not be executed\n")
        # TODO: Implement guidance-only mode
        console.print("[dim]This feature is coming soon[/dim]")
        return

    # Run test with Claude guidance
    browser_config = BrowserConfig(headless=headless)

    async def run_test():
        session_manager = BrowserSessionManager(browser_config)
        runner = EnhancedTestRunner(
            session_manager=session_manager,
            claude_client=claude_client,
        )

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Executing test with Claude guidance...", total=None)

                result = await runner.run_test(test_def)

            # Display results
            console.print("\n[green]✓[/green] Test execution completed!")
            console.print(f"\nStatus: [{'green' if result.passed else 'red'}]{result.status}[/]")
            console.print(f"Duration: {result.duration_ms}ms")
            console.print(f"Steps completed: {len(result.step_results)}/{len(test_def.steps)}")

            if verbose and result.step_results:
                console.print("\n[bold]Step Results:[/bold]")
                for i, step_result in enumerate(result.step_results, 1):
                    status_icon = "✓" if step_result.success else "✗"
                    status_color = "green" if step_result.success else "red"
                    console.print(
                        f"  [{status_color}]{status_icon}[/] Step {i}: {step_result.step_name}"
                    )

            return 0 if result.passed else 1

        finally:
            await session_manager.cleanup()

    exit_code = asyncio.run(run_test())
    raise typer.Exit(exit_code)


# ============================================================================
# MCP Server Command
# ============================================================================


def mcp_server_command(
    port: int = typer.Option(3001, "--port", "-p", help="Port for HTTP transport (if applicable)"),
    transport: str = typer.Option(
        "stdio", "--transport", "-t", help="Transport protocol (stdio or http)"
    ),
    headless: bool = typer.Option(True, "--headless/--headed", help="Browser mode"),
) -> None:
    """
    Start standalone MCP server for Claude integration.

    Launches a Model Context Protocol server that exposes browser automation
    tools to Claude AI for interactive test development.

    Examples:
        uitestflow mcp-server

        uitestflow mcp-server --transport http --port 3001

        uitestflow mcp-server --headed
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Starting MCP Server[/bold cyan]\n"
            f"Transport: {transport}\n"
            f"Port: {port if transport == 'http' else 'N/A'}\n"
            f"Browser: {'headless' if headless else 'headed'}",
            border_style="cyan",
        )
    )

    if transport not in ["stdio", "http"]:
        console.print(f"[red]Error:[/red] Invalid transport '{transport}'. Use 'stdio' or 'http'")
        raise typer.Exit(1)

    browser_config = BrowserConfig(headless=headless)

    async def start_server():
        server = PlaywrightMCPServer(browser_config=browser_config)

        console.print("\n[green]MCP server starting...[/green]")
        console.print("Press CTRL+C to stop\n")

        try:
            if transport == "stdio":
                await server.run_stdio()
            else:
                # HTTP transport not yet implemented
                console.print("[yellow]HTTP transport not yet implemented[/yellow]")
                console.print("Use --transport stdio for now")
                raise typer.Exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down MCP server...[/yellow]")
        finally:
            await server.cleanup()
            console.print("[green]Server stopped[/green]")

    asyncio.run(start_server())


# ============================================================================
# MCP Status Command
# ============================================================================


def mcp_status_command(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status information"),
) -> None:
    """
    Show MCP server status and configuration.

    Displays information about MCP server availability, configured tools,
    and current settings.

    Examples:
        uitestflow mcp-status

        uitestflow mcp-status --verbose
    """
    console.print(
        Panel.fit(
            "[bold cyan]MCP Server Status[/bold cyan]",
            border_style="cyan",
        )
    )

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    api_key_status = "✓ Set" if api_key else "✗ Not set"
    api_key_color = "green" if api_key else "red"

    # Create status table
    table = Table(show_header=False, box=None)
    table.add_column("Item", style="cyan")
    table.add_column("Status")

    table.add_row("API Key", f"[{api_key_color}]{api_key_status}[/]")
    table.add_row("MCP Package", "[green]✓ Installed[/green]")
    table.add_row("Anthropic Package", "[green]✓ Installed[/green]")

    console.print(table)

    if verbose:
        console.print("\n[bold]Available MCP Tools:[/bold]")
        tools = [
            "navigate - Navigate to a URL",
            "click - Click an element",
            "fill - Fill an input field",
            "wait_for - Wait for element to appear",
            "screenshot - Capture page screenshot",
            "get_page_state - Get current page state",
            "get_text - Extract text from element",
            "evaluate_javascript - Execute JavaScript",
            "get_console_logs - Retrieve console logs",
            "select - Select from dropdown",
        ]
        for tool in tools:
            console.print(f"  • {tool}")

        console.print("\n[bold]Configuration:[/bold]")
        console.print("  Default Model: claude-3-5-haiku-20241022")
        console.print("  MCP Server: PlaywrightMCPServer")
        console.print("  Transport: stdio")

    if not api_key:
        console.print("\n[yellow]Warning:[/yellow] Set ANTHROPIC_API_KEY to use Claude features")


# ============================================================================
# Create Typer App for MCP Commands
# ============================================================================


# These functions will be registered in main.py
__all__ = [
    "generate_command",
    "mcp_server_command",
    "mcp_status_command",
    "run_with_claude_command",
]
