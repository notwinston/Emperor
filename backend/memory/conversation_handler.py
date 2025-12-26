"""Conversation Memory Handler for Emperor AI Assistant.

Handles automatic memory extraction from conversations.
Processes chat sessions and extracts facts, preferences, and context
using mem0's intelligent extraction capabilities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .memory_service import MemoryService, MemoryResult


class ConversationMemoryHandler:
    """Handles automatic memory extraction from conversations.

    This handler processes conversations and lets mem0 automatically
    extract important information like:
    - User preferences ("I prefer dark mode")
    - Facts ("My project uses Python 3.11")
    - Relationships ("My team lead is Sarah")
    - Instructions ("Always format code with black")

    Example:
        >>> handler = ConversationMemoryHandler(memory_service)
        >>> handler.process_conversation([
        ...     {"role": "user", "content": "I'm using React 18"},
        ...     {"role": "assistant", "content": "Great choice!"}
        ... ], user_id="user123")
        >>> context = handler.get_relevant_context("frontend", user_id="user123")
        >>> print(context)
        "Relevant memories:\\n- User is using React 18"
    """

    def __init__(self, memory_service: MemoryService):
        """Initialize the conversation handler.

        Args:
            memory_service: The MemoryService instance for storing memories.
        """
        self.memory = memory_service

    def process_conversation(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a conversation and extract memories.

        Takes a list of messages and feeds them to mem0, which
        automatically identifies and extracts important information.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles are typically 'user' and 'assistant'.
            user_id: User identifier for memory isolation.
            session_id: Optional session identifier for grouping.
            metadata: Optional additional metadata to store.

        Returns:
            Dict containing extraction results from mem0.

        Example:
            >>> result = handler.process_conversation(
            ...     messages=[
            ...         {"role": "user", "content": "I always use TypeScript"},
            ...         {"role": "assistant", "content": "TypeScript is great!"}
            ...     ],
            ...     user_id="user123",
            ...     session_id="session_abc"
            ... )
        """
        if not messages:
            return {"status": "empty", "extracted": []}

        # Format conversation for mem0
        formatted = self._format_conversation(messages)

        # Build metadata
        memory_metadata = {
            "type": "conversation",
            "session_id": session_id,
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        # Add to memory - mem0 handles extraction
        result = self.memory.add(
            content=formatted,
            user_id=user_id,
            metadata=memory_metadata,
        )

        return result

    def process_message(
        self,
        role: str,
        content: str,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a single message and extract memories.

        Convenience method for processing individual messages
        instead of full conversations.

        Args:
            role: The message role ('user' or 'assistant').
            content: The message content.
            user_id: User identifier for memory isolation.
            session_id: Optional session identifier.

        Returns:
            Dict containing extraction results from mem0.
        """
        return self.process_conversation(
            messages=[{"role": role, "content": content}],
            user_id=user_id,
            session_id=session_id,
        )

    def get_relevant_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> str:
        """Get relevant memories formatted as context for prompts.

        Searches memories and formats them as a string suitable
        for injection into system prompts or context.

        Args:
            query: The search query (usually the user's current message).
            user_id: User identifier for memory isolation.
            limit: Maximum number of memories to include.

        Returns:
            Formatted string of relevant memories, or empty string if none.

        Example:
            >>> context = handler.get_relevant_context(
            ...     query="How do I set up testing?",
            ...     user_id="user123"
            ... )
            >>> print(context)
            "Relevant memories:
            - User is working on a React 18 project
            - User prefers TypeScript
            - User uses Jest for testing"
        """
        memories = self.memory.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        if not memories:
            return ""

        return self._format_context(memories)

    def get_relevant_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> List[MemoryResult]:
        """Get relevant memories as MemoryResult objects.

        Similar to get_relevant_context but returns structured
        objects instead of formatted string.

        Args:
            query: The search query.
            user_id: User identifier for memory isolation.
            limit: Maximum number of memories to return.
            min_score: Minimum relevance score threshold (0.0 to 1.0).

        Returns:
            List of MemoryResult objects filtered by score.
        """
        memories = self.memory.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        # Filter by minimum score
        if min_score > 0:
            memories = [m for m in memories if m.relevance_score >= min_score]

        return memories

    def get_session_memories(
        self,
        session_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all memories from a specific session.

        Args:
            session_id: The session identifier to filter by.
            user_id: User identifier for memory isolation.

        Returns:
            List of memories from the specified session.
        """
        all_memories = self.memory.get_all(user_id=user_id)

        return [
            m for m in all_memories
            if m.get("metadata", {}).get("session_id") == session_id
        ]

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages into a single string.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Formatted string representation of the conversation.
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _format_context(self, memories: List[MemoryResult]) -> str:
        """Format memories as context string for prompts.

        Args:
            memories: List of MemoryResult objects.

        Returns:
            Formatted string suitable for prompt injection.
        """
        if not memories:
            return ""

        lines = ["Relevant memories:"]
        for mem in memories:
            # Include score if significant
            if mem.relevance_score >= 0.8:
                lines.append(f"- {mem.content}")
            else:
                lines.append(f"- {mem.content} (relevance: {mem.relevance_score:.0%})")

        return "\n".join(lines)

    def clear_session(self, session_id: str, user_id: str) -> int:
        """Clear all memories from a specific session.

        Args:
            session_id: The session identifier.
            user_id: User identifier for memory isolation.

        Returns:
            Number of memories deleted.
        """
        session_memories = self.get_session_memories(session_id, user_id)
        deleted = 0

        for mem in session_memories:
            if self.memory.delete(mem.get("id", "")):
                deleted += 1

        return deleted


# Module-level singleton
_conversation_handler: Optional[ConversationMemoryHandler] = None


def get_conversation_handler(
    memory_service: Optional[MemoryService] = None,
) -> ConversationMemoryHandler:
    """Get the conversation handler singleton.

    Args:
        memory_service: Optional MemoryService instance.
                        If None, uses get_memory_service().

    Returns:
        The shared ConversationMemoryHandler instance.
    """
    global _conversation_handler

    if _conversation_handler is None:
        if memory_service is None:
            from .memory_service import get_memory_service
            memory_service = get_memory_service()
        _conversation_handler = ConversationMemoryHandler(memory_service)

    return _conversation_handler


def reset_conversation_handler() -> None:
    """Reset the conversation handler singleton."""
    global _conversation_handler
    _conversation_handler = None
