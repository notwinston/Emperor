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
from orchestrator import get_orchestrator, DelegationType
from process_manager import (
    init_event_bus,
    shutdown_event_bus,
    init_ui_streamer,
    shutdown_ui_streamer,
    get_event_bus,
    Event,
    EventType as PMEventType,
    Priority,
)
from voice import get_voice_handler

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


async def broadcast_to_frontend(event_data: dict) -> None:
    """
    Broadcast an event to all connected frontend clients.

    This function is passed to the UIEventStreamer to enable
    forwarding of internal events to the WebSocket connections.

    Args:
        event_data: The event data to broadcast
    """
    # Convert to BaseEvent format expected by WebSocket manager
    event = BaseEvent(
        event_type=event_data.get("event_type", "unknown"),
        payload=event_data.get("payload", {}),
    )
    await manager.broadcast(event)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Server running on {settings.host}:{settings.port}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize Event Bus
    try:
        event_bus = await init_event_bus()
        logger.info("Event Bus initialized successfully")

        # Initialize UI Event Streamer
        await init_ui_streamer(
            event_bus=event_bus,
            broadcast_func=broadcast_to_frontend,
            rate_limit_ms=100,
        )
        logger.info("UI Event Streamer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Event Bus: {e}")
        raise

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

    # Shutdown UI Streamer first (it depends on Event Bus)
    await shutdown_ui_streamer()
    logger.info("UI Event Streamer stopped")

    # Shutdown Event Bus
    await shutdown_event_bus()
    logger.info("Event Bus stopped")


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
    event_bus = get_event_bus()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "connections": manager.connection_count,
        "queued_messages": message_processor.total_queued,
        "claude_bridge": bridge.status,
        "event_bus": {
            "running": event_bus.is_running,
            "subscriptions": event_bus.subscription_count,
            "queue_size": event_bus.queue_size,
            "stats": event_bus.stats,
        },
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

    Routes messages through the Orchestrator which uses Claude Code CLI
    for intent classification and response generation.

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

        # Get orchestrator and check bridge status
        orchestrator = get_orchestrator()
        bridge = get_bridge()

        # Check if bridge is verified (Claude Code CLI available)
        if bridge.is_verified:
            # Use real AI via Claude Code CLI
            logger.debug("Processing via Claude Code Bridge...")

            # Stream response from orchestrator
            accumulated_response = ""
            is_first_chunk = True

            async for chunk in orchestrator.process_stream(content):
                accumulated_response += chunk

                # Send streaming update
                await manager.send(
                    websocket,
                    BaseEvent(
                        event_type=EventType.ASSISTANT_MESSAGE,
                        payload={
                            "message_id": message_id,
                            "content": accumulated_response,
                            "is_streaming": True,
                            "is_complete": False,
                        },
                    ),
                )

                is_first_chunk = False

            # Send final complete message
            await manager.send(
                websocket,
                BaseEvent(
                    event_type=EventType.ASSISTANT_MESSAGE,
                    payload={
                        "message_id": message_id,
                        "content": accumulated_response,
                        "is_streaming": False,
                        "is_complete": True,
                    },
                ),
            )

            # Check for delegation (for future Domain Lead integration)
            result = orchestrator._parse_response(accumulated_response)
            if result.delegation != DelegationType.NONE:
                logger.info(
                    f"Delegation detected: {result.delegation.value} - {result.delegation_task}"
                )
                # TODO: When Domain Leads are implemented (Part 10),
                # call orchestrator.delegate_to_lead() here

        else:
            # Fallback: Bridge not available, use echo mode
            logger.warning("Claude Code Bridge not verified, using fallback echo mode")

            response_content = (
                f"[Echo Mode - Claude Code CLI not available]\n\n"
                f"You said: {content}\n\n"
                f"To enable AI responses, ensure Claude Code CLI is installed and authenticated:\n"
                f"1. Install: npm install -g @anthropic-ai/claude-code\n"
                f"2. Login: claude auth login"
            )

            # Send as streaming response for consistent UX
            await send_streaming_response(
                websocket,
                message_id,
                response_content,
                chunk_size=5,
                delay=0.05,
            )

    except asyncio.TimeoutError:
        logger.error("Timeout while generating response")
        await send_error(
            websocket,
            ErrorCode.TIMEOUT,
            "Response generation timed out. Please try again.",
        )

    except BridgeError as e:
        logger.error(f"Bridge error: {e}")
        await send_error(
            websocket,
            ErrorCode.PROCESSING_ERROR,
            f"AI service error: {e}",
            recoverable=True,
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


async def handle_approval_response(websocket: WebSocket, payload: dict) -> None:
    """
    Handle approval response from the user.

    Publishes the approval response to the Event Bus so the waiting
    agent can proceed or handle denial.

    Args:
        websocket: The client's WebSocket connection
        payload: The approval response payload
    """
    from datetime import datetime, timezone

    request_id = payload.get("request_id")
    approved = payload.get("approved", False)
    reason = payload.get("reason")

    if not request_id:
        await send_error(
            websocket,
            ErrorCode.MISSING_FIELD,
            "Missing required field: request_id",
        )
        return

    # Determine event type based on approval status
    event_type = PMEventType.APPROVAL_GRANTED if approved else PMEventType.APPROVAL_DENIED

    # Create and publish the approval response event
    event = Event(
        type=event_type,
        source="user",
        data={
            "request_id": request_id,
            "approved": approved,
            "reason": reason,
            "responded_at": datetime.now(timezone.utc).isoformat(),
        },
        correlation_id=request_id,  # Use request_id as correlation
        priority=Priority.HIGH,
    )

    # Publish to Event Bus
    event_bus = get_event_bus()
    await event_bus.publish(event)

    logger.info(f"Approval response published: {request_id} - {'approved' if approved else 'denied'}")


async def handle_voice_audio(websocket: WebSocket, payload: dict) -> None:
    """
    Handle incoming voice audio from frontend.

    Transcribes audio using local Whisper (FREE) and optionally
    processes the transcribed text as a user message.

    Args:
        websocket: The client's WebSocket connection
        payload: Contains base64 audio and format
    """
    audio_b64 = payload.get("audio", "")
    audio_format = payload.get("format", "webm")

    if not audio_b64:
        await send_error(
            websocket,
            ErrorCode.MISSING_FIELD,
            "Missing required field: audio",
        )
        return

    try:
        # Get voice handler (lazy-loads Whisper model on first use)
        handler = get_voice_handler()

        # Decode base64 audio
        audio_bytes = handler.decode_audio(audio_b64)
        logger.info(f"Received audio: {len(audio_bytes)} bytes ({audio_format})")

        # Transcribe with local Whisper (FREE, runs in thread pool)
        text = await handler.transcribe(audio_bytes)

        # Send transcription back to frontend
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.VOICE_TRANSCRIPTION,
                payload={
                    "text": text,
                },
            ),
        )

        logger.info(f"Transcribed: {text[:100]}...")

        # Process as regular user message if there's content
        if text.strip():
            await handle_user_message(websocket, {"content": text})

    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.VOICE_ERROR,
                payload={
                    "error": str(e),
                    "stage": "transcription",
                    "recoverable": True,
                },
            ),
        )


async def handle_voice_tts(websocket: WebSocket, payload: dict) -> None:
    """
    Handle TTS request from frontend.

    Synthesizes text to audio using Edge TTS (FREE) and streams
    audio chunks back to the client.

    Args:
        websocket: The client's WebSocket connection
        payload: Contains text to synthesize
    """
    text = payload.get("text", "")

    if not text.strip():
        await send_error(
            websocket,
            ErrorCode.INVALID_FIELD,
            "Text cannot be empty",
        )
        return

    try:
        handler = get_voice_handler()

        logger.info(f"Synthesizing TTS: {len(text)} chars")

        # Stream audio chunks back to frontend
        async for chunk in handler.synthesize_stream(text):
            await manager.send(
                websocket,
                BaseEvent(
                    event_type=EventType.VOICE_AUDIO_CHUNK,
                    payload={
                        "audio": handler.encode_audio(chunk),
                        "format": "mp3",
                    },
                ),
            )

        # Signal completion
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.VOICE_AUDIO_COMPLETE,
                payload={},
            ),
        )

        logger.info("TTS streaming complete")

    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        await manager.send(
            websocket,
            BaseEvent(
                event_type=EventType.VOICE_ERROR,
                payload={
                    "error": str(e),
                    "stage": "synthesis",
                    "recoverable": True,
                },
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
        case "approval.response":
            await handle_approval_response(websocket, payload)
        case "voice.audio":
            await handle_voice_audio(websocket, payload)
        case "voice.tts":
            await handle_voice_tts(websocket, payload)
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
