"""
Main FastAPI application for UITestFlow server.

Provides REST API for test management, execution, and monitoring with
WebSocket support for real-time updates.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import close_db, init_db
from .middleware import RateLimitMiddleware, RequestTrackingMiddleware, configure_logging
from .routes import analytics, auth, profiles, runs, tests
from .schemas import ErrorResponse, HealthResponse
from .websocket import websocket_endpoint


# Application version
VERSION = "0.1.0"


async def cleanup_dead_sessions_periodically():
    """Periodically cleanup dead browser sessions."""
    from .routes.profiles import _executor

    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            count = await _executor.browser_manager.cleanup_dead_sessions()
            if count > 0:
                print(f"Cleaned up {count} dead browser sessions")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in periodic session cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    # Startup
    print("Starting UITestFlow server...")

    # Configure structured logging
    configure_logging()

    # Initialize database
    try:
        await init_db()
        print("Database initialized")
    except Exception as e:
        print(f"WARNING: Database connection failed: {e}")
        print("Server will start but database features will be unavailable.")
        print("To fix: Start PostgreSQL with 'docker-compose up postgres' or 'make docker-up'")

    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(cleanup_dead_sessions_periodically())

    yield

    # Shutdown
    print("Shutting down UITestFlow server...")

    # Cancel periodic cleanup
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # Close all browser sessions
    try:
        from .routes.profiles import _executor

        await _executor.browser_manager.cleanup_all_sessions()
        print("All browser sessions closed")
    except Exception as e:
        print(f"WARNING: Error closing browser sessions: {e}")

    # Close database
    try:
        await close_db()
        print("Database connections closed")
    except Exception as e:
        print(f"WARNING: Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title="UITestFlow API",
    description="Enterprise-grade UI testing platform with natural language support",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ============================================================================
# Middleware Configuration
# ============================================================================

# Request tracking (must be first to track all requests)
app.add_middleware(RequestTrackingMiddleware)

# Rate limiting (before CORS to reject early)
app.add_middleware(RateLimitMiddleware)

# MCP-specific middleware
from .mcp_middleware import MCPLoggingMiddleware, MCPResponseMiddleware, MCPValidationMiddleware


app.add_middleware(MCPResponseMiddleware)
app.add_middleware(MCPLoggingMiddleware)
app.add_middleware(MCPValidationMiddleware)

# Configure CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # Local testing
        "http://localhost:8018",  # Alternative port
        # Add production origins here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Not Found",
            detail="The requested resource was not found",
            code="NOT_FOUND",
        ).model_dump()
        | {"request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 Internal Server errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            code="INTERNAL_ERROR",
        ).model_dump()
        | {"request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


# ============================================================================
# API Routes
# ============================================================================

# Include routers
app.include_router(auth.router)
app.include_router(tests.router)
app.include_router(runs.router)
app.include_router(profiles.router)
app.include_router(analytics.router)

# Include MCP router
from .mcp_routes import router as mcp_router


app.include_router(mcp_router)


# ============================================================================
# WebSocket Endpoints
# ============================================================================


@app.websocket("/ws/runs/{run_id}")
async def websocket_runs(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for real-time test run updates.

    Args:
        websocket: WebSocket connection
        run_id: Test run ID to subscribe to

    Example client code:
        const ws = new WebSocket('ws://localhost:8000/ws/runs/123e4567-e89b-12d3-a456-426614174000');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Update:', data);
        };
    """
    from uuid import UUID

    try:
        run_uuid = UUID(run_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid run ID format")
        return

    await websocket_endpoint(websocket, run_uuid)


# ============================================================================
# Health and Status Endpoints
# ============================================================================


@app.get("/api", include_in_schema=False)
async def api_root():
    """API root endpoint."""
    return {
        "message": "UITestFlow API",
        "version": VERSION,
        "docs": "/api/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status including database connectivity
    """
    # Check database connectivity
    from sqlalchemy import text

    from .database import engine

    db_status = "unknown"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e!s}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=VERSION,
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@app.get("/api/version", tags=["info"])
async def get_version():
    """
    Get API version information.

    Returns:
        Version information
    """
    return {
        "version": VERSION,
        "name": "UITestFlow API",
        "description": "Enterprise-grade UI testing platform",
    }


# ============================================================================
# Static Files and React UI
# ============================================================================

# Get the path to the React build directory
UI_BUILD_DIR = Path(__file__).parent.parent / "ui" / "dist"

# Mount static assets
if UI_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(UI_BUILD_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        """
        Serve React app for all non-API routes.

        This allows React Router to handle client-side routing.
        """
        # Don't interfere with API routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return JSONResponse(
                status_code=404,
                content={"error": "Not Found", "detail": f"Endpoint /{full_path} not found"},
            )

        # Check if the requested file exists
        file_path = UI_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise, serve index.html (for client-side routing)
        index_file = UI_BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "detail": "UI not built. Run 'npm run build' in uitestflow/ui/",
            },
        )

else:

    @app.get("/", include_in_schema=False)
    async def no_ui_message():
        """Message when UI is not built."""
        return {
            "message": "UITestFlow API",
            "version": VERSION,
            "docs": "/api/docs",
            "note": "React UI not built. Run 'cd uitestflow/ui && npm install && npm run build' to build the UI.",
        }


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """
    Run the FastAPI application.

    This is the main entry point for running the server.
    """
    import uvicorn

    uvicorn.run(
        "uitestflow.server.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
