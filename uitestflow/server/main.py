"""
Compatibility module - redirects to api.py.

This file exists for backwards compatibility with code that imports
from uitestflow.server.main. The actual FastAPI application is in api.py.
"""

from uitestflow.server.api import VERSION, app


__all__ = ["VERSION", "app"]
