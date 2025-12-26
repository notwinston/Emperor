"""API type definitions for WebSocket communication."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be sent over WebSocket."""

    # Core message events
    USER_MESSAGE = "user.message"
    ASSISTANT_MESSAGE = "assistant.message"
    ASSISTANT_TYPING = "assistant.typing"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

    # Agent status events
    AGENT_STATUS = "agent.status"

    # Lead events
    LEAD_RECEIVED = "lead.received"
    LEAD_PLANNING = "lead.planning"
    LEAD_PROGRESS = "lead.progress"
    LEAD_COMPLETE = "lead.complete"
    LEAD_ERROR = "lead.error"

    # Worker events
    WORKER_START = "worker.start"
    WORKER_PROGRESS = "worker.progress"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"

    # Tool events
    TOOL_EXECUTE = "tool.execute"
    TOOL_PROGRESS = "tool.progress"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # Approval events
    APPROVAL_REQUEST = "approval.request"
    APPROVAL_RESPONSE = "approval.response"
    APPROVAL_TIMEOUT = "approval.timeout"

    # System events
    SYSTEM_ERROR = "system.error"


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


class AgentStatusPayload(BaseModel):
    """Payload for agent status events."""

    agent_name: str
    agent_type: str  # "orchestrator", "lead", "worker"
    status: str  # "started", "idle", "busy", "stopped"
    task_id: str | None = None
    message: str | None = None


class LeadProgressPayload(BaseModel):
    """Payload for lead progress events."""

    lead_type: str  # "code", "research", "task"
    task_id: str
    progress: float  # 0.0 to 1.0
    message: str | None = None
    subtasks_total: int | None = None
    subtasks_complete: int | None = None


class LeadCompletePayload(BaseModel):
    """Payload for lead completion events."""

    lead_type: str
    task_id: str
    result: str
    files_modified: list[str] | None = None


class WorkerProgressPayload(BaseModel):
    """Payload for worker progress events."""

    worker_type: str  # "programmer", "reviewer", etc.
    task_id: str
    progress: float  # 0.0 to 1.0
    message: str | None = None
    current_step: str | None = None


class WorkerCompletePayload(BaseModel):
    """Payload for worker completion events."""

    worker_type: str
    task_id: str
    result: str
    files_modified: list[str] | None = None


class ToolExecutePayload(BaseModel):
    """Payload for tool execution events."""

    tool_name: str
    tool_input: dict[str, Any]
    agent: str  # Which agent is executing
    requires_approval: bool = False


class ToolResultPayload(BaseModel):
    """Payload for tool result events."""

    tool_name: str
    success: bool
    output: str | None = None
    error: str | None = None
    execution_time_ms: int | None = None


class ApprovalRequestPayload(BaseModel):
    """Payload for approval request events."""

    request_id: str
    action: str
    description: str
    risk_level: str  # "low", "medium", "high"
    details: dict[str, Any]
    timeout_seconds: int
    agent: str


class ApprovalResponsePayload(BaseModel):
    """Payload for approval response events."""

    request_id: str
    approved: bool
    reason: str | None = None
