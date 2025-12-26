"""UI Event Streamer for Emperor AI Assistant.

This module bridges the internal Event Bus to the frontend WebSocket connection.
It subscribes to relevant events and transforms them into UI-friendly formats
that can be displayed to the user in real-time.

Features:
- Selective event forwarding (only UI-relevant events)
- Event transformation for frontend consumption
- Rate limiting to prevent UI flooding
- Connection-aware broadcasting
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional
from uuid import uuid4

from config import get_logger
from .events import Event, EventType, EventCategory, Priority

logger = get_logger(__name__)


# Type for broadcast function
BroadcastFunc = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


@dataclass
class UIEvent:
    """A simplified event structure for the frontend."""

    event_id: str
    event_type: str
    source: str
    timestamp: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


@dataclass
class RateLimiter:
    """Simple rate limiter for event types."""

    min_interval_ms: int = 100  # Minimum ms between events of same type
    _last_sent: dict[str, datetime] = field(default_factory=dict)

    def should_send(self, event_type: str) -> bool:
        """Check if enough time has passed to send another event of this type."""
        now = datetime.now(timezone.utc)
        last = self._last_sent.get(event_type)

        if not last:
            self._last_sent[event_type] = now
            return True

        elapsed_ms = (now - last).total_seconds() * 1000
        if elapsed_ms >= self.min_interval_ms:
            self._last_sent[event_type] = now
            return True

        return False

    def force_send(self, event_type: str) -> None:
        """Mark an event type as just sent (for important events)."""
        self._last_sent[event_type] = datetime.now(timezone.utc)


class UIEventStreamer:
    """
    Bridges the Event Bus to the frontend WebSocket.

    This class subscribes to relevant events from the Event Bus and
    transforms them into a format suitable for the frontend UI.

    Features:
    - Selective event forwarding based on UI relevance
    - Event transformation for consistent frontend format
    - Rate limiting for progress events (prevent flooding)
    - Support for multiple event categories

    Example:
        from process_manager import get_event_bus, UIEventStreamer
        from api.websocket import manager

        bus = get_event_bus()
        streamer = UIEventStreamer(bus, manager.broadcast)
        await streamer.start()
    """

    # Event types that should be forwarded to the UI
    UI_RELEVANT_EVENTS = {
        # Agent status events
        EventType.AGENT_STARTED,
        EventType.AGENT_IDLE,
        EventType.AGENT_BUSY,
        EventType.AGENT_STOPPED,

        # Lead events
        EventType.LEAD_RECEIVED,
        EventType.LEAD_PLANNING,
        EventType.LEAD_PROGRESS,
        EventType.LEAD_COMPLETE,
        EventType.LEAD_ERROR,

        # Worker events
        EventType.WORKER_START,
        EventType.WORKER_PROGRESS,
        EventType.WORKER_COMPLETE,
        EventType.WORKER_ERROR,

        # Tool events
        EventType.TOOL_EXECUTE,
        EventType.TOOL_PROGRESS,
        EventType.TOOL_RESULT,
        EventType.TOOL_ERROR,

        # Approval events
        EventType.APPROVAL_REQUEST,
        EventType.APPROVAL_GRANTED,
        EventType.APPROVAL_DENIED,
        EventType.APPROVAL_TIMEOUT,

        # System events
        EventType.SYSTEM_ERROR,
    }

    # Events that bypass rate limiting (always sent immediately)
    PRIORITY_EVENTS = {
        EventType.APPROVAL_REQUEST,
        EventType.APPROVAL_GRANTED,
        EventType.APPROVAL_DENIED,
        EventType.WORKER_COMPLETE,
        EventType.LEAD_COMPLETE,
        EventType.SYSTEM_ERROR,
        EventType.TOOL_ERROR,
        EventType.WORKER_ERROR,
        EventType.LEAD_ERROR,
    }

    # Events that are rate limited (progress events)
    RATE_LIMITED_EVENTS = {
        EventType.WORKER_PROGRESS,
        EventType.LEAD_PROGRESS,
        EventType.TOOL_PROGRESS,
    }

    def __init__(
        self,
        event_bus: "EventBus",
        broadcast_func: BroadcastFunc,
        rate_limit_ms: int = 100,
    ):
        """
        Initialize the UI Event Streamer.

        Args:
            event_bus: The event bus to subscribe to
            broadcast_func: Async function to broadcast events to frontend
            rate_limit_ms: Minimum ms between rate-limited events
        """
        from .event_bus import EventBus

        self._bus: EventBus = event_bus
        self._broadcast = broadcast_func
        self._rate_limiter = RateLimiter(min_interval_ms=rate_limit_ms)
        self._subscription_ids: list[str] = []
        self._running = False

        logger.debug("UIEventStreamer initialized")

    async def start(self) -> None:
        """Start streaming events to the UI."""
        if self._running:
            logger.warning("UIEventStreamer already running")
            return

        # Subscribe to all UI-relevant event types
        for event_type in self.UI_RELEVANT_EVENTS:
            sub_id = self._bus.subscribe(event_type, self._handle_event)
            self._subscription_ids.append(sub_id)

        self._running = True
        logger.info(f"UIEventStreamer started with {len(self._subscription_ids)} subscriptions")

    async def stop(self) -> None:
        """Stop streaming events to the UI."""
        if not self._running:
            return

        # Unsubscribe from all events
        for sub_id in self._subscription_ids:
            self._bus.unsubscribe(sub_id)

        self._subscription_ids.clear()
        self._running = False
        logger.info("UIEventStreamer stopped")

    async def _handle_event(self, event: Event) -> None:
        """
        Handle an event from the Event Bus.

        Transforms the event and broadcasts to frontend if appropriate.

        Args:
            event: The event from the Event Bus
        """
        # Check rate limiting for progress events
        if event.type in self.RATE_LIMITED_EVENTS:
            if not self._rate_limiter.should_send(event.type.value):
                return  # Skip this event due to rate limiting

        # Transform to UI event format
        ui_event = self._transform_event(event)

        # Broadcast to frontend
        try:
            await self._broadcast(ui_event.to_dict())
            logger.debug(f"Broadcasted UI event: {ui_event.event_type}")
        except Exception as e:
            logger.error(f"Failed to broadcast UI event: {e}")

    def _transform_event(self, event: Event) -> UIEvent:
        """
        Transform an internal Event to a UIEvent.

        Maps internal event types to frontend-friendly types and
        extracts relevant payload data.

        Args:
            event: The internal event

        Returns:
            A UIEvent suitable for frontend consumption
        """
        # Map internal event type to UI event type
        ui_event_type = self._map_event_type(event.type)

        # Transform payload based on event type
        ui_payload = self._transform_payload(event)

        return UIEvent(
            event_id=f"ui_{uuid4().hex[:12]}",
            event_type=ui_event_type,
            source=event.source,
            timestamp=event.timestamp.isoformat(),
            payload=ui_payload,
        )

    def _map_event_type(self, event_type: EventType) -> str:
        """Map internal event type to frontend event type."""

        # Agent status events -> agent.status
        if event_type in {
            EventType.AGENT_STARTED,
            EventType.AGENT_IDLE,
            EventType.AGENT_BUSY,
            EventType.AGENT_STOPPED,
        }:
            return "agent.status"

        # Tool events -> tool.* (keep same structure)
        if event_type == EventType.TOOL_EXECUTE:
            return "tool.execute"
        if event_type == EventType.TOOL_PROGRESS:
            return "tool.progress"
        if event_type == EventType.TOOL_RESULT:
            return "tool.result"
        if event_type == EventType.TOOL_ERROR:
            return "tool.error"

        # Approval events -> approval.* (keep same structure)
        if event_type == EventType.APPROVAL_REQUEST:
            return "approval.request"
        if event_type == EventType.APPROVAL_GRANTED:
            return "approval.response"
        if event_type == EventType.APPROVAL_DENIED:
            return "approval.response"
        if event_type == EventType.APPROVAL_TIMEOUT:
            return "approval.timeout"

        # Lead events -> lead.*
        if event_type == EventType.LEAD_RECEIVED:
            return "lead.received"
        if event_type == EventType.LEAD_PLANNING:
            return "lead.planning"
        if event_type == EventType.LEAD_PROGRESS:
            return "lead.progress"
        if event_type == EventType.LEAD_COMPLETE:
            return "lead.complete"
        if event_type == EventType.LEAD_ERROR:
            return "lead.error"

        # Worker events -> worker.*
        if event_type == EventType.WORKER_START:
            return "worker.start"
        if event_type == EventType.WORKER_PROGRESS:
            return "worker.progress"
        if event_type == EventType.WORKER_COMPLETE:
            return "worker.complete"
        if event_type == EventType.WORKER_ERROR:
            return "worker.error"

        # System events
        if event_type == EventType.SYSTEM_ERROR:
            return "system.error"

        # Default: use the original value
        return event_type.value

    def _transform_payload(self, event: Event) -> dict[str, Any]:
        """
        Transform event payload for frontend consumption.

        Extracts and formats relevant data from the event payload.

        Args:
            event: The internal event

        Returns:
            Transformed payload dictionary
        """
        payload = dict(event.data)  # Copy original data

        # Add correlation_id if present (useful for tracking related events)
        if event.correlation_id:
            payload["correlation_id"] = event.correlation_id

        # Add priority for high-priority events
        if event.priority in {Priority.HIGH, Priority.CRITICAL}:
            payload["priority"] = event.priority.value

        # Transform based on event type
        if event.type in {EventType.AGENT_STARTED, EventType.AGENT_IDLE,
                          EventType.AGENT_BUSY, EventType.AGENT_STOPPED}:
            # Add status string for agent status events
            status_map = {
                EventType.AGENT_STARTED: "started",
                EventType.AGENT_IDLE: "idle",
                EventType.AGENT_BUSY: "busy",
                EventType.AGENT_STOPPED: "stopped",
            }
            payload["status"] = status_map.get(event.type, "unknown")

        elif event.type in {EventType.APPROVAL_GRANTED, EventType.APPROVAL_DENIED}:
            # Add approved boolean for approval responses
            payload["approved"] = event.type == EventType.APPROVAL_GRANTED

        elif event.type in {EventType.WORKER_PROGRESS, EventType.LEAD_PROGRESS}:
            # Ensure progress is between 0 and 1
            if "progress" in payload:
                payload["progress"] = max(0.0, min(1.0, float(payload["progress"])))

        return payload

    @property
    def is_running(self) -> bool:
        """Check if the streamer is running."""
        return self._running

    @property
    def subscription_count(self) -> int:
        """Get the number of active subscriptions."""
        return len(self._subscription_ids)


# =============================================================================
# Singleton and Factory Functions
# =============================================================================

_ui_streamer: Optional[UIEventStreamer] = None


def get_ui_streamer() -> Optional[UIEventStreamer]:
    """Get the singleton UI Event Streamer instance."""
    return _ui_streamer


async def init_ui_streamer(
    event_bus: "EventBus",
    broadcast_func: BroadcastFunc,
    rate_limit_ms: int = 100,
) -> UIEventStreamer:
    """
    Initialize and start the UI Event Streamer.

    Args:
        event_bus: The event bus to subscribe to
        broadcast_func: Async function to broadcast events
        rate_limit_ms: Minimum ms between rate-limited events

    Returns:
        The initialized UIEventStreamer
    """
    global _ui_streamer

    if _ui_streamer is not None:
        logger.warning("UIEventStreamer already initialized")
        return _ui_streamer

    _ui_streamer = UIEventStreamer(
        event_bus=event_bus,
        broadcast_func=broadcast_func,
        rate_limit_ms=rate_limit_ms,
    )
    await _ui_streamer.start()

    return _ui_streamer


async def shutdown_ui_streamer() -> None:
    """Stop and cleanup the UI Event Streamer."""
    global _ui_streamer

    if _ui_streamer is not None:
        await _ui_streamer.stop()
        _ui_streamer = None
