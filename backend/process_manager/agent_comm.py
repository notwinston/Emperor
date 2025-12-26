"""Cross-Agent Communication for Emperor AI Assistant.

This module provides communication helpers for the agent hierarchy:
- Orchestrator → Lead delegation
- Lead → Worker assignment
- Result reporting up the chain
- Error propagation

All communication flows through the Event Bus using the publish_and_wait
pattern for request/response interactions.

Architecture:
    User Message
         ↓
    Orchestrator (CLI)
         ↓ delegate_to_lead()
    Lead (SDK)
         ↓ assign_to_worker()
    Worker (SDK)
         ↓ report_complete()
    (bubbles back up)
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from config import get_logger
from .events import (
    Event,
    EventType,
    Priority,
    LeadType,
    WorkerType,
    create_event,
    create_delegation_event,
    create_error_event,
)
from .event_bus import get_event_bus

logger = get_logger(__name__)


# =============================================================================
# Data Classes for Communication
# =============================================================================


@dataclass
class DelegationRequest:
    """Request to delegate a task to a Lead."""

    lead: LeadType
    task: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    timeout: float = 120.0  # seconds
    correlation_id: Optional[str] = None


@dataclass
class DelegationResult:
    """Result from a Lead after completing a delegated task."""

    success: bool
    result: Optional[str] = None
    files_modified: list[str] = field(default_factory=list)
    error: Optional[str] = None
    lead: Optional[LeadType] = None
    task_id: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class WorkerAssignment:
    """Assignment of a subtask to a Worker."""

    worker: WorkerType
    subtask: str
    context: dict[str, Any] = field(default_factory=dict)
    parent_task_id: Optional[str] = None
    priority: Priority = Priority.NORMAL
    timeout: float = 60.0  # seconds


@dataclass
class WorkerResult:
    """Result from a Worker after completing a subtask."""

    success: bool
    result: Optional[str] = None
    files_modified: list[str] = field(default_factory=list)
    error: Optional[str] = None
    worker: Optional[WorkerType] = None
    task_id: Optional[str] = None
    duration_ms: Optional[int] = None


# =============================================================================
# Correlation ID Management
# =============================================================================


def generate_correlation_id() -> str:
    """Generate a new correlation ID for tracking related events."""
    return f"cor_{uuid4().hex[:12]}"


def generate_task_id(prefix: str = "task") -> str:
    """Generate a unique task ID."""
    return f"{prefix}_{uuid4().hex[:12]}"


# =============================================================================
# Orchestrator → Lead Communication
# =============================================================================


async def delegate_to_lead(
    lead: LeadType,
    task: str,
    context: Optional[dict[str, Any]] = None,
    priority: Priority = Priority.NORMAL,
    timeout: float = 120.0,
    correlation_id: Optional[str] = None,
) -> DelegationResult:
    """
    Delegate a task from the Orchestrator to a Domain Lead.

    This publishes an orchestrator.delegate event and waits for
    a lead.complete or lead.error response.

    Args:
        lead: Which Lead to delegate to (CODE, RESEARCH, TASK)
        task: Task description
        context: Additional context for the Lead
        priority: Task priority
        timeout: Maximum time to wait for response (seconds)
        correlation_id: Optional correlation ID (generated if not provided)

    Returns:
        DelegationResult with success status and result/error

    Example:
        result = await delegate_to_lead(
            lead=LeadType.CODE,
            task="Implement user authentication",
            context={"files": ["auth.py"]},
            timeout=120.0,
        )
        if result.success:
            print(f"Completed: {result.result}")
        else:
            print(f"Failed: {result.error}")
    """
    bus = get_event_bus()
    start_time = datetime.now(timezone.utc)

    # Generate IDs
    if not correlation_id:
        correlation_id = generate_correlation_id()
    task_id = generate_task_id("del")

    # Create delegation event
    event = create_delegation_event(
        lead=lead,
        task=task,
        context=context or {},
        correlation_id=correlation_id,
        priority=priority,
    )

    # Add task_id to the event data
    event.data["task_id"] = task_id

    logger.info(f"Delegating to {lead.value}: {task[:50]}... (id: {task_id})")

    try:
        # Publish and wait for response
        response = await bus.publish_and_wait(
            event=event,
            response_types=[EventType.LEAD_COMPLETE, EventType.LEAD_ERROR],
            timeout=timeout,
        )

        # Calculate duration
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        if response is None:
            # Timeout
            logger.warning(f"Delegation timeout: {task_id}")
            return DelegationResult(
                success=False,
                error="Delegation timed out",
                lead=lead,
                task_id=task_id,
                duration_ms=duration_ms,
            )

        if response.type == EventType.LEAD_COMPLETE:
            # Success
            logger.info(f"Delegation complete: {task_id} ({duration_ms}ms)")
            return DelegationResult(
                success=True,
                result=response.data.get("result"),
                files_modified=response.data.get("files_modified", []),
                lead=lead,
                task_id=task_id,
                duration_ms=duration_ms,
            )
        else:
            # Error
            logger.error(f"Delegation failed: {task_id} - {response.data.get('error')}")
            return DelegationResult(
                success=False,
                error=response.data.get("error", "Unknown error"),
                lead=lead,
                task_id=task_id,
                duration_ms=duration_ms,
            )

    except Exception as e:
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        logger.error(f"Delegation exception: {task_id} - {e}")
        return DelegationResult(
            success=False,
            error=str(e),
            lead=lead,
            task_id=task_id,
            duration_ms=duration_ms,
        )


# =============================================================================
# Lead → Worker Communication
# =============================================================================


async def assign_to_worker(
    worker: WorkerType,
    subtask: str,
    context: Optional[dict[str, Any]] = None,
    parent_task_id: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
    timeout: float = 60.0,
    correlation_id: Optional[str] = None,
    source: str = "lead",
) -> WorkerResult:
    """
    Assign a subtask from a Lead to a Worker.

    This publishes a lead.assign event and waits for
    a worker.complete or worker.error response.

    Args:
        worker: Which Worker to assign to
        subtask: Subtask description
        context: Additional context for the Worker
        parent_task_id: ID of the parent task (for tracking)
        priority: Task priority
        timeout: Maximum time to wait for response (seconds)
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Lead is assigning)

    Returns:
        WorkerResult with success status and result/error

    Example:
        result = await assign_to_worker(
            worker=WorkerType.PROGRAMMER,
            subtask="Write the login function",
            parent_task_id="del_abc123",
            timeout=60.0,
        )
    """
    bus = get_event_bus()
    start_time = datetime.now(timezone.utc)

    # Generate IDs
    if not correlation_id:
        correlation_id = generate_correlation_id()
    task_id = generate_task_id("wrk")

    # Create assignment event
    event = create_event(
        event_type=EventType.LEAD_ASSIGN,
        source=source,
        data={
            "worker": worker.value if isinstance(worker, WorkerType) else worker,
            "subtask": subtask,
            "context": context or {},
            "parent_task_id": parent_task_id,
            "task_id": task_id,
            "priority": priority.value,
        },
        correlation_id=correlation_id,
        priority=priority,
    )

    logger.info(f"Assigning to {worker.value}: {subtask[:50]}... (id: {task_id})")

    try:
        # Publish and wait for response
        response = await bus.publish_and_wait(
            event=event,
            response_types=[EventType.WORKER_COMPLETE, EventType.WORKER_ERROR],
            timeout=timeout,
        )

        # Calculate duration
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        if response is None:
            # Timeout
            logger.warning(f"Worker assignment timeout: {task_id}")
            return WorkerResult(
                success=False,
                error="Worker timed out",
                worker=worker,
                task_id=task_id,
                duration_ms=duration_ms,
            )

        if response.type == EventType.WORKER_COMPLETE:
            # Success
            logger.info(f"Worker complete: {task_id} ({duration_ms}ms)")
            return WorkerResult(
                success=True,
                result=response.data.get("result"),
                files_modified=response.data.get("files_modified", []),
                worker=worker,
                task_id=task_id,
                duration_ms=duration_ms,
            )
        else:
            # Error
            logger.error(f"Worker failed: {task_id} - {response.data.get('error')}")
            return WorkerResult(
                success=False,
                error=response.data.get("error", "Unknown error"),
                worker=worker,
                task_id=task_id,
                duration_ms=duration_ms,
            )

    except Exception as e:
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        logger.error(f"Worker assignment exception: {task_id} - {e}")
        return WorkerResult(
            success=False,
            error=str(e),
            worker=worker,
            task_id=task_id,
            duration_ms=duration_ms,
        )


# =============================================================================
# Result Reporting (Worker/Lead → Parent)
# =============================================================================


async def report_lead_complete(
    task_id: str,
    result: str,
    files_modified: Optional[list[str]] = None,
    correlation_id: Optional[str] = None,
    source: str = "lead",
) -> None:
    """
    Report that a Lead has completed its task.

    Called by Leads to notify the Orchestrator of completion.

    Args:
        task_id: The task ID being completed
        result: The result/output of the task
        files_modified: List of files that were modified
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Lead)
    """
    bus = get_event_bus()

    event = create_event(
        event_type=EventType.LEAD_COMPLETE,
        source=source,
        data={
            "task_id": task_id,
            "result": result,
            "files_modified": files_modified or [],
            "subtasks_completed": 0,  # Can be updated by Lead
        },
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.info(f"Lead complete reported: {task_id}")


async def report_lead_error(
    task_id: str,
    error: str,
    recoverable: bool = True,
    correlation_id: Optional[str] = None,
    source: str = "lead",
) -> None:
    """
    Report that a Lead encountered an error.

    Args:
        task_id: The task ID that failed
        error: Error description
        recoverable: Whether the error is recoverable
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Lead)
    """
    bus = get_event_bus()

    event = create_error_event(
        error=error,
        source=source,
        task_id=task_id,
        recoverable=recoverable,
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.error(f"Lead error reported: {task_id} - {error}")


async def report_worker_complete(
    task_id: str,
    result: str,
    files_modified: Optional[list[str]] = None,
    metadata: Optional[dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    source: str = "worker",
) -> None:
    """
    Report that a Worker has completed its subtask.

    Called by Workers to notify their Lead of completion.

    Args:
        task_id: The subtask ID being completed
        result: The result/output of the subtask
        files_modified: List of files that were modified
        metadata: Additional metadata
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Worker)
    """
    bus = get_event_bus()

    event = create_event(
        event_type=EventType.WORKER_COMPLETE,
        source=source,
        data={
            "task_id": task_id,
            "result": result,
            "files_modified": files_modified or [],
            "metadata": metadata or {},
        },
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.info(f"Worker complete reported: {task_id}")


async def report_worker_error(
    task_id: str,
    error: str,
    recoverable: bool = True,
    correlation_id: Optional[str] = None,
    source: str = "worker",
) -> None:
    """
    Report that a Worker encountered an error.

    Args:
        task_id: The subtask ID that failed
        error: Error description
        recoverable: Whether the error is recoverable
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Worker)
    """
    bus = get_event_bus()

    event = create_error_event(
        error=error,
        source=source,
        task_id=task_id,
        recoverable=recoverable,
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.error(f"Worker error reported: {task_id} - {error}")


# =============================================================================
# Progress Reporting
# =============================================================================


async def report_lead_progress(
    task_id: str,
    progress: float,
    message: Optional[str] = None,
    subtasks_total: Optional[int] = None,
    subtasks_complete: Optional[int] = None,
    correlation_id: Optional[str] = None,
    source: str = "lead",
) -> None:
    """
    Report progress on a Lead's task.

    Args:
        task_id: The task ID
        progress: Progress from 0.0 to 1.0
        message: Optional progress message
        subtasks_total: Total number of subtasks
        subtasks_complete: Number of subtasks completed
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Lead)
    """
    bus = get_event_bus()

    event = create_event(
        event_type=EventType.LEAD_PROGRESS,
        source=source,
        data={
            "task_id": task_id,
            "progress": max(0.0, min(1.0, progress)),
            "message": message,
            "subtasks_total": subtasks_total,
            "subtasks_complete": subtasks_complete,
        },
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.debug(f"Lead progress: {task_id} - {progress:.0%}")


async def report_worker_progress(
    task_id: str,
    progress: float,
    message: Optional[str] = None,
    current_step: Optional[str] = None,
    correlation_id: Optional[str] = None,
    source: str = "worker",
) -> None:
    """
    Report progress on a Worker's subtask.

    Args:
        task_id: The subtask ID
        progress: Progress from 0.0 to 1.0
        message: Optional progress message
        current_step: Current step description
        correlation_id: Correlation ID for tracking
        source: Source identifier (which Worker)
    """
    bus = get_event_bus()

    event = create_event(
        event_type=EventType.WORKER_PROGRESS,
        source=source,
        data={
            "task_id": task_id,
            "progress": max(0.0, min(1.0, progress)),
            "message": message,
            "current_step": current_step,
        },
        correlation_id=correlation_id,
    )

    await bus.publish(event)
    logger.debug(f"Worker progress: {task_id} - {progress:.0%}")


# =============================================================================
# Agent Status Updates
# =============================================================================


async def report_agent_status(
    agent_name: str,
    agent_type: str,
    status: str,
    task_id: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """
    Report an agent's status change.

    Args:
        agent_name: Name of the agent
        agent_type: Type (orchestrator, lead, worker)
        status: Status (started, idle, busy, stopped)
        task_id: Current task ID if busy
        message: Optional status message
    """
    bus = get_event_bus()

    # Map status to event type
    status_to_event = {
        "started": EventType.AGENT_STARTED,
        "idle": EventType.AGENT_IDLE,
        "busy": EventType.AGENT_BUSY,
        "stopped": EventType.AGENT_STOPPED,
    }

    event_type = status_to_event.get(status, EventType.AGENT_BUSY)

    event = create_event(
        event_type=event_type,
        source=agent_name,
        data={
            "agent_name": agent_name,
            "agent_type": agent_type,
            "status": status,
            "task_id": task_id,
            "message": message,
        },
    )

    await bus.publish(event)
    logger.debug(f"Agent status: {agent_name} ({agent_type}) - {status}")


# =============================================================================
# Convenience Class for Agents
# =============================================================================


class AgentCommunicator:
    """
    Convenience wrapper for agent communication.

    Provides a cleaner interface for agents to use, with
    automatic source tracking and correlation ID management.

    Example:
        comm = AgentCommunicator(
            agent_name="code_lead",
            agent_type="lead",
        )

        # Report status
        await comm.report_busy(task_id="task_123")

        # Assign worker
        result = await comm.assign_worker(
            worker=WorkerType.PROGRAMMER,
            subtask="Write the function",
        )

        # Report completion
        await comm.report_complete(task_id="task_123", result="Done!")
    """

    def __init__(
        self,
        agent_name: str,
        agent_type: str,  # "orchestrator", "lead", "worker"
        default_correlation_id: Optional[str] = None,
    ):
        """
        Initialize the communicator.

        Args:
            agent_name: Unique name for this agent
            agent_type: Type of agent (orchestrator, lead, worker)
            default_correlation_id: Default correlation ID to use
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.correlation_id = default_correlation_id

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the current correlation ID."""
        self.correlation_id = correlation_id

    # --- Status Methods ---

    async def report_started(self, message: Optional[str] = None) -> None:
        """Report that this agent has started."""
        await report_agent_status(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            status="started",
            message=message,
        )

    async def report_idle(self, message: Optional[str] = None) -> None:
        """Report that this agent is idle."""
        await report_agent_status(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            status="idle",
            message=message,
        )

    async def report_busy(
        self,
        task_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Report that this agent is busy."""
        await report_agent_status(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            status="busy",
            task_id=task_id,
            message=message,
        )

    async def report_stopped(self, message: Optional[str] = None) -> None:
        """Report that this agent has stopped."""
        await report_agent_status(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            status="stopped",
            message=message,
        )

    # --- Delegation Methods (for Orchestrator) ---

    async def delegate_to_lead(
        self,
        lead: LeadType,
        task: str,
        context: Optional[dict[str, Any]] = None,
        priority: Priority = Priority.NORMAL,
        timeout: float = 120.0,
    ) -> DelegationResult:
        """Delegate a task to a Lead (use from Orchestrator)."""
        return await delegate_to_lead(
            lead=lead,
            task=task,
            context=context,
            priority=priority,
            timeout=timeout,
            correlation_id=self.correlation_id,
        )

    # --- Assignment Methods (for Leads) ---

    async def assign_worker(
        self,
        worker: WorkerType,
        subtask: str,
        context: Optional[dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        timeout: float = 60.0,
    ) -> WorkerResult:
        """Assign a subtask to a Worker (use from Lead)."""
        return await assign_to_worker(
            worker=worker,
            subtask=subtask,
            context=context,
            parent_task_id=parent_task_id,
            priority=priority,
            timeout=timeout,
            correlation_id=self.correlation_id,
            source=self.agent_name,
        )

    # --- Completion Methods ---

    async def report_complete(
        self,
        task_id: str,
        result: str,
        files_modified: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Report task completion (use from Lead or Worker)."""
        if self.agent_type == "lead":
            await report_lead_complete(
                task_id=task_id,
                result=result,
                files_modified=files_modified,
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )
        else:
            await report_worker_complete(
                task_id=task_id,
                result=result,
                files_modified=files_modified,
                metadata=metadata,
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )

    async def report_error(
        self,
        task_id: str,
        error: str,
        recoverable: bool = True,
    ) -> None:
        """Report an error (use from Lead or Worker)."""
        if self.agent_type == "lead":
            await report_lead_error(
                task_id=task_id,
                error=error,
                recoverable=recoverable,
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )
        else:
            await report_worker_error(
                task_id=task_id,
                error=error,
                recoverable=recoverable,
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )

    # --- Progress Methods ---

    async def report_progress(
        self,
        task_id: str,
        progress: float,
        message: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Report progress (use from Lead or Worker)."""
        if self.agent_type == "lead":
            await report_lead_progress(
                task_id=task_id,
                progress=progress,
                message=message,
                subtasks_total=kwargs.get("subtasks_total"),
                subtasks_complete=kwargs.get("subtasks_complete"),
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )
        else:
            await report_worker_progress(
                task_id=task_id,
                progress=progress,
                message=message,
                current_step=kwargs.get("current_step"),
                correlation_id=self.correlation_id,
                source=self.agent_name,
            )
