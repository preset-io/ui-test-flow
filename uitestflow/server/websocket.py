"""
WebSocket support for real-time test execution updates.

Provides connection management and broadcasting capabilities for test progress.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from .schemas import TestProgressUpdate, WebSocketMessage


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports multiple clients connected to the same test run and broadcasting
    updates to all connected clients.
    """

    def __init__(self):
        """Initialize connection manager."""
        # Map of run_id to list of active connections
        self.active_connections: dict[UUID, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, run_id: UUID):
        """
        Accept a WebSocket connection and register it for a test run.

        Args:
            websocket: WebSocket connection
            run_id: Test run ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if run_id not in self.active_connections:
                self.active_connections[run_id] = []
            self.active_connections[run_id].append(websocket)

        logger.info(
            f"WebSocket connected for run {run_id}. Total connections: {len(self.active_connections[run_id])}"
        )

    async def disconnect(self, websocket: WebSocket, run_id: UUID):
        """
        Disconnect a WebSocket and remove it from the registry.

        Args:
            websocket: WebSocket connection
            run_id: Test run ID
        """
        async with self._lock:
            if run_id in self.active_connections:
                if websocket in self.active_connections[run_id]:
                    self.active_connections[run_id].remove(websocket)

                # Clean up empty lists
                if not self.active_connections[run_id]:
                    del self.active_connections[run_id]

        logger.info("WebSocket disconnected for run %s", run_id)

    async def send_message(self, run_id: UUID, message: dict[str, Any]):
        """
        Send a message to all clients connected to a test run.

        Args:
            run_id: Test run ID
            message: Message data to send
        """
        async with self._lock:
            connections = self.active_connections.get(run_id, [])

        if not connections:
            logger.debug("No active connections for run %s", run_id)
            return

        # Create WebSocket message
        ws_message = WebSocketMessage(
            type=message.get("type", "update"),
            data=message,
            timestamp=datetime.utcnow(),
        )

        # Send to all connected clients
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(ws_message.model_dump(mode="json"))
            except Exception as e:
                logger.error("Error sending message to WebSocket: %s", e)
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                if run_id in self.active_connections:
                    for conn in disconnected:
                        if conn in self.active_connections[run_id]:
                            self.active_connections[run_id].remove(conn)
                    if not self.active_connections[run_id]:
                        del self.active_connections[run_id]

    async def broadcast_status(self, run_id: UUID, status: str, message: str | None = None):
        """
        Broadcast a status update to all connected clients.

        Args:
            run_id: Test run ID
            status: Status string (e.g., "running", "completed", "failed")
            message: Optional message
        """
        await self.send_message(
            run_id,
            {
                "type": "status",
                "run_id": str(run_id),
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_progress(self, run_id: UUID, progress: TestProgressUpdate):
        """
        Broadcast a progress update to all connected clients.

        Args:
            run_id: Test run ID
            progress: Progress update data
        """
        await self.send_message(
            run_id,
            {
                "type": "progress",
                "run_id": str(run_id),
                "status": progress.status,
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "step_name": progress.step_name,
                "message": progress.message,
                "screenshot_url": progress.screenshot_url,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_log(self, run_id: UUID, level: str, message: str):
        """
        Broadcast a log message to all connected clients.

        Args:
            run_id: Test run ID
            level: Log level (info, warning, error)
            message: Log message
        """
        await self.send_message(
            run_id,
            {
                "type": "log",
                "run_id": str(run_id),
                "level": level,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_screenshot(self, run_id: UUID, screenshot_url: str, step_name: str):
        """
        Broadcast a screenshot update to all connected clients.

        Args:
            run_id: Test run ID
            screenshot_url: URL of the screenshot
            step_name: Name of the step
        """
        await self.send_message(
            run_id,
            {
                "type": "screenshot",
                "run_id": str(run_id),
                "screenshot_url": screenshot_url,
                "step_name": step_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_complete(self, run_id: UUID, result: dict):
        """
        Broadcast test completion to all connected clients.

        Args:
            run_id: Test run ID
            result: Test result data
        """
        await self.send_message(
            run_id,
            {
                "type": "complete",
                "run_id": str(run_id),
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_error(self, run_id: UUID, error: str):
        """
        Broadcast an error to all connected clients.

        Args:
            run_id: Test run ID
            error: Error message
        """
        await self.send_message(
            run_id,
            {
                "type": "error",
                "run_id": str(run_id),
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def get_connection_count(self, run_id: UUID | None = None) -> int:
        """
        Get the number of active connections.

        Args:
            run_id: Optional run ID to get count for specific run

        Returns:
            Number of active connections
        """
        if run_id:
            return len(self.active_connections.get(run_id, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, run_id: UUID):
    """
    WebSocket endpoint for test run updates.

    Args:
        websocket: WebSocket connection
        run_id: Test run ID to subscribe to

    Example:
        @app.websocket("/ws/runs/{run_id}")
        async def websocket_runs(websocket: WebSocket, run_id: UUID):
            await websocket_endpoint(websocket, run_id)
    """
    await manager.connect(websocket, run_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "run_id": str(run_id),
            "message": "Connected to test run updates",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive messages from client (e.g., heartbeat, commands)
                data = await websocket.receive_json()

                # Handle client messages if needed
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Error in WebSocket receive loop: %s", e)
                break

    finally:
        await manager.disconnect(websocket, run_id)
