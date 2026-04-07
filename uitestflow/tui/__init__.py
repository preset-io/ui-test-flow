"""
UITestFlow TUI (Terminal User Interface) - Interactive terminal dashboard.

This package provides a rich terminal-based interface using Textual for
managing and running UI tests interactively.
"""

from .app import UITestFlowApp, run_tui


__all__ = ["UITestFlowApp", "run_tui"]
