#!/usr/bin/env python3
"""
UITestFlow CLI - Natural Language UI Testing Framework

This CLI provides commands for running UI tests, managing profiles,
and generating beautiful test reports.
"""

import sys
from datetime import datetime
from enum import Enum
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uitestflow import __version__
from uitestflow.formatters import OutputFormatter


app = typer.Typer(
    name="uitestflow",
    help="UITestFlow - Natural Language UI Testing Framework",
    add_completion=False,
)

console = Console()


def print_logo():
    """Print UITestFlow ASCII logo."""
    logo = """
  [bold cyan]█░█ █   ▀█▀ █▀▀ █▀ ▀█▀ █▀▀ █░░ █▀█ █░█░█[/bold cyan]
  [bold cyan]█▄█ █    █  ██▄ ▄█  █  █▀  █▄▄ █▄█ ▀▄▀▄▀[/bold cyan]

  [dim]🎭 Natural Language UI Testing[/dim]
  [dim]Powered by Playwright + LLM[/dim]
"""
    console.print(logo)


def version_callback(value: bool):
    """Display version and exit."""
    if value:
        print_logo()
        console.print(f"\n  Version: [green]{__version__}[/green]")
        console.print("  [dim]https://github.com/preset-io/ui-test-flow[/dim]\n")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    UITestFlow - Natural Language UI Testing Framework

    Run UI tests using natural language instructions or YAML definitions.
    """


class OutputFormat(str, Enum):
    """Output format options."""

    json = "json"
    yaml = "yaml"
    table = "table"
    html = "html"


@app.command()
def run(
    test_file: Path = typer.Argument(
        ...,
        help="Path to test file (YAML, JSON, or natural language)",
        exists=True,
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Profile name from .uitest_profiles.yaml",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--headed",
        help="Run browser in headless mode",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for test results",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="Output format",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed output",
    ),
):
    """
    Run a UI test from a test file.

    Example:
        uitestflow run tests/login.yaml --profile staging --headless
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Running UI Test[/bold cyan]\n"
            f"Test: {test_file.name}\n"
            f"Profile: {profile or 'default'}\n"
            f"Mode: {'headless' if headless else 'headed'}",
            border_style="cyan",
        )
    )

    # Mock test execution for demo
    # In production, this would call the actual test runner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading test definition...", total=None)

        # Simulate test execution
        import time

        time.sleep(0.5)
        progress.update(task, description="Initializing browser session...")
        time.sleep(0.5)
        progress.update(task, description="Executing test steps...")
        time.sleep(1.0)
        progress.update(task, description="Running evaluators...")
        time.sleep(0.5)
        progress.update(task, description="Generating report...")
        time.sleep(0.3)

    # Mock test results
    test_results = {
        "test_name": test_file.stem,
        "status": "passed",
        "duration_ms": 2500,
        "timestamp": datetime.now().isoformat(),
        "steps": [
            {"name": "Navigate to login page", "status": "passed", "duration_ms": 800},
            {"name": "Enter credentials", "status": "passed", "duration_ms": 300},
            {"name": "Click login button", "status": "passed", "duration_ms": 400},
            {"name": "Verify dashboard loads", "status": "passed", "duration_ms": 1000},
        ],
        "evaluators": [
            {
                "name": "execution_successful",
                "passed": True,
                "score": 1.0,
                "reason": "All steps completed successfully",
            },
            {
                "name": "all_steps_completed",
                "passed": True,
                "score": 1.0,
                "reason": "All 4 steps were executed",
            },
            {
                "name": "no_console_errors",
                "passed": True,
                "score": 1.0,
                "reason": "No console errors found",
            },
        ],
        "screenshots": [
            "screenshots/login_page.png",
            "screenshots/dashboard.png",
        ],
        "errors": [],
    }

    # Format and display results
    formatter = OutputFormatter(test_results)

    if format == OutputFormat.table:
        formatter.format_table(detailed=verbose)
    elif format == OutputFormat.json:
        console.print(formatter.format_json())
    elif format == OutputFormat.yaml:
        console.print(formatter.format_yaml())
    elif format == OutputFormat.html:
        if not output:
            output = Path(f"reports/{test_file.stem}_report.html")
        html_path = formatter.format_html(output)
        console.print(f"\n[green]✓[/green] HTML report generated: {html_path}")

    # Save results if output file specified
    if output and format != OutputFormat.table:
        formatter.save(output, format.value)
        console.print(f"\n[green]✓[/green] Results saved to: {output}")

    # Exit with appropriate code
    exit_code = 0 if test_results["status"] == "passed" else 1
    sys.exit(exit_code)


@app.command(name="profiles")
def profiles_command():
    """
    Profile management commands.

    Use subcommands: list, test, create, delete
    """
    # This is a group command, subcommands will be added below


profiles_app = typer.Typer(help="Manage test environment profiles")
app.add_typer(profiles_app, name="profiles")


@profiles_app.command("list")
def profiles_list(
    config_file: Path = typer.Option(
        Path(".uitest_profiles.yaml"),
        "--config",
        "-c",
        help="Path to profiles configuration file",
    ),
):
    """
    List all available profiles.

    Example:
        uitestflow profiles list
    """
    console.print(Panel.fit("[bold cyan]Available Profiles[/bold cyan]", border_style="cyan"))

    # Mock profiles for demo
    profiles = {
        "local": {
            "name": "Local Development",
            "base_url": "http://localhost:8018",
            "browser": {"headless": False},
        },
        "staging": {
            "name": "Staging Environment",
            "base_url": "https://staging.example.com",
            "browser": {"headless": True},
        },
        "production": {
            "name": "Production Environment",
            "base_url": "https://app.example.com",
            "browser": {"headless": True},
        },
    }

    table = Table(show_header=True)
    table.add_column("Profile ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Base URL")
    table.add_column("Mode")

    for profile_id, profile in profiles.items():
        mode = "headless" if profile.get("browser", {}).get("headless", True) else "headed"
        table.add_row(
            profile_id,
            profile.get("name", ""),
            profile.get("base_url", ""),
            mode,
        )

    console.print(table)


@profiles_app.command("test")
def profiles_test(
    profile_name: str = typer.Argument(..., help="Profile name to test"),
    config_file: Path = typer.Option(
        Path(".uitest_profiles.yaml"),
        "--config",
        "-c",
        help="Path to profiles configuration file",
    ),
):
    """
    Test connectivity for a profile.

    Example:
        uitestflow profiles test staging
    """
    import asyncio
    import time

    import httpx

    from uitestflow.core.profiles import ProfileManager

    console.print(
        Panel.fit(
            f"[bold cyan]Testing Profile: {profile_name}[/bold cyan]",
            border_style="cyan",
        )
    )

    # Load profile
    try:
        pm = ProfileManager(config_file if config_file.exists() else None)
        profile = pm.get_profile(profile_name)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Failed to load profile: {e}")
        sys.exit(1)

    console.print(f"\n  Profile: {profile.name}")
    console.print(f"  Base URL: {profile.base_url}")
    console.print(f"  Auth Type: {profile.auth.auth_type.value}")
    console.print()

    # Test connectivity
    async def test_connection():
        start_time = time.time()
        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(profile.base_url)
                latency_ms = int((time.time() - start_time) * 1000)

                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "error": None if response.status_code < 400 else f"HTTP {response.status_code}",
                }
        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": None,
                "latency_ms": latency_ms,
                "error": "Connection timeout (10 seconds)",
            }
        except httpx.ConnectError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": None,
                "latency_ms": latency_ms,
                "error": f"Connection failed: {e!s}",
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": None,
                "latency_ms": latency_ms,
                "error": f"Test failed: {e!s}",
            }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Testing connection...", total=None)
        result = asyncio.run(test_connection())

    # Display results
    if result["success"]:
        console.print("\n[green]✓[/green] Profile connectivity test passed!")
        console.print(f"  Status: HTTP {result['status_code']}")
        console.print(f"  Response time: {result['latency_ms']}ms")
        sys.exit(0)
    else:
        console.print("\n[red]✗[/red] Profile connectivity test failed!")
        console.print(f"  Error: {result['error']}")
        if result["latency_ms"]:
            console.print(f"  Time elapsed: {result['latency_ms']}ms")
        sys.exit(1)


@app.command(name="config")
def config_command():
    """
    Configuration management commands.

    Use subcommands: init, validate, show
    """


config_app = typer.Typer(help="Manage UITestFlow configuration")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(
    output: Path = typer.Option(
        Path(".uitest_profiles.yaml"),
        "--output",
        "-o",
        help="Output path for configuration file",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration",
    ),
):
    """
    Initialize a new configuration file.

    Example:
        uitestflow config init
    """
    if output.exists() and not force:
        console.print(f"[yellow]Warning:[/yellow] Configuration file already exists: {output}")
        console.print("Use --force to overwrite")
        sys.exit(1)

    # Create default configuration
    default_config = {
        "default": "local",
        "profiles": {
            "local": {
                "name": "Local Development",
                "base_url": "http://localhost:8018",
                "auth": {
                    "type": "form",
                    "username": "${LOCAL_USERNAME}",
                    "password": "${LOCAL_PASSWORD}",
                },
                "browser": {
                    "headless": False,
                    "slowmo": 500,
                },
            },
            "staging": {
                "name": "Staging Environment",
                "base_url": "https://staging.example.com",
                "auth": {
                    "type": "oauth",
                    "provider": "okta",
                    "client_id": "${OKTA_CLIENT_ID}",
                    "client_secret": "${OKTA_CLIENT_SECRET}",
                },
                "browser": {
                    "headless": True,
                },
            },
        },
    }

    with Path(output).open("w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/green] Configuration file created: {output}")
    console.print("\nEdit this file to customize your test profiles.")


@config_app.command("validate")
def config_validate(
    config_file: Path = typer.Option(
        Path(".uitest_profiles.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
    ),
):
    """
    Validate configuration file.

    Example:
        uitestflow config validate
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Validating Configuration[/bold cyan]\n" f"File: {config_file}",
            border_style="cyan",
        )
    )

    if not config_file.exists():
        console.print(f"[red]✗[/red] Configuration file not found: {config_file}")
        sys.exit(1)

    try:
        with Path(config_file).open() as f:
            config = yaml.safe_load(f)

        # Validate structure
        if not isinstance(config, dict):
            console.print("[red]✗[/red] Invalid configuration: must be a dictionary")
            sys.exit(1)

        if "profiles" not in config:
            console.print("[red]✗[/red] Missing 'profiles' section")
            sys.exit(1)

        profiles = config["profiles"]
        console.print(f"[green]✓[/green] Found {len(profiles)} profile(s)")

        # Validate each profile
        for profile_name, profile in profiles.items():
            required_fields = ["name", "base_url"]
            missing = [f for f in required_fields if f not in profile]

            if missing:
                console.print(
                    f"[yellow]![/yellow] Profile '{profile_name}' missing: {', '.join(missing)}"
                )
            else:
                console.print(f"[green]✓[/green] Profile '{profile_name}' is valid")

        console.print("\n[green]✓[/green] Configuration is valid!")

    except yaml.YAMLError as e:
        console.print(f"[red]✗[/red] YAML parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Validation error: {e}")
        sys.exit(1)


@app.command()
def version_command():
    """
    Show version information.

    Example:
        uitestflow version
    """
    print_logo()
    console.print(f"\n  Version: [green]{__version__}[/green]")
    console.print("  [dim]https://github.com/preset-io/ui-test-flow[/dim]\n")


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        8018,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes (production mode only)",
    ),
):
    """
    Start the FastAPI web server for the Web UI.

    This launches the REST API server that powers the web interface,
    allowing you to create, run, and monitor tests through a browser.

    Development mode (with --reload):
        uitestflow serve --reload

    Production mode:
        uitestflow serve --host 0.0.0.0 --port 8018 --workers 4

    The web UI will be available at http://localhost:8018
    API documentation will be available at http://localhost:8018/docs
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Starting UITestFlow Web Server[/bold cyan]\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"Mode: {'development (auto-reload)' if reload else 'production'}\n"
            f"Workers: {workers if not reload else 1}",
            border_style="cyan",
        )
    )

    try:
        import uvicorn

        # Import here to avoid circular imports and lazy load server
        from uitestflow.server.api import app as server_app

        console.print("\n[green]Server starting...[/green]")
        console.print(f"Web UI: http://{host}:{port}")
        console.print(f"API Docs: http://{host}:{port}/docs")
        console.print(f"OpenAPI: http://{host}:{port}/openapi.json\n")

        if reload:
            console.print(
                "[yellow]Development mode:[/yellow] Auto-reload enabled. " "Press CTRL+C to stop.\n"
            )

        uvicorn.run(
            "uitestflow.server.api:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info",
        )
    except ImportError as e:
        console.print(
            f"[red]Error:[/red] Server dependencies not installed.\n"
            f"Install with: pip install 'uitestflow[server]'\n"
            f"Details: {e}"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting server:[/red] {e}")
        sys.exit(1)


@app.command()
def tui(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Default profile to use in TUI",
    ),
):
    """
    Launch the interactive Terminal User Interface (TUI) dashboard.

    The TUI provides a rich terminal-based interface for managing and
    running tests, viewing results, and monitoring test execution in real-time.

    Features:
        - Browse and run tests interactively
        - Real-time test execution monitoring
        - View test history and results
        - Manage profiles
        - View screenshots and logs

    Example:
        uitestflow tui
        uitestflow tui --profile staging

    Navigation:
        - Use arrow keys or hjkl (vim-style) to navigate
        - Tab: Switch between panels
        - Enter: Select/activate
        - ?: Show help
        - q or Ctrl+C: Quit
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Launching UITestFlow TUI Dashboard[/bold cyan]\n"
            f"Profile: {profile or 'default'}",
            border_style="cyan",
        )
    )

    try:
        # Import here to avoid loading TUI dependencies unless needed
        from uitestflow.tui.app import run_tui

        run_tui(profile=profile)
    except ImportError as e:
        console.print(
            f"[red]Error:[/red] TUI dependencies not installed.\n"
            f"Install with: pip install 'uitestflow[tui]'\n"
            f"Details: {e}"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]TUI stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting TUI:[/red] {e}")
        sys.exit(1)


# ============================================================================
# MCP Commands
# ============================================================================

# Import MCP commands
from uitestflow.cli.mcp_commands import (
    generate_command,
    mcp_server_command,
    mcp_status_command,
    run_with_claude_command,
)


# Register MCP commands
app.command(name="generate")(generate_command)
app.command(name="run-with-claude")(run_with_claude_command)
app.command(name="mcp-server")(mcp_server_command)
app.command(name="mcp-status")(mcp_status_command)


if __name__ == "__main__":
    app()
