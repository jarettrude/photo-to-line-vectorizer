"""
WebSocket support for real-time progress updates.

Provides WebSocket endpoint for clients to receive live progress
updates during image processing.
"""

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time progress updates.

    Allows multiple clients to subscribe to progress updates for specific jobs.
    Supports broadcasting progress to all connected clients for a job.
    """

    def __init__(self):
        """Initialize connection manager with empty connection registry."""
        # Map job_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        """
        Accept WebSocket connection and register for job updates.

        Args:
            websocket: WebSocket connection to accept
            job_id: Job ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = []
            self.active_connections[job_id].append(websocket)

        logger.info(f"WebSocket connected for job {job_id}. Total: {len(self.active_connections[job_id])}")

    async def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """
        Remove WebSocket connection from registry.

        Args:
            websocket: WebSocket connection to remove
            job_id: Job ID to unsubscribe from
        """
        async with self._lock:
            if job_id in self.active_connections:
                if websocket in self.active_connections[job_id]:
                    self.active_connections[job_id].remove(websocket)

                # Clean up empty job lists
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

        logger.info(f"WebSocket disconnected for job {job_id}")

    async def broadcast_progress(
        self,
        job_id: str,
        progress: int,
        stage: str | None = None,
        message: str | None = None,
    ) -> None:
        """
        Broadcast progress update to all clients subscribed to a job.

        Args:
            job_id: Job ID to broadcast to
            progress: Progress percentage (0-100)
            stage: Current processing stage (e.g., "preprocessing", "vectorizing")
            message: Optional status message
        """
        data = {
            "type": "progress",
            "job_id": job_id,
            "progress": progress,
        }

        if stage:
            data["stage"] = stage

        if message:
            data["message"] = message

        message_json = json.dumps(data)

        async with self._lock:
            if job_id not in self.active_connections:
                return

            # Send to all connections for this job
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(connection)

            # Clean up failed connections
            for connection in disconnected:
                if connection in self.active_connections[job_id]:
                    self.active_connections[job_id].remove(connection)

            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast_complete(
        self,
        job_id: str,
        result_url: str,
        stats: dict | None = None,
    ) -> None:
        """
        Broadcast completion message to all clients.

        Args:
            job_id: Job ID to broadcast to
            result_url: URL to download result
            stats: Optional processing statistics
        """
        data = {
            "type": "complete",
            "job_id": job_id,
            "progress": 100,
            "result_url": result_url,
        }

        if stats:
            data["stats"] = stats

        message_json = json.dumps(data)

        async with self._lock:
            if job_id not in self.active_connections:
                return

            for connection in list(self.active_connections[job_id]):
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send completion: {e}")

    async def broadcast_error(
        self,
        job_id: str,
        error: str,
    ) -> None:
        """
        Broadcast error message to all clients.

        Args:
            job_id: Job ID to broadcast to
            error: Error message
        """
        data = {
            "type": "error",
            "job_id": job_id,
            "error": error,
        }

        message_json = json.dumps(data)

        async with self._lock:
            if job_id not in self.active_connections:
                return

            for connection in list(self.active_connections[job_id]):
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send error: {e}")


# Global connection manager instance
ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, job_id: str) -> None:
    """
    WebSocket endpoint for real-time progress updates.

    Clients connect to /ws/status/{job_id} to receive progress updates
    as the job processes.

    Message format:
    {
        "type": "progress" | "complete" | "error",
        "job_id": str,
        "progress": int,  // 0-100
        "stage": str,     // optional: current processing stage
        "message": str,   // optional: status message
        "result_url": str,  // only for "complete" type
        "stats": {...},     // only for "complete" type
        "error": str,     // only for "error" type
    }

    Args:
        websocket: WebSocket connection
        job_id: Job ID to subscribe to
    """
    await ws_manager.connect(websocket, job_id)

    try:
        # Keep connection alive and handle ping/pong
        while True:
            # Wait for client messages (pings)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send keepalive ping from server
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception:
                    # Connection dead
                    break

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from job {job_id}")
    except Exception as e:
        logger.exception(f"WebSocket error for job {job_id}: {e}")
    finally:
        await ws_manager.disconnect(websocket, job_id)
