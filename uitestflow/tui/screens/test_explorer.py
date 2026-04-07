"""
Test Explorer screen for UITestFlow TUI.

Browse test files, view test definitions, and run tests.
"""

import os
from pathlib import Path

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DirectoryTree, Label, Static


class TestExplorerScreen(Screen):
    """Test explorer screen for browsing test files."""

    BINDINGS = [
        ("r", "run_selected", "Run Test"),
        ("e", "edit_test", "Edit"),
        ("v", "view_test", "View"),
        ("n", "new_test", "New Test"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("q", "app.quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    TestExplorerScreen {
        background: $surface;
    }

    #explorer-container {
        width: 100%;
        height: 100%;
    }

    #tree-panel {
        width: 40%;
        height: 100%;
        border: solid $border;
        background: $panel;
    }

    #preview-panel {
        width: 60%;
        height: 100%;
        border: solid $border;
        background: $panel;
        padding: 1;
    }

    #tree-header {
        background: $primary;
        color: $background;
        padding: 0 1;
        text-style: bold;
    }

    #preview-header {
        background: $primary;
        color: $background;
        padding: 0 1;
        text-style: bold;
        margin-bottom: 1;
    }

    DirectoryTree {
        background: $panel;
    }

    #action-buttons {
        height: auto;
        padding: 1;
        background: $surface;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_test: Path | None = None
        self.test_content: str | None = None

    def compose(self) -> ComposeResult:
        """Compose test explorer layout."""
        with Horizontal(id="explorer-container"):
            # Left panel: Directory tree
            with Vertical(id="tree-panel"):
                yield Label("Test Files", id="tree-header")
                yield DirectoryTree("./", id="test_tree")

            # Right panel: Preview
            with Vertical(id="preview-panel"):
                yield Label("Test Preview", id="preview-header")
                with VerticalScroll(id="preview-content"):
                    yield Static(
                        "Select a test file to preview", id="preview-text", classes="muted"
                    )

        # Action buttons at bottom
        with Horizontal(id="action-buttons"):
            yield Button("Run Test", id="btn_run", variant="primary")
            yield Button("Edit in $EDITOR", id="btn_edit")
            yield Button("New Test", id="btn_new")
            yield Button("Back", id="btn_back")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection in tree."""
        path = event.path

        # Only show YAML test files
        if path.suffix.lower() in [".yaml", ".yml"]:
            self.selected_test = path
            self.app.selected_test_path = path
            self._preview_test(path)

    def _preview_test(self, path: Path) -> None:
        """
        Preview test file content.

        Args:
            path: Path to test file
        """
        try:
            with Path(path).open("r") as f:
                content = f.read()

            # Create syntax highlighted preview
            syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)

            preview = self.query_one("#preview-text", Static)
            preview.update(syntax)

            self.test_content = content

        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_run":
            self.action_run_selected()
        elif button_id == "btn_edit":
            self.action_edit_test()
        elif button_id == "btn_new":
            self.action_new_test()
        elif button_id == "btn_back":
            self.app.pop_screen()

    def action_run_selected(self) -> None:
        """Run the selected test."""
        if not self.selected_test:
            self.notify("No test selected", severity="warning")
            return

        # Navigate to test runner with selected test
        self.app.selected_test_path = self.selected_test
        self.app.action_screen_runner()

    def action_edit_test(self) -> None:
        """Edit test in external editor."""
        if not self.selected_test:
            self.notify("No test selected", severity="warning")
            return

        editor = os.environ.get("EDITOR", "vim")
        self.notify(f"Opening {self.selected_test.name} in {editor}...", timeout=2)

        # Exit TUI temporarily to open editor
        try:
            self.app.suspend()
            os.system(f"{editor} {self.selected_test}")
            self.app.resume()
            self.notify("Returned from editor", timeout=2)

            # Refresh preview
            if self.selected_test:
                self._preview_test(self.selected_test)

        except Exception as e:
            self.notify(f"Error opening editor: {e}", severity="error")

    def action_new_test(self) -> None:
        """Create a new test file."""
        from ..widgets.input_modal import InputModal

        def on_submit(name: str) -> None:
            """Handle test name submission."""
            if not name:
                return

            # Ensure .yaml extension
            if not name.endswith((".yaml", ".yml")):
                name += ".yaml"

            # Create in tests directory
            test_dir = Path("tests")
            test_dir.mkdir(exist_ok=True)

            test_path = test_dir / name

            if test_path.exists():
                self.notify(f"Test {name} already exists", severity="warning")
                return

            # Create template test
            template = """version: "1.0"
name: "New Test"
url: "http://localhost:8018"

steps:
  - name: "Navigate to page"
    action: "goto"
    url: "{{ base_url }}"

evaluators:
  - name: "all_steps_completed"
    type: "all_steps_completed"
"""

            try:
                with Path(test_path).open("w") as f:
                    f.write(template)

                self.notify(f"Created test: {name}", timeout=3)
                self.selected_test = test_path
                self._preview_test(test_path)

            except Exception as e:
                self.notify(f"Error creating test: {e}", severity="error")

        # Show input modal
        self.app.push_screen(
            InputModal(
                title="New Test",
                prompt="Enter test name:",
                on_submit=on_submit,
            )
        )

    def action_cursor_down(self) -> None:
        """Move cursor down in tree."""
        tree = self.query_one(DirectoryTree)
        tree.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in tree."""
        tree = self.query_one(DirectoryTree)
        tree.action_cursor_up()
