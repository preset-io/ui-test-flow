#!/usr/bin/env python3
"""
UITestFlow Server - Entry point for running the FastAPI server standalone.

This module allows running the server directly with:
    python -m uitestflow.server

It supports both development and production modes with configurable settings.
"""

import os
import sys

import uvicorn
from rich.console import Console
from rich.panel import Panel


console = Console()


def main():
    """
    Main entry point for the UITestFlow server.

    Environment Variables:
        UITESTFLOW_HOST: Host to bind to (default: 0.0.0.0)
        UITESTFLOW_PORT: Port to bind to (default: 8018)
        UITESTFLOW_RELOAD: Enable auto-reload (default: false)
        UITESTFLOW_WORKERS: Number of worker processes (default: 1)
        ENVIRONMENT: Set to 'development' for dev mode (default: production)
        LOG_LEVEL: Logging level (default: info)
    """
    # Read configuration from environment
    host = os.getenv("UITESTFLOW_HOST", "0.0.0.0")
    port = int(os.getenv("UITESTFLOW_PORT", "8018"))
    environment = os.getenv("ENVIRONMENT", "production")
    log_level = os.getenv("LOG_LEVEL", "info")

    # Development mode settings
    is_dev = environment.lower() == "development"
    reload = os.getenv("UITESTFLOW_RELOAD", str(is_dev)).lower() in ("true", "1", "yes")
    workers = 1 if reload else int(os.getenv("UITESTFLOW_WORKERS", "1"))

    # Display startup information
    console.print(
        Panel.fit(
            f"[bold cyan]UITestFlow Server[/bold cyan]\n\n"
            f"Environment: {environment}\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"Reload: {'enabled' if reload else 'disabled'}\n"
            f"Workers: {workers}\n"
            f"Log Level: {log_level}",
            border_style="cyan",
            title="Server Configuration",
        )
    )

    console.print("\n[green]Server starting...[/green]")
    console.print(f"Web UI: http://{host}:{port}")
    console.print(f"API Docs: http://{host}:{port}/docs")
    console.print(f"Health Check: http://{host}:{port}/health")
    console.print(f"OpenAPI Spec: http://{host}:{port}/openapi.json\n")

    if reload:
        console.print(
            "[yellow]Development mode:[/yellow] Auto-reload enabled. "
            "Code changes will restart the server automatically.\n"
        )

    console.print("[dim]Press CTRL+C to stop the server[/dim]\n")

    try:
        # Run the server
        uvicorn.run(
            "uitestflow.server.api:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level=log_level.lower(),
            access_log=True,
            # Additional production settings
            proxy_headers=True if not is_dev else False,
            forwarded_allow_ips="*" if not is_dev else None,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error starting server:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
