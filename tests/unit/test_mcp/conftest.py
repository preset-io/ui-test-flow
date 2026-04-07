"""Conftest for MCP unit tests to fix import issues."""

import sys
from pathlib import Path


# Ensure the project root is in sys.path (not the tests/unit/mcp directory)
# This prevents pytest from shadowing the external 'mcp' package
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
