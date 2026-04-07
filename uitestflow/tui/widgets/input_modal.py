"""
Input modal widget for prompting user input.
"""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class InputModal(ModalScreen):
    """Modal screen for prompting user input."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    DEFAULT_CSS = """
    InputModal {
        align: center middle;
    }

    #input-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $panel;
    }

    #input-header {
        background: $primary;
        color: $background;
        padding: 1;
        text-style: bold;
        text-align: center;
    }

    #input-content {
        padding: 2;
        height: auto;
    }

    #input-prompt {
        margin-bottom: 1;
    }

    #input-field {
        width: 100%;
    }

    #input-footer {
        padding: 1;
        height: auto;
        align: center middle;
        background: $surface;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str,
        prompt: str,
        placeholder: str = "",
        on_submit: Callable[[str], None] | None = None,
    ):
        """
        Initialize input modal.

        Args:
            title: Modal title
            prompt: Prompt text
            placeholder: Input placeholder text
            on_submit: Callback function called with input value on submit
        """
        super().__init__()
        self.title = title
        self.prompt = prompt
        self.placeholder = placeholder
        self.on_submit_callback = on_submit

    def compose(self) -> ComposeResult:
        """Compose input modal layout."""
        with Vertical(id="input-dialog"):
            yield Label(self.title, id="input-header")

            with Vertical(id="input-content"):
                yield Static(self.prompt, id="input-prompt")
                yield Input(
                    placeholder=self.placeholder,
                    id="input-field",
                )

            with Horizontal(id="input-footer"):
                yield Button("Submit", variant="success", id="submit_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self) -> None:
        """Focus input field on mount."""
        self.query_one("#input-field", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "submit_btn":
            self._submit()
        elif event.button.id == "cancel_btn":
            self.dismiss()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        self._submit()

    def _submit(self) -> None:
        """Submit input value."""
        input_field = self.query_one("#input-field", Input)
        value = input_field.value.strip()

        if self.on_submit_callback:
            self.on_submit_callback(value)

        self.dismiss(value)

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
