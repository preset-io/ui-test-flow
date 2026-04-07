"""
Home screen for UITestFlow TUI.

Displays recent test runs, quick actions, and statistics.
"""

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ...core.profiles import ProfileManager


class HomeScreen(Screen):
    """Home screen with dashboard overview."""

    BINDINGS = [
        ("1", "run_test", "Run Test"),
        ("2", "explorer", "Explore Tests"),
        ("3", "results", "View Results"),
        ("4", "profiles", "Profiles"),
        ("5", "config", "Config"),
        ("r", "refresh", "Refresh"),
        ("q", "app.quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    HomeScreen {
        background: $surface;
    }

    #home-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    .section {
        border: solid $border;
        background: $panel;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .quick-action {
        width: 100%;
        margin: 0 0 1 0;
    }

    .stat-container {
        height: auto;
        padding: 1;
    }

    .stat-value {
        text-style: bold;
        color: $accent;
        font-size: 2;
    }

    .stat-label {
        color: $text-muted;
    }

    .recent-run {
        padding: 0 1;
        margin: 0 0 1 0;
    }

    .run-passed {
        color: $success;
    }

    .run-failed {
        color: $error;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose home screen layout."""
        with VerticalScroll(id="home-container"):
            # Welcome header
            yield Label("Welcome to UITestFlow", classes="section-title")
            yield Label(
                "Interactive UI Testing Dashboard - Press ? for help",
                classes="muted",
            )
            yield Label("")

            # Stats section
            with Container(classes="section"):
                yield Label("Statistics", classes="section-title")
                with Horizontal():
                    yield from self._compose_stats()

            # Quick Actions
            with Container(classes="section"):
                yield Label("Quick Actions", classes="section-title")
                with Vertical():
                    yield Button("Run Test", id="btn_run", classes="quick-action")
                    yield Button("Browse Tests", id="btn_explorer", classes="quick-action")
                    yield Button("View Results", id="btn_results", classes="quick-action")
                    yield Button("Manage Profiles", id="btn_profiles", classes="quick-action")
                    yield Button("Configuration", id="btn_config", classes="quick-action")

            # Recent runs
            with Container(classes="section"):
                yield Label("Recent Test Runs", classes="section-title")
                yield from self._compose_recent_runs()

    def _compose_stats(self) -> ComposeResult:
        """Compose statistics section."""
        # Get test statistics
        test_count = self._count_tests()
        profile_count = self._count_profiles()
        recent_runs = len(self.app.test_history)

        # Display stats
        with Container(classes="stat-container"):
            yield Label(str(test_count), classes="stat-value")
            yield Label("Tests", classes="stat-label")

        with Container(classes="stat-container"):
            yield Label(str(profile_count), classes="stat-value")
            yield Label("Profiles", classes="stat-label")

        with Container(classes="stat-container"):
            yield Label(str(recent_runs), classes="stat-value")
            yield Label("Recent Runs", classes="stat-label")

    def _compose_recent_runs(self) -> ComposeResult:
        """Compose recent test runs section."""
        if not self.app.test_history:
            yield Label("  No recent test runs", classes="muted")
            return

        # Show last 5 runs
        for run in self.app.test_history[-5:]:
            status = run.get("status", "unknown")
            name = run.get("name", "Unknown Test")
            duration = run.get("duration_ms", 0)

            run_text = Text()
            if status == "passed":
                run_text.append("  ✓ ", style="green")
            elif status == "failed":
                run_text.append("  ✗ ", style="red")
            else:
                run_text.append("  • ", style="yellow")

            run_text.append(f"{name} ", style="white")
            run_text.append(f"({duration}ms)", style="dim")

            yield Static(run_text, classes="recent-run")

    def _count_tests(self) -> int:
        """Count number of test files."""
        # Look for test files in common locations
        test_dirs = [Path("tests"), Path("test"), Path()]
        count = 0

        for test_dir in test_dirs:
            if test_dir.exists():
                count += len(list(test_dir.glob("**/*.yaml")))
                count += len(list(test_dir.glob("**/*.yml")))

        return count

    def _count_profiles(self) -> int:
        """Count number of configured profiles."""
        try:
            pm = ProfileManager()
            return len(pm.list_profiles())
        except Exception:
            return 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_run":
            self.action_run_test()
        elif button_id == "btn_explorer":
            self.action_explorer()
        elif button_id == "btn_results":
            self.action_results()
        elif button_id == "btn_profiles":
            self.app.action_screen_profiles()
        elif button_id == "btn_config":
            self.app.action_screen_config()

    def action_run_test(self) -> None:
        """Navigate to test runner."""
        self.app.action_screen_runner()

    def action_explorer(self) -> None:
        """Navigate to test explorer."""
        self.app.action_screen_explorer()

    def action_results(self) -> None:
        """Navigate to results screen."""
        self.app.action_screen_results()

    def action_refresh(self) -> None:
        """Refresh the home screen."""
        self.notify("Refreshing...", timeout=2)
        self.refresh()
