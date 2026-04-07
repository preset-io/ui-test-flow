#!/usr/bin/env python3
"""
UITestFlow TUI - Entry point for running the TUI standalone.

This module allows running the TUI directly with:
    python -m uitestflow.tui
"""

import argparse
import sys

from rich.console import Console

from uitestflow.tui.app import run_tui


console = Console()


def main():
    """
    Main entry point for the UITestFlow TUI.

    Command-line Arguments:
        --profile, -p: Default profile to use in TUI
        --config, -c: Path to configuration file
    """
    parser = argparse.ArgumentParser(
        description="UITestFlow Terminal User Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m uitestflow.tui
    python -m uitestflow.tui --profile staging
    python -m uitestflow.tui --config /path/to/.uitest_profiles.yaml

Navigation:
    Arrow keys or hjkl: Navigate
    Tab: Switch panels
    Enter: Select/activate
    ?: Show help
    q or Ctrl+C: Quit
        """,
    )

    parser.add_argument(
        "--profile",
        "-p",
        type=str,
        default=None,
        help="Default profile to use in TUI",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=".uitest_profiles.yaml",
        help="Path to configuration file (default: .uitest_profiles.yaml)",
    )

    parser.add_argument(
        "--theme",
        "-t",
        type=str,
        default="dark",
        choices=["dark", "light", "high-contrast"],
        help="TUI theme (default: dark)",
    )

    parser.add_argument(
        "--results-dir",
        "-r",
        type=str,
        default="test_results",
        help="Directory for test results (default: test_results)",
    )

    args = parser.parse_args()

    try:
        # Run the TUI
        run_tui(
            profile=args.profile,
            theme=args.theme,
            results_dir=args.results_dir,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]TUI stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error starting TUI:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
