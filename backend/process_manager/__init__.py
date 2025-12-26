"""Process Manager module for Emperor AI Assistant.

This module provides the event bus and agent lifecycle management:
- Event definitions and types
- Pub/sub event bus
- Cross-agent communication
- UI event streaming
"""

from .events import (
    # Enums
    EventType,
    EventCategory,
    Priority,
    RiskLevel,
    LeadType,
    WorkerType,
    # Event class
    Event,
    # Payload types
    DelegatePayload,
    ResponsePayload,
    LeadAssignPayload,
    LeadCompletePayload,
    WorkerProgressPayload,
    WorkerCompletePayload,
    ToolExecutePayload,
    ToolResultPayload,
    ApprovalRequestPayload,
    ApprovalResponsePayload,
    AgentStatusPayload,
    ErrorPayload,
    # Factory functions
    create_event,
    create_delegation_event,
    create_approval_request,
    create_tool_event,
    create_error_event,
)

from .event_bus import (
    EventBus,
    Subscription,
    get_event_bus,
    init_event_bus,
    shutdown_event_bus,
)

from .ui_streamer import (
    UIEventStreamer,
    UIEvent,
    get_ui_streamer,
    init_ui_streamer,
    shutdown_ui_streamer,
)

from .agent_comm import (
    # Data classes
    DelegationRequest,
    DelegationResult,
    WorkerAssignment,
    WorkerResult,
    # ID generation
    generate_correlation_id,
    generate_task_id,
    # Orchestrator → Lead
    delegate_to_lead,
    # Lead → Worker
    assign_to_worker,
    # Completion reporting
    report_lead_complete,
    report_lead_error,
    report_worker_complete,
    report_worker_error,
    # Progress reporting
    report_lead_progress,
    report_worker_progress,
    # Status reporting
    report_agent_status,
    # Convenience class
    AgentCommunicator,
)

__all__ = [
    # Enums
    "EventType",
    "EventCategory",
    "Priority",
    "RiskLevel",
    "LeadType",
    "WorkerType",
    # Event class
    "Event",
    # Payload types
    "DelegatePayload",
    "ResponsePayload",
    "LeadAssignPayload",
    "LeadCompletePayload",
    "WorkerProgressPayload",
    "WorkerCompletePayload",
    "ToolExecutePayload",
    "ToolResultPayload",
    "ApprovalRequestPayload",
    "ApprovalResponsePayload",
    "AgentStatusPayload",
    "ErrorPayload",
    # Factory functions
    "create_event",
    "create_delegation_event",
    "create_approval_request",
    "create_tool_event",
    "create_error_event",
    # Event Bus
    "EventBus",
    "Subscription",
    "get_event_bus",
    "init_event_bus",
    "shutdown_event_bus",
    # UI Streamer
    "UIEventStreamer",
    "UIEvent",
    "get_ui_streamer",
    "init_ui_streamer",
    "shutdown_ui_streamer",
    # Agent Communication - Data classes
    "DelegationRequest",
    "DelegationResult",
    "WorkerAssignment",
    "WorkerResult",
    # Agent Communication - ID generation
    "generate_correlation_id",
    "generate_task_id",
    # Agent Communication - Delegation
    "delegate_to_lead",
    "assign_to_worker",
    # Agent Communication - Reporting
    "report_lead_complete",
    "report_lead_error",
    "report_worker_complete",
    "report_worker_error",
    "report_lead_progress",
    "report_worker_progress",
    "report_agent_status",
    # Agent Communication - Convenience class
    "AgentCommunicator",
]
