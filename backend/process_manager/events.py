"""Event definitions for the Emperor AI Assistant event bus.

This module defines the structure and types of all events that flow
through the system. Events enable loose coupling between components:
- Orchestrator
- Domain Leads (Code, Research, Task)
- Workers (Programmer, Reviewer, etc.)
- Tools
- UI
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, TypedDict
from uuid import uuid4


# =============================================================================
# Event Types
# =============================================================================


class EventCategory(str, Enum):
    """Categories of events for filtering and routing."""
    ORCHESTRATOR = "orchestrator"
    LEAD = "lead"
    WORKER = "worker"
    TOOL = "tool"
    APPROVAL = "approval"
    AGENT = "agent"
    MEMORY = "memory"
    SYSTEM = "system"


class EventType(str, Enum):
    """All event types in the system.

    Naming convention: {category}.{action}
    """

    # -------------------------------------------------------------------------
    # Orchestrator Events
    # Published by the main orchestrator when delegating or responding
    # -------------------------------------------------------------------------
    ORCHESTRATOR_DELEGATE = "orchestrator.delegate"
    ORCHESTRATOR_RESPONSE = "orchestrator.response"
    ORCHESTRATOR_ERROR = "orchestrator.error"

    # -------------------------------------------------------------------------
    # Lead Events
    # Published by Domain Leads (Code, Research, Task) when managing workers
    # -------------------------------------------------------------------------
    LEAD_RECEIVED = "lead.received"      # Lead received a task
    LEAD_PLANNING = "lead.planning"      # Lead is planning subtasks
    LEAD_ASSIGN = "lead.assign"          # Lead assigns to Worker
    LEAD_PROGRESS = "lead.progress"      # Lead progress update
    LEAD_COMPLETE = "lead.complete"      # Lead finished task
    LEAD_ERROR = "lead.error"            # Lead encountered error

    # -------------------------------------------------------------------------
    # Worker Events
    # Published by Workers (Programmer, Reviewer, Documentor, etc.)
    # -------------------------------------------------------------------------
    WORKER_START = "worker.start"        # Worker started subtask
    WORKER_PROGRESS = "worker.progress"  # Worker progress update
    WORKER_COMPLETE = "worker.complete"  # Worker finished subtask
    WORKER_ERROR = "worker.error"        # Worker encountered error

    # -------------------------------------------------------------------------
    # Tool Events
    # Published when tools are executed
    # -------------------------------------------------------------------------
    TOOL_EXECUTE = "tool.execute"        # Tool execution requested
    TOOL_PROGRESS = "tool.progress"      # Tool execution progress
    TOOL_RESULT = "tool.result"          # Tool execution completed
    TOOL_ERROR = "tool.error"            # Tool execution failed

    # -------------------------------------------------------------------------
    # Approval Events
    # Published for dangerous actions needing user approval
    # -------------------------------------------------------------------------
    APPROVAL_REQUEST = "approval.request"    # Action needs approval
    APPROVAL_GRANTED = "approval.granted"    # User approved
    APPROVAL_DENIED = "approval.denied"      # User denied
    APPROVAL_TIMEOUT = "approval.timeout"    # Approval timed out

    # -------------------------------------------------------------------------
    # Agent Status Events
    # Published for tracking agent lifecycle
    # -------------------------------------------------------------------------
    AGENT_STARTED = "agent.started"      # Agent began execution
    AGENT_IDLE = "agent.idle"            # Agent is waiting
    AGENT_BUSY = "agent.busy"            # Agent is processing
    AGENT_STOPPED = "agent.stopped"      # Agent stopped

    # -------------------------------------------------------------------------
    # Memory Events
    # Published for memory operations
    # -------------------------------------------------------------------------
    MEMORY_STORE = "memory.store"        # Information stored
    MEMORY_RECALL = "memory.recall"      # Information retrieved
    MEMORY_FORGET = "memory.forget"      # Information deleted

    # -------------------------------------------------------------------------
    # System Events
    # Published for system-level operations
    # -------------------------------------------------------------------------
    SYSTEM_STARTUP = "system.startup"    # System started
    SYSTEM_SHUTDOWN = "system.shutdown"  # System shutting down
    SYSTEM_ERROR = "system.error"        # System error

    @property
    def category(self) -> EventCategory:
        """Get the category for this event type."""
        category_name = self.value.split(".")[0].upper()
        return EventCategory(category_name.lower())


class Priority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk levels for approval requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LeadType(str, Enum):
    """Types of Domain Leads."""
    CODE = "code"
    RESEARCH = "research"
    TASK = "task"


class WorkerType(str, Enum):
    """Types of Workers."""
    PROGRAMMER = "programmer"
    REVIEWER = "reviewer"
    DOCUMENTOR = "documentor"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXECUTOR = "executor"
    MONITOR = "monitor"


# =============================================================================
# Payload Type Definitions
# =============================================================================


class DelegatePayload(TypedDict, total=False):
    """Payload for orchestrator.delegate events."""
    lead: str              # "code", "research", or "task"
    task: str              # Task description
    context: dict          # Additional context
    priority: str          # Priority level
    user_message_id: str   # Original user message ID


class ResponsePayload(TypedDict, total=False):
    """Payload for orchestrator.response events."""
    content: str           # Response content
    message_id: str        # Message ID
    sources: list          # Sources used (for research)


class LeadAssignPayload(TypedDict, total=False):
    """Payload for lead.assign events."""
    worker: str            # Worker type
    subtask: str           # Subtask description
    parent_task_id: str    # Link to parent task
    context: dict          # Additional context
    priority: str          # Priority level


class LeadCompletePayload(TypedDict, total=False):
    """Payload for lead.complete events."""
    task_id: str           # Task ID
    result: str            # Aggregated result
    subtasks_completed: int  # Number of subtasks
    files_modified: list   # Files that were modified


class WorkerProgressPayload(TypedDict, total=False):
    """Payload for worker.progress events."""
    task_id: str           # Task ID
    progress: float        # Progress 0.0 to 1.0
    message: str           # Progress message
    current_step: str      # Current step description


class WorkerCompletePayload(TypedDict, total=False):
    """Payload for worker.complete events."""
    task_id: str           # Task ID
    result: str            # Result content
    files_modified: list   # Files that were modified
    metadata: dict         # Additional metadata


class ToolExecutePayload(TypedDict, total=False):
    """Payload for tool.execute events."""
    tool_name: str         # Tool name
    input: dict            # Tool input parameters
    agent: str             # Which agent requested it
    requires_approval: bool  # Whether approval is needed


class ToolResultPayload(TypedDict, total=False):
    """Payload for tool.result events."""
    tool_name: str         # Tool name
    output: str            # Tool output
    success: bool          # Whether it succeeded
    execution_time_ms: int  # Execution time in milliseconds


class ApprovalRequestPayload(TypedDict, total=False):
    """Payload for approval.request events."""
    request_id: str        # Unique ID for this request
    action: str            # What action needs approval
    description: str       # Human-readable description
    risk_level: str        # "low", "medium", "high"
    details: dict          # Full details for review
    timeout_seconds: int   # How long to wait for approval
    agent: str             # Which agent requested it


class ApprovalResponsePayload(TypedDict, total=False):
    """Payload for approval.granted/denied events."""
    request_id: str        # Request ID being responded to
    approved: bool         # Whether it was approved
    reason: str            # Reason (for denial)
    responded_at: str      # When the response was given


class AgentStatusPayload(TypedDict, total=False):
    """Payload for agent status events."""
    agent_name: str        # Agent identifier
    agent_type: str        # Agent type (lead, worker, etc.)
    task_id: str           # Current task ID (if any)
    status: str            # Current status
    message: str           # Status message


class ErrorPayload(TypedDict, total=False):
    """Payload for error events."""
    error: str             # Error message
    error_type: str        # Error type/class
    task_id: str           # Related task ID
    agent: str             # Agent that encountered error
    recoverable: bool      # Whether it's recoverable
    stack_trace: str       # Stack trace (debug mode)


# =============================================================================
# Event Class
# =============================================================================


@dataclass
class Event:
    """Base event structure for all system events.

    Events are the primary communication mechanism between components.
    They enable loose coupling and provide a complete audit trail.

    Attributes:
        type: The event type (from EventType enum)
        data: Event-specific payload data
        source: Identifier of the component that published the event
        id: Unique event identifier
        timestamp: When the event was created
        correlation_id: Links related events (e.g., same user request)
        priority: Event priority for processing order
    """

    type: EventType
    data: dict[str, Any]
    source: str
    id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    priority: Priority = Priority.NORMAL

    def __post_init__(self):
        """Validate event after initialization."""
        if isinstance(self.type, str):
            self.type = EventType(self.type)
        if isinstance(self.priority, str):
            self.priority = Priority(self.priority)

    @property
    def category(self) -> EventCategory:
        """Get the category for this event."""
        return self.type.category

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create an Event from a dictionary."""
        return cls(
            id=data.get("id", f"evt_{uuid4().hex[:12]}"),
            type=EventType(data["type"]),
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else datetime.now(timezone.utc),
            correlation_id=data.get("correlation_id"),
            priority=Priority(data.get("priority", "normal")),
            data=data.get("data", {}),
        )

    def with_correlation(self, correlation_id: str) -> "Event":
        """Create a copy of this event with a correlation ID."""
        return Event(
            id=self.id,
            type=self.type,
            source=self.source,
            timestamp=self.timestamp,
            correlation_id=correlation_id,
            priority=self.priority,
            data=self.data,
        )


# =============================================================================
# Event Factory Functions
# =============================================================================


def create_event(
    event_type: EventType,
    source: str,
    data: dict[str, Any],
    correlation_id: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
) -> Event:
    """Create a new event with the given parameters.

    Args:
        event_type: Type of event
        source: Component publishing the event
        data: Event payload
        correlation_id: Optional correlation ID
        priority: Event priority

    Returns:
        A new Event instance
    """
    return Event(
        type=event_type,
        source=source,
        data=data,
        correlation_id=correlation_id,
        priority=priority,
    )


def create_delegation_event(
    lead: LeadType,
    task: str,
    context: Optional[dict] = None,
    correlation_id: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
) -> Event:
    """Create an orchestrator.delegate event.

    Args:
        lead: Which lead to delegate to
        task: Task description
        context: Additional context
        correlation_id: Correlation ID for tracking
        priority: Task priority

    Returns:
        A delegation Event
    """
    return Event(
        type=EventType.ORCHESTRATOR_DELEGATE,
        source="orchestrator",
        data={
            "lead": lead.value if isinstance(lead, LeadType) else lead,
            "task": task,
            "context": context or {},
            "priority": priority.value,
        },
        correlation_id=correlation_id,
        priority=priority,
    )


def create_approval_request(
    action: str,
    description: str,
    risk_level: RiskLevel,
    details: dict[str, Any],
    agent: str,
    timeout_seconds: int = 60,
    correlation_id: Optional[str] = None,
) -> Event:
    """Create an approval.request event.

    Args:
        action: Action needing approval
        description: Human-readable description
        risk_level: Risk level of the action
        details: Full details for review
        agent: Agent requesting approval
        timeout_seconds: Approval timeout
        correlation_id: Correlation ID

    Returns:
        An approval request Event
    """
    request_id = f"apr_{uuid4().hex[:12]}"

    return Event(
        type=EventType.APPROVAL_REQUEST,
        source=agent,
        data={
            "request_id": request_id,
            "action": action,
            "description": description,
            "risk_level": risk_level.value if isinstance(risk_level, RiskLevel) else risk_level,
            "details": details,
            "timeout_seconds": timeout_seconds,
            "agent": agent,
        },
        correlation_id=correlation_id,
        priority=Priority.HIGH,
    )


def create_tool_event(
    tool_name: str,
    input_data: dict[str, Any],
    agent: str,
    requires_approval: bool = False,
    correlation_id: Optional[str] = None,
) -> Event:
    """Create a tool.execute event.

    Args:
        tool_name: Name of the tool
        input_data: Tool input parameters
        agent: Agent requesting execution
        requires_approval: Whether approval is needed
        correlation_id: Correlation ID

    Returns:
        A tool execution Event
    """
    return Event(
        type=EventType.TOOL_EXECUTE,
        source=agent,
        data={
            "tool_name": tool_name,
            "input": input_data,
            "agent": agent,
            "requires_approval": requires_approval,
        },
        correlation_id=correlation_id,
    )


def create_error_event(
    error: str,
    source: str,
    error_type: str = "Error",
    task_id: Optional[str] = None,
    recoverable: bool = True,
    correlation_id: Optional[str] = None,
) -> Event:
    """Create an error event.

    Args:
        error: Error message
        source: Component that encountered the error
        error_type: Type of error
        task_id: Related task ID
        recoverable: Whether it's recoverable
        correlation_id: Correlation ID

    Returns:
        An error Event
    """
    # Determine the appropriate error event type
    if "orchestrator" in source.lower():
        event_type = EventType.ORCHESTRATOR_ERROR
    elif "lead" in source.lower():
        event_type = EventType.LEAD_ERROR
    elif "worker" in source.lower():
        event_type = EventType.WORKER_ERROR
    elif "tool" in source.lower():
        event_type = EventType.TOOL_ERROR
    else:
        event_type = EventType.SYSTEM_ERROR

    return Event(
        type=event_type,
        source=source,
        data={
            "error": error,
            "error_type": error_type,
            "task_id": task_id,
            "agent": source,
            "recoverable": recoverable,
        },
        correlation_id=correlation_id,
        priority=Priority.HIGH,
    )
