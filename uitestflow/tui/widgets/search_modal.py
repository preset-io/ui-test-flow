"""
Search modal widget for global search functionality.
"""

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from ...core.profiles import ProfileManager
from ...src.test_parser import YAMLTestParser


class SearchModal(ModalScreen):
    """Modal screen for global search."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("ctrl+c", "dismiss", "Close", priority=True),
    ]

    DEFAULT_CSS = """
    SearchModal {
        align: center middle;
    }

    #search-dialog {
        width: 80;
        max-width: 100;
        height: 60%;
        border: thick $primary;
        background: $panel;
    }

    #search-header {
        background: $primary;
        color: $background;
        padding: 1;
        text-style: bold;
    }

    #search-input {
        margin: 1;
    }

    #search-results {
        height: 1fr;
        padding: 1;
    }

    #search-footer {
        padding: 1;
        height: auto;
        background: $surface;
    }

    ListView {
        height: 100%;
    }
    """

    def __init__(self):
        """Initialize search modal."""
        super().__init__()
        self.search_results: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose search modal layout."""
        with Vertical(id="search-dialog"):
            yield Label("Search Tests, Profiles, and Results", id="search-header")

            yield Input(
                placeholder="Type to search...",
                id="search-input",
            )

            with Container(id="search-results"):
                yield ListView(id="results_list")

            with Horizontal(id="search-footer"):
                yield Static("Press Enter to select, Esc to cancel", classes="muted")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self) -> None:
        """Focus search input on mount."""
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        query = event.value.strip()

        if not query:
            self._clear_results()
            return

        # Perform search
        self._perform_search(query)

    def _perform_search(self, query: str) -> None:
        """
        Perform search across tests, profiles, and results.

        Args:
            query: Search query string
        """
        results = []
        query_lower = query.lower()

        # Search test files
        try:
            test_dir = Path("tests")
            if test_dir.exists():
                for test_file in test_dir.rglob("*.yaml"):
                    try:
                        # Search by filename
                        if query_lower in test_file.name.lower():
                            results.append({
                                "type": "test",
                                "name": test_file.stem,
                                "path": str(test_file),
                                "match": "filename",
                            })
                            continue

                        # Parse and search test content
                        parser = YAMLTestParser()
                        test_def = parser.parse_file(test_file)

                        # Search by test name
                        if query_lower in test_def.name.lower():
                            results.append({
                                "type": "test",
                                "name": test_def.name,
                                "path": str(test_file),
                                "match": "name",
                            })
                            continue

                        # Search by description
                        if test_def.description and query_lower in test_def.description.lower():
                            results.append({
                                "type": "test",
                                "name": test_def.name,
                                "path": str(test_file),
                                "match": "description",
                            })
                            continue

                        # Search by tags
                        if test_def.tags:
                            for tag in test_def.tags:
                                if query_lower in tag.lower():
                                    results.append({
                                        "type": "test",
                                        "name": test_def.name,
                                        "path": str(test_file),
                                        "match": f"tag:{tag}",
                                    })
                                    break

                    except Exception:
                        # Skip files that can't be parsed
                        pass
        except Exception:
            pass

        # Search profiles
        try:
            pm = ProfileManager()
            for profile_id in pm.list_profiles():
                profile = pm.get_profile(profile_id)

                # Search by profile ID or name
                if query_lower in profile_id.lower() or query_lower in profile.name.lower():
                    results.append({
                        "type": "profile",
                        "name": profile.name,
                        "path": profile.base_url,
                        "match": profile_id,
                    })
                    continue

                # Search by URL
                if query_lower in profile.base_url.lower():
                    results.append({
                        "type": "profile",
                        "name": profile.name,
                        "path": profile.base_url,
                        "match": "url",
                    })
        except Exception:
            pass

        # Search test history
        try:
            for run in self.app.test_history:
                name = run.get("name", "")
                if query_lower in name.lower():
                    status = run.get("status", "unknown")
                    run_id = run.get("run_id", "N/A")[:8]
                    results.append({
                        "type": "result",
                        "name": name,
                        "path": f"{status} - {run_id}",
                        "match": "test_name",
                    })
        except Exception:
            pass

        self.search_results = results
        self._display_results()

    def _display_results(self) -> None:
        """Display search results in list."""
        list_view = self.query_one("#results_list", ListView)
        list_view.clear()

        if not self.search_results:
            list_view.append(ListItem(Label("No results found", classes="muted")))
            return

        for idx, result in enumerate(self.search_results):
            item_type = result.get("type", "unknown")
            name = result.get("name", "Unknown")
            path = result.get("path", "")
            match = result.get("match", "")

            # Create rich text with highlighting
            text = Text()

            # Type badge with color
            if item_type == "test":
                text.append("[TEST] ", style="bold cyan")
            elif item_type == "profile":
                text.append("[PROFILE] ", style="bold magenta")
            elif item_type == "result":
                text.append("[RESULT] ", style="bold yellow")
            else:
                text.append(f"[{item_type.upper()}] ", style="bold")

            # Name (highlighted if it matches)
            query = self.query_one("#search-input", Input).value.lower()
            if query in name.lower():
                # Simple highlight by making it bold
                text.append(name, style="bold green")
            else:
                text.append(name, style="")

            text.append("\n  ")
            text.append(path, style="dim")

            if match:
                text.append(f" ({match})", style="italic dim")

            item = ListItem(Static(text))
            item.data = result  # Store result data
            list_view.append(item)

    def _clear_results(self) -> None:
        """Clear search results."""
        self.search_results = []
        list_view = self.query_one("#results_list", ListView)
        list_view.clear()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if hasattr(event.item, "data") and event.item.data:
            result = event.item.data
            self._handle_selection(result)

    def _handle_selection(self, result: dict) -> None:
        """
        Handle selection of a search result.

        Args:
            result: Selected search result dictionary
        """
        result_type = result.get("type")

        if result_type == "test":
            # Navigate to test runner with selected test
            path = Path(result.get("path", ""))
            if path.exists():
                self.app.selected_test_path = path
                self.dismiss()
                self.app.action_screen_runner()
            else:
                self.app.notify("Test file not found", severity="error")

        elif result_type == "profile":
            # Navigate to profiles screen
            self.dismiss()
            self.app.action_screen_profiles()

        elif result_type == "result":
            # Navigate to results screen
            self.dismiss()
            self.app.action_screen_results()

        else:
            self.app.notify("Unknown result type", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel_btn":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
