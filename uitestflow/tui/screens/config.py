"""
Configuration screen for UITestFlow TUI.

Edit settings and preferences.
"""

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Switch


class ConfigScreen(Screen):
    """Configuration editor screen."""

    BINDINGS = [
        ("s", "save", "Save"),
        ("q", "app.quit_screen", "Back"),
    ]

    CONFIG_DIR = Path.home() / ".uitestflow"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CSS = """
    ConfigScreen {
        background: $surface;
    }

    #config-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    .config-section {
        border: solid $border;
        background: $panel;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .config-item {
        margin: 1 0;
        height: auto;
    }

    .config-label {
        color: $text;
        margin-bottom: 0;
    }

    Input {
        margin-bottom: 1;
    }

    #controls {
        height: auto;
        padding: 1;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose config layout."""
        with VerticalScroll(id="config-container"):
            yield Label("Configuration", classes="panel-title")
            yield Label("Manage UITestFlow settings", classes="muted")
            yield Label("")

            # General settings
            with Container(classes="config-section"):
                yield Label("General Settings", classes="section-title")

                with Container(classes="config-item"):
                    yield Label("Default Profile:", classes="config-label")
                    yield Input(placeholder="default", id="input_profile")

                with Container(classes="config-item"):
                    yield Label("Results Directory:", classes="config-label")
                    yield Input(placeholder="test_results", id="input_results_dir")

            # Display settings
            with Container(classes="config-section"):
                yield Label("Display Settings", classes="section-title")

                with Container(classes="config-item"):
                    yield Label("Theme:", classes="config-label")
                    yield Select(
                        [
                            ("Dark", "dark"),
                            ("Light", "light"),
                            ("High Contrast", "high-contrast"),
                        ],
                        id="select_theme",
                    )

                with Container(classes="config-item"):
                    yield Label("Auto-refresh:", classes="config-label")
                    yield Switch(value=False, id="switch_autorefresh")

            # Browser settings
            with Container(classes="config-section"):
                yield Label("Browser Settings", classes="section-title")

                with Container(classes="config-item"):
                    yield Label("Default Browser:", classes="config-label")
                    yield Select(
                        [
                            ("Chromium", "chromium"),
                            ("Firefox", "firefox"),
                            ("WebKit", "webkit"),
                        ],
                        id="select_browser",
                    )

                with Container(classes="config-item"):
                    yield Label("Headless Mode:", classes="config-label")
                    yield Switch(value=True, id="switch_headless")

        # Controls
        with Horizontal(id="controls"):
            yield Button("Save", id="btn_save", variant="success")
            yield Button("Reset", id="btn_reset", variant="warning")
            yield Button("Back", id="btn_back")

    def on_mount(self) -> None:
        """Load saved configuration on mount."""
        self._load_config()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_save":
            self.action_save()
        elif button_id == "btn_reset":
            self._reset_config()
        elif button_id == "btn_back":
            self.app.pop_screen()

    def action_save(self) -> None:
        """Save configuration."""
        try:
            # Get values from inputs
            config = {
                "profile": self.query_one("#input_profile", Input).value,
                "results_dir": self.query_one("#input_results_dir", Input).value,
                "theme": self.query_one("#select_theme", Select).value,
                "auto_refresh": self.query_one("#switch_autorefresh", Switch).value,
                "browser": self.query_one("#select_browser", Select).value,
                "headless": self.query_one("#switch_headless", Switch).value,
            }

            # Create config directory if it doesn't exist
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Save to JSON file
            with Path(self.CONFIG_FILE).open("w") as f:
                json.dump(config, f, indent=2)

            # Update app settings
            if config.get("profile"):
                self.app.profile = config["profile"]
            if config.get("results_dir"):
                self.app.results_dir = Path(config["results_dir"])
            if config.get("theme"):
                self.app.theme_name = config["theme"]

            self.notify("Configuration saved successfully", timeout=2, severity="information")

        except Exception as e:
            self.notify(f"Error saving configuration: {e}", timeout=3, severity="error")

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if not self.CONFIG_FILE.exists():
                # Use app defaults
                self._load_from_app()
                return

            with Path(self.CONFIG_FILE).open("r") as f:
                config = json.load(f)

            # Populate inputs with saved values
            if "profile" in config:
                self.query_one("#input_profile", Input).value = config["profile"]
            if "results_dir" in config:
                self.query_one("#input_results_dir", Input).value = config["results_dir"]
            if "theme" in config:
                self.query_one("#select_theme", Select).value = config["theme"]
            if "auto_refresh" in config:
                self.query_one("#switch_autorefresh", Switch).value = config["auto_refresh"]
            if "browser" in config:
                self.query_one("#select_browser", Select).value = config["browser"]
            if "headless" in config:
                self.query_one("#switch_headless", Switch).value = config["headless"]

        except Exception as e:
            self.notify(f"Error loading configuration: {e}", timeout=3, severity="warning")
            self._load_from_app()

    def _load_from_app(self) -> None:
        """Load configuration from app state."""
        try:
            if self.app.profile:
                self.query_one("#input_profile", Input).value = self.app.profile
            if self.app.results_dir:
                self.query_one("#input_results_dir", Input).value = str(self.app.results_dir)
            if self.app.theme_name:
                self.query_one("#select_theme", Select).value = self.app.theme_name
        except Exception:
            pass

    def _reset_config(self) -> None:
        """Reset configuration to defaults."""
        try:
            # Reset to defaults
            self.query_one("#input_profile", Input).value = ""
            self.query_one("#input_results_dir", Input).value = "test_results"
            self.query_one("#select_theme", Select).value = "dark"
            self.query_one("#switch_autorefresh", Switch).value = False
            self.query_one("#select_browser", Select).value = "chromium"
            self.query_one("#switch_headless", Switch).value = True

            # Delete config file if it exists
            if self.CONFIG_FILE.exists():
                self.CONFIG_FILE.unlink()

            self.notify("Configuration reset to defaults", timeout=2, severity="information")

        except Exception as e:
            self.notify(f"Error resetting configuration: {e}", timeout=3, severity="error")

    @staticmethod
    def load_app_config() -> dict:
        """
        Load configuration from file for app initialization.

        Returns:
            Configuration dictionary with defaults if file doesn't exist
        """
        config_file = Path.home() / ".uitestflow" / "config.json"

        try:
            if config_file.exists():
                with Path(config_file).open("r") as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            "profile": None,
            "results_dir": "test_results",
            "theme": "dark",
            "auto_refresh": False,
            "browser": "chromium",
            "headless": True,
        }
