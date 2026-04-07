"""
Theme configuration for UITestFlow TUI.

Defines color schemes and styling for different themes.
"""

from dataclasses import dataclass


@dataclass
class Theme:
    """Theme configuration with color definitions."""

    name: str
    description: str

    # Base colors
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    panel: str

    # Text colors
    text: str
    text_muted: str
    text_disabled: str

    # Status colors
    success: str
    warning: str
    error: str
    info: str

    # UI element colors
    border: str
    border_focused: str
    selection: str
    hover: str


# Dark theme (default)
DARK_THEME = Theme(
    name="dark",
    description="Dark mode with cyan accents",
    primary="#00D9FF",  # Cyan
    secondary="#00A3CC",  # Darker cyan
    accent="#FF00FF",  # Magenta
    background="#0C0C0C",  # Near black
    surface="#1A1A1A",  # Dark gray
    panel="#262626",  # Light gray
    text="#FFFFFF",  # White
    text_muted="#808080",  # Gray
    text_disabled="#404040",  # Dark gray
    success="#00FF00",  # Green
    warning="#FFAA00",  # Orange
    error="#FF0000",  # Red
    info="#00D9FF",  # Cyan
    border="#404040",  # Dark gray
    border_focused="#00D9FF",  # Cyan
    selection="#00A3CC",  # Darker cyan
    hover="#333333",  # Dark gray
)

# Light theme
LIGHT_THEME = Theme(
    name="light",
    description="Light mode for bright environments",
    primary="#0066CC",  # Blue
    secondary="#0052A3",  # Darker blue
    accent="#CC00CC",  # Purple
    background="#FFFFFF",  # White
    surface="#F5F5F5",  # Light gray
    panel="#E8E8E8",  # Gray
    text="#000000",  # Black
    text_muted="#666666",  # Gray
    text_disabled="#CCCCCC",  # Light gray
    success="#00AA00",  # Green
    warning="#CC8800",  # Orange
    error="#CC0000",  # Red
    info="#0066CC",  # Blue
    border="#CCCCCC",  # Light gray
    border_focused="#0066CC",  # Blue
    selection="#B3D9FF",  # Light blue
    hover="#DDDDDD",  # Light gray
)

# High contrast theme
HIGH_CONTRAST_THEME = Theme(
    name="high-contrast",
    description="High contrast for accessibility",
    primary="#FFFF00",  # Yellow
    secondary="#FFCC00",  # Orange-yellow
    accent="#00FFFF",  # Cyan
    background="#000000",  # Black
    surface="#1A1A1A",  # Very dark gray
    panel="#333333",  # Dark gray
    text="#FFFFFF",  # White
    text_muted="#AAAAAA",  # Light gray
    text_disabled="#555555",  # Medium gray
    success="#00FF00",  # Bright green
    warning="#FFAA00",  # Bright orange
    error="#FF0000",  # Bright red
    info="#00FFFF",  # Bright cyan
    border="#FFFFFF",  # White
    border_focused="#FFFF00",  # Yellow
    selection="#FFFF00",  # Yellow
    hover="#555555",  # Medium gray
)

# Theme registry
THEMES: dict[str, Theme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "high-contrast": HIGH_CONTRAST_THEME,
}


def get_theme(name: str) -> Theme:
    """
    Get theme by name.

    Args:
        name: Theme name

    Returns:
        Theme configuration

    Raises:
        ValueError: If theme not found
    """
    theme = THEMES.get(name)
    if not theme:
        raise ValueError(f"Unknown theme: {name}. Available: {list(THEMES.keys())}")
    return theme


def list_themes() -> list[str]:
    """
    Get list of available theme names.

    Returns:
        List of theme names
    """
    return list(THEMES.keys())
