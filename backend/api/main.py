"""Main FastAPI application for Emperor AI Assistant."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings, get_logger
from .types import EventType, BaseEvent, ErrorCode
from .websocket import manager
from claude_code_bridge import (
    get_bridge,
    BridgeError,
    CLINotInstalledError,
    AuthenticationError,
)

logger = get_logger(__name__)


# =============================================================================
# Message Queue System
# =============================================================================


@dataclass
class QueuedMessage:
    """A message waiting to be processed."""

    websocket: WebSocket
    data: dict[str, Any]


class MessageProcessor:
    """
    Processes messages in order using a queue and lock.

    Ensures messages are handled one at a time in FIFO order,
    preventing race conditions and lost messages.
    """

    def __init__(self):
        self.queues: dict[WebSocket, asyncio.Queue[QueuedMessage]] = {}
        self.locks: dict[WebSocket, asyncio.Lock] = {}
        self.processors: dict[WebSocket, asyncio.Task] = {}

    def _get_queue(self, websocket: WebSocket) -> asyncio.Queue[QueuedMessage]:
        """Get or create queue for a websocket connection."""
        if websocket not in self.queues:
            self.queues[websocket] = asyncio.Queue()
        return self.queues[websocket]

    def _get_lock(self, websocket: WebSocket) -> asyncio.Lock:
        """Get or create lock for a websocket connection."""
        if websocket not in self.locks:
            self.locks[websocket] = asyncio.Lock()
        return self.locks[websocket]

    async def enqueue(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """
        Add a message to the queue for processing.

        Args:
            websocket: The client's WebSocket connection
            data: The message data to process
        """
        queue = self._get_queue(websocket)
        message = QueuedMessage(websocket=websocket, data=data)
        await queue.put(message)

        logger.debug(f"Message queued. Queue size: {queue.qsize()}")

        # Start processor if not running
        if websocket not in self.processors or self.processors[websocket].done():
            self.processors[websocket] = asyncio.create_task(
                self._process_queue(websocket)
            )

    async def _process_queue(self, websocket: WebSocket) -> None:
        """
        Process messages from the queue one at a time.

        Args:
            websocket: The client's WebSocket connection
        """
        queue = self._get_queue(websocket)
        lock = self._get_lock(websocket)

        while not queue.empty():
            message = await queue.get()

            try:
                async with lock:  # One message at a time
                    logger.debug(f"Processing message. Remaining: {queue.qsize()}")
                    await route_message(message.websocket, message.data)

            except asyncio.TimeoutError:
                logger.error("Message processing timed out")
                await send_error(
                    message.websocket,
                    ErrorCode.TIMEOUT,
                    "Request timed out. Please try again.",
                    recoverable=True,
                )

            except Exception as e:
                logger.error(f"Error processing queued message: {e}", exc_info=True)
                await send_error(
                    message.websocket,
                    ErrorCode.PROCESSING_ERROR,
                    "Failed to process your request",
                    recoverable=True,
                )

            finally:
                queue.task_done()

    def cleanup(self, websocket: WebSocket) -> None:
        """
        Clean up resources for a disconnected client.

        Args:
            websocket: The disconnected WebSocket connection
        """
        # Cancel processor task if running
        if websocket in self.processors:
            task = self.processors[websocket]
            if not task.done():
                task.cancel()
            del self.processors[websocket]

        # Remove queue and lock
        if websocket in self.queues:
            del self.queues[websocket]
        if websocket in self.locks:
            del self.locks[websocket]

        logger.debug("Cleaned up message processor for disconnected client")

    @property
    def total_queued(self) -> int:
        """Return total number of messages queued across all connections."""
        return sum(q.qsize() for q in self.queues.values())


# Singleton instance
message_processor = MessageProcessor()


# =============================================================================
# Error Handling Helpers
# =============================================================================


async def send_error(
    websocket: WebSocket,
    code: ErrorCode,
    message: str,
    recoverable: bool = True,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Send an error event to the client.

    Args:
        websocket: The client's WebSocket connection
        code: Error code from ErrorCode enum
        message: Human-readable error message
        recoverable: Whether the client can continue after this error
        details: Optional additional error details
    """
    try:
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.ERROR,
                payload={
                    "code": code.value if isinstance(code, ErrorCode) else code,
                    "message": message,
                    "recoverable": recoverable,
                    "details": details,
                },
            ),
        )
    except Exception as e:
        logger.error(f"Failed to send error to client: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Server running on {settings.host}:{settings.port}")
    logger.info(f"Debug mode: {settings.debug}")

    # Verify Claude Code Bridge
    try:
        bridge = get_bridge()
        await bridge.verify()
        logger.info("Claude Code Bridge initialized successfully")
    except CLINotInstalledError as e:
        logger.warning(f"Claude Code CLI not available: {e}")
        logger.warning("Running in limited mode (echo responses only)")
    except AuthenticationError as e:
        logger.warning(f"Claude Code authentication issue: {e}")
        logger.warning("Running in limited mode (echo responses only)")
    except BridgeError as e:
        logger.warning(f"Claude Code Bridge error: {e}")
        logger.warning("Running in limited mode (echo responses only)")

    yield

    # Shutdown
    logger.info("Shutting down server...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow all origins in dev mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    bridge = get_bridge()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "connections": manager.connection_count,
        "queued_messages": message_processor.total_queued,
        "claude_bridge": bridge.status,
    }


async def send_streaming_response(
    websocket: WebSocket,
    message_id: str,
    full_text: str,
    chunk_size: int = 5,
    delay: float = 0.05,
) -> None:
    """
    Send a response as streaming chunks.

    Args:
        websocket: The client's WebSocket connection
        message_id: Unique ID for this message
        full_text: The complete response text
        chunk_size: Number of words per chunk
        delay: Delay between chunks in seconds
    """
    words = full_text.split()
    chunks = []

    # Build cumulative chunks
    for i in range(0, len(words), chunk_size):
        chunk_words = words[: i + chunk_size]
        chunks.append(" ".join(chunk_words))

    # Send each chunk
    for i, chunk_content in enumerate(chunks):
        is_last = i == len(chunks) - 1

        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.ASSISTANT_MESSAGE,
                payload={
                    "message_id": message_id,
                    "content": chunk_content,
                    "is_streaming": not is_last,
                    "is_complete": is_last,
                },
            ),
        )

        if not is_last:
            await asyncio.sleep(delay)


async def handle_user_message(websocket: WebSocket, payload: dict) -> None:
    """
    Handle incoming user messages.

    Args:
        websocket: The client's WebSocket connection
        payload: The message payload containing content
    """
    from uuid import uuid4

    content = payload.get("content", "")

    # Validate content
    if not content or not content.strip():
        await send_error(
            websocket,
            ErrorCode.INVALID_FIELD,
            "Message content cannot be empty",
        )
        return

    logger.debug(f"Received message: {content[:50]}...")

    # Generate message ID for the response
    message_id = str(uuid4())

    try:
        # Send typing indicator
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.ASSISTANT_TYPING,
                payload={"is_typing": True},
            ),
        )

        # Small delay before starting response
        await asyncio.sleep(0.3)

        # Placeholder echo response (Claude Code Bridge integration later)
        response_content = f"You said: {content}. This is a streaming response from Emperor AI Assistant. Each word appears progressively to demonstrate the streaming capability."

        # Send streaming response
        await send_streaming_response(
            websocket,
            message_id,
            response_content,
            chunk_size=3,  # Words per chunk
            delay=0.08,    # Delay between chunks
        )

    except asyncio.TimeoutError:
        logger.error("Timeout while generating response")
        await send_error(
            websocket,
            ErrorCode.TIMEOUT,
            "Response generation timed out. Please try again.",
        )

    except Exception as e:
        logger.error(f"Error handling user message: {e}", exc_info=True)
        await send_error(
            websocket,
            ErrorCode.PROCESSING_ERROR,
            "Failed to generate response. Please try again.",
        )

    finally:
        # Always clear typing indicator
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.ASSISTANT_TYPING,
                payload={"is_typing": False},
            ),
        )


async def handle_heartbeat(websocket: WebSocket, payload: dict) -> None:
    """
    Handle heartbeat messages (ping/pong).

    Args:
        websocket: The client's WebSocket connection
        payload: The heartbeat payload
    """
    status = payload.get("status", "")

    if status == "pong":
        # Client responding to our ping
        manager.record_pong(websocket)
    else:
        # Client initiated ping, respond with pong
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.HEARTBEAT,
                payload={"status": "pong"},
            ),
        )


async def route_message(websocket: WebSocket, data: dict) -> None:
    """
    Route incoming messages to appropriate handlers.

    Args:
        websocket: The client's WebSocket connection
        data: The parsed message data
    """
    event_type = data.get("event_type", "")
    payload = data.get("payload", {})

    match event_type:
        case "user.message":
            await handle_user_message(websocket, payload)
        case "heartbeat":
            await handle_heartbeat(websocket, payload)
        case _:
            logger.warning(f"Unknown event type: {event_type}")
            await send_error(
                websocket,
                ErrorCode.UNKNOWN_EVENT,
                f"Unknown event type: {event_type}",
            )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for client communication.

    Handles connection lifecycle and message routing.
    Messages are queued and processed in order.
    Includes comprehensive error handling for graceful recovery.
    """
    await manager.connect(websocket)

    try:
        while True:
            try:
                # Receive raw message
                raw_data = await websocket.receive_text()

                # Parse JSON
                try:
                    import json
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {e}")
                    await send_error(
                        websocket,
                        ErrorCode.INVALID_JSON,
                        "Message must be valid JSON",
                        details={"position": e.pos},
                    )
                    continue  # Keep connection alive

                # Validate required fields
                if not isinstance(data, dict):
                    await send_error(
                        websocket,
                        ErrorCode.MALFORMED_MESSAGE,
                        "Message must be a JSON object",
                    )
                    continue

                if "event_type" not in data:
                    await send_error(
                        websocket,
                        ErrorCode.MISSING_FIELD,
                        "Missing required field: event_type",
                    )
                    continue

                logger.debug(f"Received: {data}")

                # Add to queue for processing (non-blocking)
                await message_processor.enqueue(websocket, data)

            except WebSocketDisconnect:
                raise  # Re-raise to outer handler

            except Exception as e:
                # Log full error for debugging
                logger.error(f"Error processing message: {e}", exc_info=True)

                # Send sanitized error to client
                await send_error(
                    websocket,
                    ErrorCode.INTERNAL_ERROR,
                    "An unexpected error occurred",
                    recoverable=True,
                )
                # Keep connection alive, continue processing

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message_processor.cleanup(websocket)
        logger.info("Client disconnected normally")

    except Exception as e:
        logger.error(f"Fatal WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
        message_processor.cleanup(websocket)


def start_server():
    """Start the uvicorn server."""
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    start_server()
