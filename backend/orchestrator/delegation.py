"""Delegation Protocol for Emperor AI Assistant.

This module defines the protocol for delegating tasks from the
Orchestrator to Domain Leads (Code, Research, Task).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional
import time

from config import get_logger

if TYPE_CHECKING:
    from .memory_integration import MemoryContext

logger = get_logger(__name__)


class DelegationType(str, Enum):
    """Types of delegation to Domain Leads."""

    NONE = "none"          # Handle directly
    CODE = "code"          # Delegate to Code Lead
    RESEARCH = "research"  # Delegate to Research Lead
    TASK = "task"          # Delegate to Task Lead


class DelegationStatus(str, Enum):
    """Status of a delegation request."""

    PENDING = "pending"        # Request created, not started
    IN_PROGRESS = "in_progress"  # Lead is processing
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed with error
    TIMEOUT = "timeout"        # Timed out
    CANCELLED = "cancelled"    # Cancelled by user/system


class Priority(str, Enum):
    """Priority levels for delegation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class DelegationContext:
    """Context passed to Domain Leads for task execution."""

    # Conversation context
    conversation_history: list[dict[str, str]] = field(default_factory=list)

    # User context (from memory, when implemented)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    user_profile: dict[str, Any] = field(default_factory=dict)

    # Task context
    related_facts: list[str] = field(default_factory=list)
    working_directory: Optional[str] = None
    allowed_tools: list[str] = field(default_factory=list)

    # Session context
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Memory context (Part 8.4)
    memory_context: Optional["MemoryContext"] = None


@dataclass
class DelegationRequest:
    """
    Request to delegate a task to a Domain Lead.

    Created by the Orchestrator when intent classification
    determines that a task should be handled by a specialist.
    """

    # Core request info
    delegation_type: DelegationType
    task: str                        # Processed task description
    original_message: str            # User's raw message

    # Context for the lead
    context: DelegationContext = field(default_factory=DelegationContext)

    # Request metadata
    request_id: str = ""             # Unique ID for tracking
    priority: Priority = Priority.MEDIUM
    timeout_seconds: int = 120       # Max execution time

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Options
    stream_response: bool = True     # Whether to stream the response
    require_approval: bool = False   # Whether high-risk actions need approval

    def __post_init__(self):
        """Generate request ID if not provided."""
        if not self.request_id:
            from uuid import uuid4
            self.request_id = str(uuid4())


@dataclass
class DelegationResult:
    """
    Result from a Domain Lead after processing a delegation request.
    """

    # Status
    success: bool
    status: DelegationStatus

    # Response content
    content: str                     # The main response/output
    delegation_type: DelegationType

    # Metadata
    request_id: str = ""
    lead_name: str = ""              # Which lead handled it
    workers_used: list[str] = field(default_factory=list)  # Workers that helped

    # Performance
    execution_time_ms: int = 0
    tokens_used: int = 0

    # Error info (if failed)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Additional data
    artifacts: list[dict[str, Any]] = field(default_factory=list)  # Files created, etc.
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        content: str,
        delegation_type: DelegationType,
        request_id: str = "",
        lead_name: str = "",
        execution_time_ms: int = 0,
        **kwargs,
    ) -> "DelegationResult":
        """Create a successful result."""
        return cls(
            success=True,
            status=DelegationStatus.COMPLETED,
            content=content,
            delegation_type=delegation_type,
            request_id=request_id,
            lead_name=lead_name,
            execution_time_ms=execution_time_ms,
            **kwargs,
        )

    @classmethod
    def failure_result(
        cls,
        error_message: str,
        delegation_type: DelegationType,
        request_id: str = "",
        error_code: str = "UNKNOWN",
        status: DelegationStatus = DelegationStatus.FAILED,
        **kwargs,
    ) -> "DelegationResult":
        """Create a failed result."""
        return cls(
            success=False,
            status=status,
            content="",
            delegation_type=delegation_type,
            request_id=request_id,
            error_message=error_message,
            error_code=error_code,
            **kwargs,
        )


class DelegationManager:
    """
    Manages delegation of tasks to Domain Leads.

    This class handles:
    - Routing requests to appropriate leads
    - Tracking in-flight delegations
    - Publishing delegation events
    - Handling timeouts and failures
    """

    def __init__(self):
        """Initialize the delegation manager."""
        self._active_delegations: dict[str, DelegationRequest] = {}
        self._leads_available = {
            DelegationType.CODE: False,      # Part 10.1
            DelegationType.RESEARCH: False,  # Part 10.2
            DelegationType.TASK: False,      # Part 10.3
        }

    def is_lead_available(self, delegation_type: DelegationType) -> bool:
        """Check if a lead is available for the given type."""
        return self._leads_available.get(delegation_type, False)

    def register_lead(self, delegation_type: DelegationType) -> None:
        """Register that a lead is available."""
        self._leads_available[delegation_type] = True
        logger.info(f"Lead registered: {delegation_type.value}")

    def unregister_lead(self, delegation_type: DelegationType) -> None:
        """Unregister a lead."""
        self._leads_available[delegation_type] = False
        logger.info(f"Lead unregistered: {delegation_type.value}")

    async def delegate(
        self,
        request: DelegationRequest,
    ) -> DelegationResult:
        """
        Delegate a task to the appropriate Domain Lead.

        Args:
            request: The delegation request

        Returns:
            DelegationResult from the lead
        """
        start_time = time.time()

        logger.info(
            f"Delegation started: {request.delegation_type.value} "
            f"(request_id: {request.request_id})"
        )

        # Track active delegation
        self._active_delegations[request.request_id] = request

        try:
            # Publish delegation start event
            await self._publish_delegation_start(request)

            # Route to appropriate lead
            result = await self._route_to_lead(request)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms

            # Publish delegation complete event
            await self._publish_delegation_complete(request, result)

            logger.info(
                f"Delegation completed: {request.delegation_type.value} "
                f"(success: {result.success}, time: {execution_time_ms}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Delegation error: {e}", exc_info=True)

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = DelegationResult.failure_result(
                error_message=str(e),
                delegation_type=request.delegation_type,
                request_id=request.request_id,
                error_code="DELEGATION_ERROR",
            )
            result.execution_time_ms = execution_time_ms

            await self._publish_delegation_error(request, result)

            return result

        finally:
            # Remove from active delegations
            self._active_delegations.pop(request.request_id, None)

    async def delegate_stream(
        self,
        request: DelegationRequest,
    ) -> AsyncIterator[str]:
        """
        Delegate a task and stream the response.

        Args:
            request: The delegation request

        Yields:
            Response chunks from the lead
        """
        logger.info(
            f"Streaming delegation started: {request.delegation_type.value} "
            f"(request_id: {request.request_id})"
        )

        # Track active delegation
        self._active_delegations[request.request_id] = request

        try:
            # Publish delegation start event
            await self._publish_delegation_start(request)

            # Route to appropriate lead with streaming
            async for chunk in self._route_to_lead_stream(request):
                yield chunk

            # Publish delegation complete event (basic, no result details)
            await self._publish_delegation_complete(
                request,
                DelegationResult.success_result(
                    content="[Streamed]",
                    delegation_type=request.delegation_type,
                    request_id=request.request_id,
                )
            )

        except Exception as e:
            logger.error(f"Streaming delegation error: {e}", exc_info=True)
            yield f"\n\nI apologize, but I encountered an error: {e}"

            await self._publish_delegation_error(
                request,
                DelegationResult.failure_result(
                    error_message=str(e),
                    delegation_type=request.delegation_type,
                    request_id=request.request_id,
                )
            )

        finally:
            # Remove from active delegations
            self._active_delegations.pop(request.request_id, None)

    async def _route_to_lead(
        self,
        request: DelegationRequest,
    ) -> DelegationResult:
        """Route request to the appropriate lead."""

        match request.delegation_type:
            case DelegationType.CODE:
                return await self._delegate_to_code_lead(request)
            case DelegationType.RESEARCH:
                return await self._delegate_to_research_lead(request)
            case DelegationType.TASK:
                return await self._delegate_to_task_lead(request)
            case _:
                return DelegationResult.failure_result(
                    error_message=f"Unknown delegation type: {request.delegation_type}",
                    delegation_type=request.delegation_type,
                    request_id=request.request_id,
                    error_code="UNKNOWN_DELEGATION_TYPE",
                )

    async def _route_to_lead_stream(
        self,
        request: DelegationRequest,
    ) -> AsyncIterator[str]:
        """Route request to the appropriate lead with streaming."""

        match request.delegation_type:
            case DelegationType.CODE:
                async for chunk in self._delegate_to_code_lead_stream(request):
                    yield chunk
            case DelegationType.RESEARCH:
                async for chunk in self._delegate_to_research_lead_stream(request):
                    yield chunk
            case DelegationType.TASK:
                async for chunk in self._delegate_to_task_lead_stream(request):
                    yield chunk
            case _:
                yield f"Unknown delegation type: {request.delegation_type}"

    # =========================================================================
    # Lead Delegation Methods (Placeholders until Part 10)
    # =========================================================================

    async def _delegate_to_code_lead(
        self,
        request: DelegationRequest,
    ) -> DelegationResult:
        """
        Delegate to Code Lead.

        TODO: Implement in Part 10.1
        """
        if self.is_lead_available(DelegationType.CODE):
            # Future: actual lead implementation
            # from leads import get_code_lead
            # lead = get_code_lead()
            # return await lead.run(request)
            pass

        # Placeholder response
        return DelegationResult.success_result(
            content=(
                f"**Code Lead** would handle this task:\n\n"
                f"*\"{request.task}\"*\n\n"
                f"---\n"
                f"*Domain Leads are not yet implemented (Part 10). "
                f"The Code Lead will be able to:*\n"
                f"- Write and modify code\n"
                f"- Debug and fix errors\n"
                f"- Review code quality\n"
                f"- Refactor for better structure\n"
            ),
            delegation_type=DelegationType.CODE,
            request_id=request.request_id,
            lead_name="code_lead (placeholder)",
            metadata={"placeholder": True},
        )

    async def _delegate_to_research_lead(
        self,
        request: DelegationRequest,
    ) -> DelegationResult:
        """
        Delegate to Research Lead.

        TODO: Implement in Part 10.2
        """
        if self.is_lead_available(DelegationType.RESEARCH):
            # Future: actual lead implementation
            pass

        # Placeholder response
        return DelegationResult.success_result(
            content=(
                f"**Research Lead** would handle this task:\n\n"
                f"*\"{request.task}\"*\n\n"
                f"---\n"
                f"*Domain Leads are not yet implemented (Part 10). "
                f"The Research Lead will be able to:*\n"
                f"- Conduct in-depth research\n"
                f"- Analyze and compare options\n"
                f"- Provide citations and sources\n"
                f"- Summarize complex topics\n"
            ),
            delegation_type=DelegationType.RESEARCH,
            request_id=request.request_id,
            lead_name="research_lead (placeholder)",
            metadata={"placeholder": True},
        )

    async def _delegate_to_task_lead(
        self,
        request: DelegationRequest,
    ) -> DelegationResult:
        """
        Delegate to Task Lead.

        TODO: Implement in Part 10.3
        """
        if self.is_lead_available(DelegationType.TASK):
            # Future: actual lead implementation
            pass

        # Placeholder response
        return DelegationResult.success_result(
            content=(
                f"**Task Lead** would handle this task:\n\n"
                f"*\"{request.task}\"*\n\n"
                f"---\n"
                f"*Domain Leads are not yet implemented (Part 10). "
                f"The Task Lead will be able to:*\n"
                f"- Execute shell commands\n"
                f"- Manage files and directories\n"
                f"- Run automation workflows\n"
                f"- Set up environments\n"
            ),
            delegation_type=DelegationType.TASK,
            request_id=request.request_id,
            lead_name="task_lead (placeholder)",
            metadata={"placeholder": True},
        )

    # Streaming versions
    async def _delegate_to_code_lead_stream(
        self,
        request: DelegationRequest,
    ) -> AsyncIterator[str]:
        """Stream delegation to Code Lead."""
        result = await self._delegate_to_code_lead(request)
        # Simulate streaming by yielding the content
        yield result.content

    async def _delegate_to_research_lead_stream(
        self,
        request: DelegationRequest,
    ) -> AsyncIterator[str]:
        """Stream delegation to Research Lead."""
        result = await self._delegate_to_research_lead(request)
        yield result.content

    async def _delegate_to_task_lead_stream(
        self,
        request: DelegationRequest,
    ) -> AsyncIterator[str]:
        """Stream delegation to Task Lead."""
        result = await self._delegate_to_task_lead(request)
        yield result.content

    # =========================================================================
    # Event Publishing
    # =========================================================================

    async def _publish_delegation_start(
        self,
        request: DelegationRequest,
    ) -> None:
        """Publish event when delegation starts."""
        try:
            from process_manager import get_event_bus, Event, EventType, Priority as EventPriority

            event_bus = get_event_bus()
            if not event_bus.is_running:
                return

            event = Event(
                type=EventType.ORCHESTRATOR_DELEGATE,
                source="orchestrator",
                data={
                    "request_id": request.request_id,
                    "delegation_type": request.delegation_type.value,
                    "task": request.task[:200],  # Truncate for event
                    "priority": request.priority.value,
                },
                correlation_id=request.context.correlation_id,
                priority=EventPriority.MEDIUM,
            )

            await event_bus.publish(event)

        except Exception as e:
            logger.warning(f"Failed to publish delegation start event: {e}")

    async def _publish_delegation_complete(
        self,
        request: DelegationRequest,
        result: DelegationResult,
    ) -> None:
        """Publish event when delegation completes."""
        try:
            from process_manager import get_event_bus, Event, EventType, Priority as EventPriority

            event_bus = get_event_bus()
            if not event_bus.is_running:
                return

            event = Event(
                type=EventType.LEAD_COMPLETE,
                source="orchestrator",
                data={
                    "request_id": request.request_id,
                    "delegation_type": request.delegation_type.value,
                    "success": result.success,
                    "lead_name": result.lead_name,
                    "execution_time_ms": result.execution_time_ms,
                    "workers_used": result.workers_used,
                },
                correlation_id=request.context.correlation_id,
                priority=EventPriority.MEDIUM,
            )

            await event_bus.publish(event)

        except Exception as e:
            logger.warning(f"Failed to publish delegation complete event: {e}")

    async def _publish_delegation_error(
        self,
        request: DelegationRequest,
        result: DelegationResult,
    ) -> None:
        """Publish event when delegation fails."""
        try:
            from process_manager import get_event_bus, Event, EventType, Priority as EventPriority

            event_bus = get_event_bus()
            if not event_bus.is_running:
                return

            event = Event(
                type=EventType.LEAD_ERROR,
                source="orchestrator",
                data={
                    "request_id": request.request_id,
                    "delegation_type": request.delegation_type.value,
                    "error_message": result.error_message,
                    "error_code": result.error_code,
                },
                correlation_id=request.context.correlation_id,
                priority=EventPriority.HIGH,
            )

            await event_bus.publish(event)

        except Exception as e:
            logger.warning(f"Failed to publish delegation error event: {e}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @property
    def active_delegation_count(self) -> int:
        """Return number of active delegations."""
        return len(self._active_delegations)

    def get_active_delegation(self, request_id: str) -> Optional[DelegationRequest]:
        """Get an active delegation by ID."""
        return self._active_delegations.get(request_id)

    def cancel_delegation(self, request_id: str) -> bool:
        """
        Cancel an active delegation.

        Note: This removes tracking but doesn't stop in-progress work.
        """
        if request_id in self._active_delegations:
            del self._active_delegations[request_id]
            logger.info(f"Delegation cancelled: {request_id}")
            return True
        return False


# Singleton instance
_delegation_manager: Optional[DelegationManager] = None


def get_delegation_manager() -> DelegationManager:
    """Get the singleton delegation manager instance."""
    global _delegation_manager
    if _delegation_manager is None:
        _delegation_manager = DelegationManager()
    return _delegation_manager
