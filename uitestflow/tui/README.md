# UITestFlow TUI - Terminal User Interface

Interactive terminal dashboard for managing and running UI tests using Textual.

## Features

### Screens

1. **Home Screen** (`screens/home.py`)
   - Dashboard overview with statistics
   - Quick actions menu
   - Recent test runs
   - Keyboard shortcuts: `1-5` for quick actions, `r` to refresh

2. **Test Explorer** (`screens/test_explorer.py`)
   - Browse test files in directory tree
   - Preview YAML test content with syntax highlighting
   - Run selected tests
   - Edit tests in $EDITOR
   - Create new tests from templates
   - Keyboard shortcuts: `r` run, `e` edit, `v` view, `n` new, `j/k` navigate

3. **Test Runner** (`screens/test_runner.py`)
   - Real-time test execution
   - Live progress tracking
   - Step-by-step output logging
   - Test results display
   - Keyboard shortcuts: `r` run, `s` stop

4. **Results Viewer** (`screens/results.py`)
   - Test run history table
   - Detailed run information
   - Filterable results
   - Keyboard shortcuts: `v` view details, `d` delete, `r` refresh, `j/k` navigate

5. **Profile Manager** (`screens/profiles.py`)
   - View configured profiles
   - Profile details (URL, browser, auth)
   - Test connectivity
   - Keyboard shortcuts: `t` test connection, `r` refresh

6. **Configuration** (`screens/config.py`)
   - Edit settings and preferences
   - Theme selection (dark, light, high-contrast)
   - Browser defaults
   - Keyboard shortcuts: `s` save

### Widgets

1. **Error Modal** (`widgets/error_modal.py`)
   - Display error messages
   - Stack trace viewing
   - Close with Esc/Enter/q

2. **Help Modal** (`widgets/help_modal.py`)
   - Comprehensive keyboard shortcuts
   - Context-sensitive help
   - Press `?` anywhere

3. **Search Modal** (`widgets/search_modal.py`)
   - Global search across tests, profiles, results
   - Fuzzy matching
   - Press `/` anywhere

4. **Input Modal** (`widgets/input_modal.py`)
   - Prompt for user input
   - Used for new test creation
   - Submit with Enter

### Theme Support

Three built-in themes (`themes.py`):

- **Dark** (default): Cyan accents on dark background
- **Light**: Blue accents on light background
- **High Contrast**: Yellow/cyan for accessibility

## Keyboard Shortcuts

### Global Navigation

- `h` or `1`: Home screen
- `t` or `2`: Test Explorer
- `3`: Test Runner
- `r` or `4`: Results viewer
- `p` or `5`: Profiles
- `c` or `6`: Configuration
- `?`: Help modal
- `/`: Search modal
- `q`: Back/Quit screen
- `Ctrl+C`: Quit application

### Vim-style Navigation

- `j`: Move down
- `k`: Move up
- `h`: Go to home

## Usage

```python
from uitestflow.tui import run_tui

# Run with defaults
run_tui()

# Run with specific profile and theme
run_tui(profile="staging", theme="light", results_dir="test_results")
```

From CLI:

```bash
uitestflow tui
uitestflow tui --profile staging --theme light
```

## Architecture

```
uitestflow/tui/
├── __init__.py           # Package exports
├── app.py                # Main TUI application (UITestFlowApp)
├── styles.tcss           # Global CSS styles
├── themes.py             # Theme configurations
├── screens/              # Screen implementations
│   ├── __init__.py
│   ├── home.py           # Dashboard home screen
│   ├── test_explorer.py  # Test file browser
│   ├── test_runner.py    # Test execution screen
│   ├── results.py        # Results viewer
│   ├── profiles.py       # Profile management
│   └── config.py         # Configuration editor
└── widgets/              # Reusable widgets
    ├── __init__.py
    ├── error_modal.py    # Error display modal
    ├── help_modal.py     # Help/shortcuts modal
    ├── search_modal.py   # Global search
    └── input_modal.py    # Input prompt modal
```

## Integration

The TUI integrates with existing UITestFlow components:

- **Test Runner** (`uitestflow.src.test_runner.TestRunner`): Executes tests asynchronously
- **Test Parser** (`uitestflow.src.test_parser.YAMLTestParser`): Parses YAML test files
- **Profile Manager** (`uitestflow.core.profiles.ProfileManager`): Manages test profiles
- **Browser Manager** (`uitestflow.src.browser_manager.BrowserSessionManager`): Manages Playwright sessions

## Dependencies

- `textual`: TUI framework
- `rich`: Terminal formatting and syntax highlighting
- Existing UITestFlow core components

## Future Enhancements

- [ ] Screenshot preview (ASCII art or kitty protocol)
- [ ] Real-time log streaming during test execution
- [ ] Test result filtering and search
- [ ] Profile connectivity testing
- [ ] Configuration persistence
- [ ] Test editing in TUI (not just external editor)
- [ ] Test run comparison
- [ ] Notification support
- [ ] Auto-refresh mode
- [ ] Test templates library

## Development

The TUI follows testmcpy patterns but adapts them for UI testing:

- Similar screen/widget structure
- Error handling with modals
- Vim-style keybindings
- Beautiful Rich formatting
- Async test execution support

## Notes

- The TUI requires a terminal with 256-color support
- Recommended terminal size: 80x24 minimum, 120x40+ optimal
- All file paths are absolute for clarity
- Theme changes require TUI restart (limitation of Textual CSS)
