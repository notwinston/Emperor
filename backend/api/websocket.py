"""WebSocket connection manager for Emperor AI Assistant."""

import asyncio
from datetime import datetime, timezone

from fastapi import WebSocket

from config import get_logger
from .types import BaseEvent, EventType

logger = get_logger(__name__)


# Heartbeat configuration
HEARTBEAT_INTERVAL = 30  # seconds between heartbeats
HEARTBEAT_TIMEOUT = 10   # seconds to wait for pong
STALE_THRESHOLD = 60     # seconds before connection considered stale


class ConnectionManager:
    """Manages active WebSocket connections with heartbeat monitoring."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: list[WebSocket] = []
        self.last_pong: dict[WebSocket, datetime] = {}
        self.heartbeat_tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.last_pong[websocket] = datetime.now(timezone.utc)

        # Start heartbeat task for this connection
        self.heartbeat_tasks[websocket] = asyncio.create_task(
            self._heartbeat_loop(websocket)
        )

        logger.info(
            f"Client connected. Active connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the active list.

        Args:
            websocket: The WebSocket connection to remove
        """
        # Cancel heartbeat task
        if websocket in self.heartbeat_tasks:
            task = self.heartbeat_tasks[websocket]
            if not task.done():
                task.cancel()
            del self.heartbeat_tasks[websocket]

        # Remove pong tracking
        if websocket in self.last_pong:
            del self.last_pong[websocket]

        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        logger.info(
            f"Client disconnected. Active connections: {len(self.active_connections)}"
        )

    def record_pong(self, websocket: WebSocket) -> None:
        """
        Record that a pong was received from a client.

        Args:
            websocket: The WebSocket connection that sent the pong
        """
        self.last_pong[websocket] = datetime.now(timezone.utc)
        logger.debug("Heartbeat pong received")

    def is_stale(self, websocket: WebSocket) -> bool:
        """
        Check if a connection is stale (no recent pong).

        Args:
            websocket: The WebSocket connection to check

        Returns:
            True if connection is stale, False otherwise
        """
        last = self.last_pong.get(websocket)
        if not last:
            return True

        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        return elapsed > STALE_THRESHOLD

    async def _heartbeat_loop(self, websocket: WebSocket) -> None:
        """
        Send periodic heartbeats to detect dead connections.

        Args:
            websocket: The WebSocket connection to monitor
        """
        try:
            while websocket in self.active_connections:
                await asyncio.sleep(HEARTBEAT_INTERVAL)

                # Check if connection is stale
                if self.is_stale(websocket):
                    logger.warning("Connection stale, no heartbeat response")
                    await self._close_stale_connection(websocket)
                    break

                # Send heartbeat
                try:
                    await self.send(
                        websocket,
                        BaseEvent(
                            event_type=EventType.HEARTBEAT,
                            payload={"status": "ping"},
                        ),
                    )
                    logger.debug("Heartbeat ping sent")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    break

        except asyncio.CancelledError:
            # Task was cancelled (client disconnected normally)
            pass
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")

    async def _close_stale_connection(self, websocket: WebSocket) -> None:
        """
        Close a stale connection.

        Args:
            websocket: The stale WebSocket connection
        """
        try:
            await websocket.close(code=1000, reason="Heartbeat timeout")
        except Exception:
            pass  # Connection might already be closed
        finally:
            self.disconnect(websocket)

    async def send(self, websocket: WebSocket, event: BaseEvent) -> None:
        """
        Send an event to a specific WebSocket connection.

        Args:
            websocket: The target WebSocket connection
            event: The event to send
        """
        try:
            await websocket.send_json(event.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, event: BaseEvent) -> None:
        """
        Send an event to all active WebSocket connections.

        Args:
            event: The event to broadcast
        """
        disconnected: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(event.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)

        # Clean up failed connections
        for connection in disconnected:
            self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        """Return the number of active connections."""
        return len(self.active_connections)


# Singleton instance
manager = ConnectionManager()
