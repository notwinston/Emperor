"""API type definitions for WebSocket communication."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be sent over WebSocket."""

    USER_MESSAGE = "user.message"
    ASSISTANT_MESSAGE = "assistant.message"
    ASSISTANT_TYPING = "assistant.typing"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class BaseEvent(BaseModel):
    """Base event structure for all WebSocket messages."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    source: str = "backend"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)


class MessagePayload(BaseModel):
    """Payload structure for message events."""

    content: str
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    is_streaming: bool = False
    is_complete: bool = True


class ErrorCode(str, Enum):
    """Standard error codes for WebSocket communication."""

    # Parse errors
    INVALID_JSON = "INVALID_JSON"
    MALFORMED_MESSAGE = "MALFORMED_MESSAGE"

    # Validation errors
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FIELD = "INVALID_FIELD"
    UNKNOWN_EVENT = "UNKNOWN_EVENT"

    # Processing errors
    PROCESSING_ERROR = "PROCESSING_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorPayload(BaseModel):
    """Payload structure for error events."""

    code: str
    message: str
    recoverable: bool = True
    details: dict[str, Any] | None = None
