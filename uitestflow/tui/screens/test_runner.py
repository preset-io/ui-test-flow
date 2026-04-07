"""
Test Runner screen for UITestFlow TUI.

Run tests with live execution view and progress tracking.
"""

import asyncio
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, ProgressBar, Static

from ...src.test_parser import YAMLTestParser
from ...src.test_runner import TestRunner


class TestRunnerScreen(Screen):
    """Test runner screen for executing tests with live feedback."""

    BINDINGS = [
        ("r", "run_test", "Run"),
        ("s", "stop_test", "Stop"),
        ("q", "app.quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    TestRunnerScreen {
        background: $surface;
    }

    #runner-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #test-info {
        border: solid $border;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }

    #progress-panel {
        border: solid $border;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }

    #output-panel {
        border: solid $border;
        background: $panel;
        padding: 1;
        height: 1fr;
    }

    .panel-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .step-running {
        color: $primary;
    }

    .step-passed {
        color: $success;
    }

    .step-failed {
        color: $error;
    }

    #controls {
        height: auto;
        padding: 1;
        background: $surface;
    }
    """

    def __init__(self):
        super().__init__()
        self.test_path: Path | None = None
        self.runner: TestRunner | None = None
        self.is_running: bool = False
        self.abort_requested: bool = False
        self.current_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose test runner layout."""
        with Vertical(id="runner-container"):
            # Test info section
            with Container(id="test-info"):
                yield Label("Test Information", classes="panel-title")
                yield Static("No test selected", id="test-name")
                yield Static("", id="test-description")

            # Progress section
            with Container(id="progress-panel"):
                yield Label("Progress", classes="panel-title")
                yield ProgressBar(total=100, show_eta=True, id="progress_bar")
                yield Static("Ready to run", id="progress_status")

            # Output section
            with Container(id="output-panel"):
                yield Label("Execution Log", classes="panel-title")
                with VerticalScroll(id="log-scroll"):
                    yield Static("", id="log-output")

        # Control buttons
        with Horizontal(id="controls"):
            yield Button("Run Test", id="btn_run", variant="success")
            yield Button("Abort Test", id="btn_abort", variant="error", disabled=True)
            yield Button("Select Test", id="btn_select")
            yield Button("Back", id="btn_back")

    def on_mount(self) -> None:
        """Initialize runner on mount."""
        # Check if a test was selected
        if self.app.selected_test_path:
            self.test_path = self.app.selected_test_path
            self._load_test_info()

    def _load_test_info(self) -> None:
        """Load and display test information."""
        if not self.test_path:
            return

        try:
            parser = YAMLTestParser()
            test_def = parser.parse_file(self.test_path)

            # Update UI with test info
            self.query_one("#test-name", Static).update(f"[bold]{test_def.name}[/bold]")

            if test_def.description:
                self.query_one("#test-description", Static).update(test_def.description)

            # Update progress bar total
            total_steps = len(test_def.steps)
            progress = self.query_one("#progress_bar", ProgressBar)
            progress.update(total=total_steps, progress=0)

            self.notify(f"Loaded test: {test_def.name}", timeout=2)

        except Exception as e:
            self.notify(f"Error loading test: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_run":
            self.action_run_test()
        elif button_id == "btn_abort":
            self.action_abort_test()
        elif button_id == "btn_select":
            self.app.action_screen_explorer()
        elif button_id == "btn_back":
            self.app.pop_screen()

    def action_run_test(self) -> None:
        """Run the selected test."""
        if not self.test_path:
            self.notify("No test selected", severity="warning")
            return

        if self.is_running:
            self.notify("Test is already running", severity="warning")
            return

        # Reset abort flag
        self.abort_requested = False

        # Start test execution in background
        self.current_task = asyncio.create_task(self._run_test_async())

    async def _run_test_async(self) -> None:
        """Run test asynchronously with live updates."""
        self.is_running = True

        # Update button states
        self.query_one("#btn_run", Button).disabled = True
        self.query_one("#btn_abort", Button).disabled = False

        # Reset progress
        progress = self.query_one("#progress_bar", ProgressBar)
        progress.update(progress=0)

        log_output = self.query_one("#log-output", Static)
        log_output.update("")

        try:
            # Parse test
            parser = YAMLTestParser()
            test_def = parser.parse_file(self.test_path)

            self._log(f"Starting test: {test_def.name}")
            self._update_status("Running...", "step-running")

            # Create runner
            self.runner = TestRunner(results_dir=self.app.results_dir)

            # Run test
            test_run = await self.runner.run_test(
                test_def, profile=self.app.profile, context={"source": "tui"}
            )

            # Update progress to completion
            progress.update(progress=progress.total)

            # Display results
            if test_run.result:
                if test_run.result.passed:
                    self._log("✓ Test PASSED", "step-passed")
                    self._update_status(
                        f"Completed successfully in {test_run.duration_ms}ms",
                        "step-passed",
                    )
                    self.notify("Test passed!", severity="information")
                else:
                    self._log("✗ Test FAILED", "step-failed")
                    self._update_status(f"Failed after {test_run.duration_ms}ms", "step-failed")
                    self.notify("Test failed!", severity="error")

                    if test_run.result.error_message:
                        self._log(f"Error: {test_run.result.error_message}", "step-failed")

                # Show step results
                for step_result in test_run.result.step_results:
                    status_class = "step-passed" if step_result.success else "step-failed"
                    symbol = "✓" if step_result.success else "✗"
                    self._log(
                        f"  {symbol} {step_result.step_name} ({step_result.duration_ms}ms)",
                        status_class,
                    )

                # Store in app history
                self.app.test_history.append({
                    "name": test_def.name,
                    "status": "passed" if test_run.result.passed else "failed",
                    "duration_ms": test_run.duration_ms,
                    "run_id": str(test_run.id),
                })

                # Save run ID for results view
                self.app.current_run_id = str(test_run.id)

        except Exception as e:
            self._log(f"✗ Error: {e!s}", "step-failed")
            self._update_status("Error during execution", "step-failed")
            self.notify(f"Test error: {e}", severity="error")

        finally:
            self.is_running = False
            self.abort_requested = False
            self.current_task = None
            self.query_one("#btn_run", Button).disabled = False
            self.query_one("#btn_abort", Button).disabled = True

    def _log(self, message: str, style: str | None = None) -> None:
        """
        Append message to log output.

        Args:
            message: Message to log
            style: Optional CSS class for styling
        """
        log_output = self.query_one("#log-output", Static)
        current = str(log_output.renderable)

        text = Text()
        if style:
            text.append(message + "\n", style=style)
        else:
            text.append(message + "\n")

        log_output.update(current + str(text))

        # Auto-scroll to bottom
        scroll = self.query_one("#log-scroll", VerticalScroll)
        scroll.scroll_end()

    def _update_status(self, message: str, style: str | None = None) -> None:
        """
        Update progress status.

        Args:
            message: Status message
            style: Optional CSS class for styling
        """
        status = self.query_one("#progress_status", Static)
        if style:
            status.update(f"[{style}]{message}[/{style}]")
        else:
            status.update(message)

    def action_abort_test(self) -> None:
        """Abort the running test."""
        if not self.is_running:
            self.notify("No test is running", severity="warning")
            return

        from ..widgets.input_modal import InputModal

        def on_confirm(value: str) -> None:
            """Handle abort confirmation."""
            if value.lower() in ["y", "yes"]:
                self.abort_requested = True
                self._log("Abort requested, stopping test...", "step-failed")
                self.notify("Aborting test...", timeout=2)

        # Show confirmation dialog
        self.app.push_screen(
            InputModal(
                title="Abort Test",
                prompt="Are you sure you want to abort the running test? (y/n)",
                placeholder="y/n",
                on_submit=on_confirm,
            )
        )
