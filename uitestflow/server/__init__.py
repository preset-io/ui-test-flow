"""
FastAPI backend server for UITestFlow.

This package contains the REST API server implementation including:
- API endpoints (auth, profiles, tests, runs, analytics)
- Database models and ORM setup
- WebSocket handlers for real-time updates
- Authentication and authorization
- Background task execution

Main components:
- api.py: FastAPI application with all routes
- database.py: SQLAlchemy models and session management
- auth.py: JWT authentication and authorization
- websocket.py: WebSocket connection management
- schemas.py: Pydantic models for request/response validation
- routes/: API route handlers by resource type
"""

from .api import app
from .database import close_db, get_db, init_db
from .mcp_middleware import MCPLoggingMiddleware, MCPResponseMiddleware, MCPValidationMiddleware
from .mcp_routes import router as mcp_router
from .websocket import manager


__all__ = [
    "MCPLoggingMiddleware",
    "MCPResponseMiddleware",
    "MCPValidationMiddleware",
    "app",
    "close_db",
    "get_db",
    "init_db",
    "manager",
    "mcp_router",
]
