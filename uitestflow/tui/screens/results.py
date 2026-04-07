"""
Results screen for UITestFlow TUI.

View test run history and detailed results.
"""

import json
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, Static


class ResultsScreen(Screen):
    """Results viewer screen for test run history."""

    BINDINGS = [
        ("v", "view_details", "View Details"),
        ("d", "delete_run", "Delete"),
        ("r", "refresh", "Refresh"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("q", "app.quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    ResultsScreen {
        background: $surface;
    }

    #results-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #table-panel {
        border: solid $border;
        background: $panel;
        padding: 1;
        height: 1fr;
    }

    #details-panel {
        border: solid $border;
        background: $panel;
        padding: 1;
        height: 40%;
        margin-top: 1;
    }

    DataTable {
        height: 100%;
    }

    #controls {
        height: auto;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose results layout."""
        with Vertical(id="results-container"):
            yield Label("Test Run History", classes="panel-title")

            # Table of results
            with Container(id="table-panel"):
                yield DataTable(id="results_table")

            # Details panel
            with Container(id="details-panel"):
                yield Label("Run Details", classes="panel-title")
                with VerticalScroll():
                    yield Static("Select a run to view details", id="details")

        # Controls
        with Horizontal(id="controls"):
            yield Button("View Details", id="btn_view")
            yield Button("Delete", id="btn_delete", variant="error")
            yield Button("Refresh", id="btn_refresh")
            yield Button("Back", id="btn_back")

    def on_mount(self) -> None:
        """Initialize results table."""
        self._setup_table()
        self._load_results()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in table."""
        self.action_view_details()

    def _setup_table(self) -> None:
        """Setup DataTable columns."""
        table = self.query_one(DataTable)
        table.add_columns("Status", "Test Name", "Duration", "Timestamp", "Run ID")

    def _load_results(self) -> None:
        """Load test results from history."""
        table = self.query_one(DataTable)
        table.clear()

        # Load from app history
        for run in reversed(self.app.test_history):
            status = run.get("status", "unknown")
            name = run.get("name", "Unknown")
            duration = f"{run.get('duration_ms', 0)}ms"
            timestamp = run.get("timestamp", "N/A")
            run_id = run.get("run_id", "N/A")[:8]

            # Status with color
            if status == "passed":
                status_str = "[green]✓ PASSED[/green]"
            elif status == "failed":
                status_str = "[red]✗ FAILED[/red]"
            else:
                status_str = "[yellow]• RUNNING[/yellow]"

            table.add_row(status_str, name, duration, timestamp, run_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_view":
            self.action_view_details()
        elif button_id == "btn_delete":
            self.action_delete_run()
        elif button_id == "btn_refresh":
            self.action_refresh()
        elif button_id == "btn_back":
            self.app.pop_screen()

    def action_view_details(self) -> None:
        """View details of selected run."""
        table = self.query_one(DataTable)
        if table.cursor_row < 0:
            self.notify("No run selected", severity="warning")
            return

        # Get selected run from history
        run_index = len(self.app.test_history) - 1 - table.cursor_row
        if run_index < 0 or run_index >= len(self.app.test_history):
            self.notify("Invalid run selection", severity="error")
            return

        run = self.app.test_history[run_index]
        self._display_run_details(run)

    def action_delete_run(self) -> None:
        """Delete selected run."""
        self.notify("Delete functionality coming soon", timeout=2)

    def action_refresh(self) -> None:
        """Refresh results."""
        self._load_results()
        self.notify("Refreshed", timeout=1)

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def _display_run_details(self, run: dict) -> None:
        """
        Display detailed information about a test run.

        Args:
            run: Test run dictionary
        """
        try:
            run_id = run.get("run_id", "N/A")
            name = run.get("name", "Unknown")
            status = run.get("status", "unknown")
            duration = run.get("duration_ms", 0)

            # Build details text
            details_text = Text()
            details_text.append("Test Run Details\n", style="bold cyan")
            details_text.append("=" * 50 + "\n\n", style="dim")

            details_text.append("Run ID: ", style="bold")
            details_text.append(f"{run_id}\n")

            details_text.append("Test Name: ", style="bold")
            details_text.append(f"{name}\n")

            details_text.append("Status: ", style="bold")
            if status == "passed":
                details_text.append(f"{status.upper()}\n", style="green")
            elif status == "failed":
                details_text.append(f"{status.upper()}\n", style="red")
            else:
                details_text.append(f"{status.upper()}\n", style="yellow")

            details_text.append("Duration: ", style="bold")
            details_text.append(f"{duration}ms\n")

            # Try to load full run data from results directory
            run_dir = self.app.results_dir / run_id
            if run_dir.exists():
                details_text.append("\n" + "=" * 50 + "\n\n", style="dim")

                # Load step results
                steps_file = run_dir / "steps.json"
                if steps_file.exists():
                    with Path(steps_file).open() as f:
                        steps_data = json.load(f)

                    details_text.append("Steps:\n", style="bold cyan")
                    for step in steps_data:
                        step_name = step.get("name", "Unknown")
                        success = step.get("success", False)
                        duration_ms = step.get("duration_ms", 0)

                        symbol = "✓" if success else "✗"
                        style = "green" if success else "red"

                        details_text.append(f"  {symbol} ", style=style)
                        details_text.append(f"{step_name} ({duration_ms}ms)\n")

                        if not success and "error" in step:
                            details_text.append(f"     Error: {step['error']}\n", style="red dim")

                # Load screenshots
                screenshots_dir = run_dir / "screenshots"
                if screenshots_dir.exists():
                    screenshots = list(screenshots_dir.glob("*.png"))
                    if screenshots:
                        details_text.append("\n" + "=" * 50 + "\n\n", style="dim")
                        details_text.append("Screenshots:\n", style="bold cyan")
                        for screenshot in screenshots:
                            details_text.append(f"  - {screenshot.name}\n", style="dim")
                            details_text.append(f"    {screenshot}\n", style="italic dim")

                # Load logs
                logs_file = run_dir / "logs.json"
                if logs_file.exists():
                    with Path(logs_file).open() as f:
                        logs_data = json.load(f)

                    if logs_data:
                        details_text.append("\n" + "=" * 50 + "\n\n", style="dim")
                        details_text.append("Logs:\n", style="bold cyan")
                        for log in logs_data[:10]:  # Show first 10 logs
                            level = log.get("level", "info")
                            message = log.get("message", "")

                            if level == "error":
                                details_text.append("  [ERROR] ", style="red")
                            elif level == "warning":
                                details_text.append("  [WARN]  ", style="yellow")
                            else:
                                details_text.append("  [INFO]  ", style="dim")

                            details_text.append(f"{message}\n")

                        if len(logs_data) > 10:
                            details_text.append(
                                f"\n  ... and {len(logs_data) - 10} more logs\n", style="dim"
                            )

                # Load evaluator results
                eval_file = run_dir / "evaluators.json"
                if eval_file.exists():
                    with Path(eval_file).open() as f:
                        eval_data = json.load(f)

                    if eval_data:
                        details_text.append("\n" + "=" * 50 + "\n\n", style="dim")
                        details_text.append("Evaluators:\n", style="bold cyan")
                        for evaluator in eval_data:
                            eval_name = evaluator.get("name", "Unknown")
                            passed = evaluator.get("passed", False)
                            score = evaluator.get("score", 0.0)

                            symbol = "✓" if passed else "✗"
                            style = "green" if passed else "red"

                            details_text.append(f"  {symbol} ", style=style)
                            details_text.append(f"{eval_name} (score: {score:.2f})\n")

                            if "reason" in evaluator:
                                details_text.append(f"     {evaluator['reason']}\n", style="dim")

            else:
                details_text.append(
                    "\n[yellow]Full run data not found in results directory[/yellow]\n"
                )

            # Display in details panel
            details_widget = self.query_one("#details", Static)
            details_widget.update(details_text)

            self.notify(f"Loaded details for run {run_id[:8]}", timeout=2)

        except Exception as e:
            self.notify(f"Error loading run details: {e}", severity="error")
            details_widget = self.query_one("#details", Static)
            details_widget.update(f"[red]Error loading details: {e}[/red]")
