"""
Help modal widget for displaying keyboard shortcuts and help.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown


HELP_MARKDOWN = """
# UITestFlow Keyboard Shortcuts

Press `?` anywhere to show this help guide.

## Global Navigation

| Key | Action |
|-----|--------|
| `h` or `1` | Home screen |
| `t` or `2` | Test Explorer |
| `3` | Test Runner |
| `r` or `4` | Results viewer |
| `p` or `5` | Profiles |
| `c` or `6` | Configuration |
| `?` | Show this help |
| `/` | Global search |
| `q` | Back/Quit screen |
| `Ctrl+C` | Quit application |

## Test Explorer

| Key | Action |
|-----|--------|
| `↑↓` / `j k` | Navigate files |
| `Enter` | Select test file |
| `r` | Run selected test |
| `e` | Edit in $EDITOR |
| `v` | View test content |
| `n` | Create new test |

## Test Runner

| Key | Action |
|-----|--------|
| `r` | Run test |
| `s` | Stop test |
| `Enter` | Start execution |

## Results Viewer

| Key | Action |
|-----|--------|
| `↑↓` / `j k` | Navigate results |
| `v` | View details |
| `d` | Delete run |
| `r` | Refresh |

## Profiles

| Key | Action |
|-----|--------|
| `t` | Test connection |
| `r` | Refresh |

## Configuration

| Key | Action |
|-----|--------|
| `s` | Save config |
| `Tab` | Next field |
| `Shift+Tab` | Previous field |

## Tips & Tricks

### Vim Keybindings
- Use `j/k` for up/down navigation in lists
- Press `q` to go back or quit screens
- `/` for search anywhere

### Quick Actions
- Number keys `1-6` work on any screen for navigation
- `Enter` to execute or confirm
- `Esc` to cancel or close modals

---

**UITestFlow** - UI Testing Dashboard
"""


class HelpModal(ModalScreen):
    """Modal screen showing keyboard shortcuts and help."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("q", "dismiss", "Close", priority=True),
        Binding("?", "dismiss", "Close", priority=True),
    ]

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    #help-dialog {
        width: 90;
        max-width: 100;
        height: 90%;
        max-height: 100;
        border: thick $primary;
        background: $surface;
    }

    #help-header {
        background: $primary;
        color: $background;
        padding: 1;
        text-style: bold;
        text-align: center;
    }

    #help-content {
        height: 100%;
        padding: 1;
    }

    #help-footer {
        padding: 1;
        height: auto;
        background: $surface;
        align: center middle;
    }

    HelpModal Markdown {
        height: auto;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose help modal layout."""
        with Vertical(id="help-dialog"):
            yield Label("Keyboard Shortcuts & Help", id="help-header")

            with VerticalScroll(id="help-content"):
                yield Markdown(HELP_MARKDOWN)

            with Horizontal(id="help-footer"):
                yield Button("Close [Esc]", variant="primary", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close_btn":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
