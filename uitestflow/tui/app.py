"""
UITestFlow TUI Application - Main Textual application.

This module implements the interactive terminal user interface for UITestFlow
using the Textual framework.
"""

import traceback
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from ..core.profiles import ProfileManager
from .screens.config import ConfigScreen
from .screens.home import HomeScreen
from .screens.profiles import ProfilesScreen
from .screens.results import ResultsScreen
from .screens.test_explorer import TestExplorerScreen
from .screens.test_runner import TestRunnerScreen
from .themes import THEMES, Theme
from .widgets.error_modal import ErrorModal
from .widgets.help_modal import HelpModal


class UITestFlowApp(App):
    """
    UITestFlow TUI Application.

    Main application class with screen management, keyboard bindings,
    and theme support.
    """

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("q", "quit_screen", "Quit/Back", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("/", "search", "Search", show=True),
        Binding("1", "screen_home", "Home", show=False),
        Binding("2", "screen_explorer", "Tests", show=False),
        Binding("3", "screen_runner", "Run", show=False),
        Binding("4", "screen_results", "Results", show=False),
        Binding("5", "screen_profiles", "Profiles", show=False),
        Binding("6", "screen_config", "Config", show=False),
        Binding("h", "screen_home", "Home", show=False),
        Binding("t", "screen_explorer", "Tests", show=False),
        Binding("r", "screen_results", "Results", show=False),
        Binding("p", "screen_profiles", "Profiles", show=False),
        Binding("c", "screen_config", "Config", show=False),
    ]

    SCREENS = {
        "home": HomeScreen,
        "explorer": TestExplorerScreen,
        "runner": TestRunnerScreen,
        "results": ResultsScreen,
        "profiles": ProfilesScreen,
        "config": ConfigScreen,
    }

    TITLE = "UITestFlow"
    SUB_TITLE = "UI Testing Dashboard"

    def __init__(
        self,
        profile: str | None = None,
        results_dir: str | Path = "test_results",
        theme: str = "dark",
        **kwargs,
    ):
        """
        Initialize UITestFlow TUI application.

        Args:
            profile: Profile name to use
            results_dir: Directory for test results
            theme: Theme name (dark, light, high-contrast)
            **kwargs: Additional arguments passed to App
        """
        super().__init__(**kwargs)
        self.profile = profile
        self.results_dir = Path(results_dir)
        self.theme_name = theme
        self.current_theme = THEMES.get(theme, THEMES["dark"])
        self.profile_manager = ProfileManager()

        # Application state
        self.selected_test_path: Path | None = None
        self.current_run_id: str | None = None
        self.test_history: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(show_clock=True)
        yield Footer()

    def on_mount(self) -> None:
        """Initialize application on mount."""
        try:
            # Set theme colors
            self._apply_theme(self.current_theme)

            # Update subtitle with profile
            if self.profile:
                self.sub_title = f"Profile: {self.profile}"

            # Show home screen
            self.push_screen("home")

        except Exception as e:
            error_msg = f"Failed to initialize TUI: {e!s}\n\n{traceback.format_exc()}"
            self.push_screen(ErrorModal(error_msg, title="Initialization Error"))

    def _apply_theme(self, theme: Theme) -> None:
        """
        Apply theme colors to the application.

        Args:
            theme: Theme configuration to apply
        """
        # This would set CSS variables if Textual supported runtime theme changes
        # For now, themes are applied via CSS classes
        self.add_class(f"theme-{self.theme_name}")

    def action_quit_screen(self) -> None:
        """Quit current screen or exit application."""
        try:
            if len(self.screen_stack) > 1:
                self.pop_screen()
            else:
                self.action_quit()
        except Exception as e:
            self._show_error(f"Navigation error: {e}")

    def action_help(self) -> None:
        """Show help modal."""
        try:
            self.push_screen(HelpModal())
        except Exception as e:
            self._show_error(f"Failed to open help: {e}")

    def action_search(self) -> None:
        """Show global search modal."""
        from .widgets.search_modal import SearchModal

        try:
            self.push_screen(SearchModal())
        except Exception as e:
            self._show_error(f"Failed to open search: {e}")

    def action_screen_home(self) -> None:
        """Navigate to home screen."""
        self._safe_push_screen("home")

    def action_screen_explorer(self) -> None:
        """Navigate to test explorer screen."""
        self._safe_push_screen("explorer")

    def action_screen_runner(self) -> None:
        """Navigate to test runner screen."""
        self._safe_push_screen("runner")

    def action_screen_results(self) -> None:
        """Navigate to results screen."""
        self._safe_push_screen("results")

    def action_screen_profiles(self) -> None:
        """Navigate to profiles screen."""
        self._safe_push_screen("profiles")

    def action_screen_config(self) -> None:
        """Navigate to config screen."""
        self._safe_push_screen("config")

    def _safe_push_screen(self, screen_name: str) -> None:
        """
        Safely push a screen with error handling.

        Args:
            screen_name: Name of screen to push
        """
        try:
            self.push_screen(screen_name)
        except Exception as e:
            self._show_error(f"Failed to navigate to {screen_name}: {e}")

    def _show_error(self, message: str) -> None:
        """
        Show error modal.

        Args:
            message: Error message to display
        """
        try:
            self.push_screen(ErrorModal(message))
        except Exception:
            # If we can't even show the error modal, log it
            self.log.error("Fatal error: %s", message)

    def handle_exception(self, exc: Exception) -> None:
        """
        Global exception handler.

        Args:
            exc: Exception that was raised
        """
        error_msg = f"Unexpected error:\n{exc!s}\n\n{traceback.format_exc()}"
        try:
            self.push_screen(ErrorModal(error_msg, title="Unexpected Error"))
        except Exception:
            self.log.error("Fatal error: %s", error_msg)
            self.exit(return_code=1)


def run_tui(
    profile: str | None = None,
    results_dir: str | Path = "test_results",
    theme: str = "dark",
) -> None:
    """
    Run the UITestFlow Terminal User Interface.

    Args:
        profile: Default profile to use in the TUI
        results_dir: Directory for test results
        theme: Theme name (dark, light, high-contrast)

    This function launches an interactive terminal dashboard for managing
    and running UI tests.
    """
    # Load saved configuration
    from .screens.config import ConfigScreen

    saved_config = ConfigScreen.load_app_config()

    # Use command line args if provided, otherwise use saved config
    if profile is None:
        profile = saved_config.get("profile")

    if results_dir == "test_results":  # Default value
        saved_results_dir = saved_config.get("results_dir")
        if saved_results_dir:
            results_dir = saved_results_dir

    if theme == "dark":  # Default value
        saved_theme = saved_config.get("theme")
        if saved_theme:
            theme = saved_theme

    app = UITestFlowApp(profile=profile, results_dir=results_dir, theme=theme)
    app.run()
