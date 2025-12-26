"""Event Bus implementation for Emperor AI Assistant.

This module provides the central pub/sub event bus that enables
loose coupling between all system components:
- Orchestrator
- Domain Leads
- Workers
- Tools
- UI

Features:
- Async event processing
- Wildcard subscriptions
- Request/response pattern
- Middleware support
- Event history for debugging
"""

import asyncio
import fnmatch
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional, Union
from uuid import uuid4

from config import get_logger
from .events import Event, EventType, Priority

logger = get_logger(__name__)


# Type aliases
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]
Middleware = Callable[[Event, Callable], Coroutine[Any, Any, None]]


@dataclass
class Subscription:
    """Represents a subscription to an event type."""
    pattern: str                    # Event pattern (e.g., "worker.*" or "*")
    handler: EventHandler           # Handler function
    id: str = field(default_factory=lambda: f"sub_{uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def matches(self, event_type: str) -> bool:
        """Check if this subscription matches an event type."""
        if self.pattern == "*":
            return True
        if self.pattern == event_type:
            return True
        # Support wildcard patterns like "worker.*"
        return fnmatch.fnmatch(event_type, self.pattern)


@dataclass
class PendingResponse:
    """Tracks a pending request waiting for a response."""
    correlation_id: str
    response_types: set[EventType]
    future: asyncio.Future
    timeout: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """
    Central event bus for component communication.

    Provides publish/subscribe functionality with:
    - Async event processing
    - Wildcard subscriptions (*, category.*)
    - Request/response pattern
    - Middleware pipeline
    - Event history

    Example:
        bus = EventBus()

        @bus.on(EventType.WORKER_COMPLETE)
        async def handle_completion(event):
            print(f"Worker completed: {event.data}")

        await bus.start()
        await bus.publish(Event(...))
    """

    def __init__(
        self,
        history_size: int = 1000,
        max_queue_size: int = 10000,
    ):
        """
        Initialize the event bus.

        Args:
            history_size: Number of events to keep in history
            max_queue_size: Maximum queue size (0 = unlimited)
        """
        # Subscriptions: pattern -> list of subscriptions
        self._subscriptions: dict[str, list[Subscription]] = {}

        # Event queue
        self._queue: asyncio.Queue[Event] = asyncio.Queue(
            maxsize=max_queue_size if max_queue_size > 0 else 0
        )

        # Middleware pipeline
        self._middleware: list[Middleware] = []

        # Event history (circular buffer)
        self._history: deque[Event] = deque(maxlen=history_size)

        # Pending responses for request/response pattern
        self._pending_responses: dict[str, PendingResponse] = {}

        # Processing state
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_dropped": 0,
            "handlers_called": 0,
            "errors": 0,
        }

        logger.debug("EventBus initialized")

    # =========================================================================
    # Subscription Methods
    # =========================================================================

    def subscribe(
        self,
        pattern: Union[str, EventType],
        handler: EventHandler,
    ) -> str:
        """
        Subscribe a handler to an event pattern.

        Args:
            pattern: Event type, pattern with wildcards, or "*" for all
            handler: Async function to handle events

        Returns:
            Subscription ID for later unsubscription

        Example:
            # Subscribe to specific event
            bus.subscribe(EventType.WORKER_COMPLETE, my_handler)

            # Subscribe to all worker events
            bus.subscribe("worker.*", my_handler)

            # Subscribe to all events
            bus.subscribe("*", audit_logger)
        """
        pattern_str = pattern.value if isinstance(pattern, EventType) else pattern

        subscription = Subscription(pattern=pattern_str, handler=handler)

        if pattern_str not in self._subscriptions:
            self._subscriptions[pattern_str] = []

        self._subscriptions[pattern_str].append(subscription)

        logger.debug(f"Subscribed {handler.__name__} to '{pattern_str}' (id: {subscription.id})")

        return subscription.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription by ID.

        Args:
            subscription_id: ID returned from subscribe()

        Returns:
            True if removed, False if not found
        """
        for pattern, subs in self._subscriptions.items():
            for sub in subs:
                if sub.id == subscription_id:
                    subs.remove(sub)
                    logger.debug(f"Unsubscribed {subscription_id} from '{pattern}'")
                    return True

        return False

    def on(
        self,
        pattern: Union[str, EventType],
    ) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator to subscribe a handler to an event pattern.

        Args:
            pattern: Event type or pattern

        Returns:
            Decorator function

        Example:
            @bus.on(EventType.WORKER_COMPLETE)
            async def handle_completion(event):
                print(f"Completed: {event.data}")

            @bus.on("worker.*")
            async def track_workers(event):
                update_ui(event)
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(pattern, handler)
            return handler
        return decorator

    def _get_handlers(self, event_type: str) -> list[EventHandler]:
        """Get all handlers that match an event type."""
        handlers = []

        for pattern, subs in self._subscriptions.items():
            for sub in subs:
                if sub.matches(event_type):
                    handlers.append(sub.handler)

        return handlers

    # =========================================================================
    # Publishing Methods
    # =========================================================================

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        The event is added to the queue and processed asynchronously.
        This method returns immediately without waiting for handlers.

        Args:
            event: The event to publish
        """
        try:
            # Add to queue (non-blocking with timeout)
            await asyncio.wait_for(
                self._queue.put(event),
                timeout=5.0,
            )

            self._stats["events_published"] += 1
            logger.debug(f"Published: {event.type.value} (id: {event.id})")

        except asyncio.TimeoutError:
            self._stats["events_dropped"] += 1
            logger.error(f"Event queue full, dropped: {event.type.value}")

    async def publish_sync(self, event: Event) -> None:
        """
        Publish an event and wait for all handlers to complete.

        Unlike publish(), this waits for all handlers to finish.
        Use sparingly as it can block the caller.

        Args:
            event: The event to publish
        """
        await self._dispatch(event)
        self._stats["events_published"] += 1

    async def publish_and_wait(
        self,
        event: Event,
        response_types: Union[EventType, list[EventType]],
        timeout: float = 30.0,
    ) -> Optional[Event]:
        """
        Publish an event and wait for a response event.

        Useful for request/response patterns like approval requests.

        Args:
            event: The event to publish
            response_types: Event type(s) to wait for
            timeout: Timeout in seconds

        Returns:
            The response event, or None if timeout

        Example:
            response = await bus.publish_and_wait(
                event=approval_request,
                response_types=[EventType.APPROVAL_GRANTED, EventType.APPROVAL_DENIED],
                timeout=60,
            )
            if response and response.type == EventType.APPROVAL_GRANTED:
                proceed()
        """
        # Ensure we have a correlation ID
        if not event.correlation_id:
            event = event.with_correlation(f"cor_{uuid4().hex[:12]}")

        # Normalize response types to set
        if isinstance(response_types, EventType):
            response_types = {response_types}
        else:
            response_types = set(response_types)

        # Create pending response tracker
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        pending = PendingResponse(
            correlation_id=event.correlation_id,
            response_types=response_types,
            future=future,
            timeout=timeout,
        )

        self._pending_responses[event.correlation_id] = pending

        try:
            # Publish the event
            await self.publish(event)

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to {event.id}")
            return None

        finally:
            # Clean up
            self._pending_responses.pop(event.correlation_id, None)

    def _check_pending_responses(self, event: Event) -> None:
        """Check if event satisfies any pending responses."""
        if not event.correlation_id:
            return

        pending = self._pending_responses.get(event.correlation_id)
        if not pending:
            return

        if event.type in pending.response_types:
            if not pending.future.done():
                pending.future.set_result(event)

    # =========================================================================
    # Middleware
    # =========================================================================

    def use(self, middleware: Middleware) -> None:
        """
        Add middleware to the processing pipeline.

        Middleware is called for every event before handlers.
        It can modify events, filter them, or add logging.

        Args:
            middleware: Async function (event, next) -> None

        Example:
            async def logging_middleware(event, next):
                logger.info(f"Event: {event.type}")
                await next(event)
                logger.info(f"Processed: {event.type}")

            bus.use(logging_middleware)
        """
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")

    async def _apply_middleware(
        self,
        event: Event,
        final: Callable[[Event], Coroutine],
    ) -> None:
        """Apply middleware pipeline to an event."""

        async def create_next(index: int) -> Callable:
            async def next_fn(evt: Event) -> None:
                if index < len(self._middleware):
                    await self._middleware[index](evt, await create_next(index + 1))
                else:
                    await final(evt)
            return next_fn

        if self._middleware:
            first_next = await create_next(0)
            await self._middleware[0](event, first_next)
        else:
            await final(event)

    # =========================================================================
    # Event Processing
    # =========================================================================

    async def start(self) -> None:
        """Start the event processing loop."""
        if self._running:
            logger.warning("EventBus already running")
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus started")

    async def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the event processing loop.

        Args:
            timeout: Time to wait for pending events
        """
        if not self._running:
            return

        self._running = False

        # Wait for queue to drain (with timeout)
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout draining queue, {self._queue.qsize()} events remaining")

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("EventBus stopped")

    async def _process_loop(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the event
                try:
                    await self._dispatch(event)
                    self._stats["events_processed"] += 1
                except Exception as e:
                    self._stats["errors"] += 1
                    logger.error(f"Error processing {event.type.value}: {e}", exc_info=True)
                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event loop error: {e}", exc_info=True)

    async def _dispatch(self, event: Event) -> None:
        """Dispatch an event to all matching handlers."""

        # Add to history
        self._history.append(event)

        # Check for pending responses
        self._check_pending_responses(event)

        # Get matching handlers
        event_type_str = event.type.value if isinstance(event.type, EventType) else event.type
        handlers = self._get_handlers(event_type_str)

        if not handlers:
            logger.debug(f"No handlers for: {event_type_str}")
            return

        # Apply middleware and call handlers
        async def call_handlers(evt: Event) -> None:
            # Call all handlers concurrently
            tasks = [self._call_handler(h, evt) for h in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

        await self._apply_middleware(event, call_handlers)

    async def _call_handler(self, handler: EventHandler, event: Event) -> None:
        """Call a single handler with error handling."""
        try:
            await handler(event)
            self._stats["handlers_called"] += 1
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(
                f"Handler {handler.__name__} error for {event.type.value}: {e}",
                exc_info=True
            )

    # =========================================================================
    # History and Queries
    # =========================================================================

    def get_history(self, limit: int = 100) -> list[Event]:
        """
        Get recent events from history.

        Args:
            limit: Maximum events to return

        Returns:
            List of recent events (newest last)
        """
        return list(self._history)[-limit:]

    def get_by_correlation(self, correlation_id: str) -> list[Event]:
        """
        Get all events with a correlation ID.

        Args:
            correlation_id: Correlation ID to search for

        Returns:
            List of matching events
        """
        return [e for e in self._history if e.correlation_id == correlation_id]

    def get_by_type(
        self,
        event_type: Union[str, EventType],
        limit: int = 100,
    ) -> list[Event]:
        """
        Get events of a specific type.

        Args:
            event_type: Event type to filter by
            limit: Maximum events to return

        Returns:
            List of matching events
        """
        type_str = event_type.value if isinstance(event_type, EventType) else event_type
        matches = [e for e in self._history if e.type.value == type_str]
        return matches[-limit:]

    def get_by_source(self, source: str, limit: int = 100) -> list[Event]:
        """
        Get events from a specific source.

        Args:
            source: Source to filter by
            limit: Maximum events to return

        Returns:
            List of matching events
        """
        matches = [e for e in self._history if e.source == source]
        return matches[-limit:]

    # =========================================================================
    # Properties and Stats
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """Check if the event bus is running."""
        return self._running

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def subscription_count(self) -> int:
        """Get total number of subscriptions."""
        return sum(len(subs) for subs in self._subscriptions.values())

    @property
    def stats(self) -> dict[str, int]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "queue_size": self.queue_size,
            "subscriptions": self.subscription_count,
            "history_size": len(self._history),
        }

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()
        logger.debug("Event history cleared")

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        for key in self._stats:
            self._stats[key] = 0
        logger.debug("Event stats reset")


# =============================================================================
# Singleton Instance
# =============================================================================

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the singleton event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def init_event_bus() -> EventBus:
    """Initialize and start the event bus."""
    bus = get_event_bus()
    if not bus.is_running:
        await bus.start()
    return bus


async def shutdown_event_bus() -> None:
    """Stop the event bus."""
    global _event_bus
    if _event_bus and _event_bus.is_running:
        await _event_bus.stop()
