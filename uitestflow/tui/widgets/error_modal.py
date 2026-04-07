"""
Error modal widget for displaying error messages.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ErrorModal(ModalScreen):
    """Modal screen for displaying error messages."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("enter", "dismiss", "Close", priority=True),
        Binding("q", "dismiss", "Close", priority=True),
    ]

    DEFAULT_CSS = """
    ErrorModal {
        align: center middle;
    }

    #error-dialog {
        width: 80;
        max-width: 100;
        height: auto;
        max-height: 80%;
        border: thick $error;
        background: $panel;
    }

    #error-header {
        background: $error;
        color: $background;
        padding: 1;
        text-style: bold;
        text-align: center;
    }

    #error-content {
        padding: 2;
        height: auto;
        max-height: 50;
    }

    #error-message {
        width: 100%;
        height: auto;
    }

    #error-footer {
        padding: 1;
        height: auto;
        align: center middle;
        background: $surface;
    }
    """

    def __init__(self, error_message: str, title: str = "Error"):
        """
        Initialize error modal.

        Args:
            error_message: Error message to display
            title: Modal title
        """
        super().__init__()
        self.error_message = error_message
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose error modal layout."""
        with Vertical(id="error-dialog"):
            yield Label(self.title, id="error-header")

            with VerticalScroll(id="error-content"):
                yield Static(self.error_message, id="error-message")

            with Horizontal(id="error-footer"):
                yield Button("Close [Esc]", variant="error", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close_btn":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
