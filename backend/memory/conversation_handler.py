"""Conversation Memory Handler for Emperor AI Assistant.

Handles automatic memory extraction from conversations.
Processes chat sessions and extracts facts, preferences, and context
using mem0's intelligent extraction capabilities.

Supports mode-based filtering (work, personal, general).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .memory_service import MemoryService, MemoryResult
from .user_profile import Mode, MODE_CONTEXTS, get_current_mode


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
        context: Optional[str] = None,
        agent: Optional[str] = None,
        source: Optional[str] = None,
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
            context: Context mode ("work", "personal", "general").
                     Uses current mode if not specified.
            agent: The agent storing this memory (e.g., "code_lead", "research_lead").
            source: The activity that produced this memory (e.g., "chat", "code_review").

        Returns:
            Dict containing extraction results from mem0.

        Example:
            >>> result = handler.process_conversation(
            ...     messages=[
            ...         {"role": "user", "content": "I always use TypeScript"},
            ...         {"role": "assistant", "content": "TypeScript is great!"}
            ...     ],
            ...     user_id="user123",
            ...     session_id="session_abc",
            ...     context="work",
            ...     agent="code_lead",
            ...     source="code_review"
            ... )
        """
        if not messages:
            return {"status": "empty", "extracted": []}

        # Format conversation for mem0
        formatted = self._format_conversation(messages)

        # Determine context mode
        if context is None:
            context = get_current_mode().value

        # Build metadata with context
        memory_metadata = {
            "type": "conversation",
            "context": context,  # Store the mode context
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
            agent=agent,
            source=source,
        )

        return result

    def process_message(
        self,
        role: str,
        content: str,
        user_id: str,
        session_id: Optional[str] = None,
        agent: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a single message and extract memories.

        Convenience method for processing individual messages
        instead of full conversations.

        Args:
            role: The message role ('user' or 'assistant').
            content: The message content.
            user_id: User identifier for memory isolation.
            session_id: Optional session identifier.
            agent: The agent storing this memory (e.g., "code_lead").
            source: The activity that produced this memory.

        Returns:
            Dict containing extraction results from mem0.
        """
        return self.process_conversation(
            messages=[{"role": role, "content": content}],
            user_id=user_id,
            session_id=session_id,
            agent=agent,
            source=source,
        )

    def get_relevant_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        filter_by_mode: bool = True,
    ) -> str:
        """Get relevant memories formatted as context for prompts.

        Searches memories and formats them as a string suitable
        for injection into system prompts or context.

        Filters results based on current mode:
        - WORK mode: returns work + general memories
        - PERSONAL mode: returns personal + general memories
        - GENERAL mode: returns all memories

        Args:
            query: The search query (usually the user's current message).
            user_id: User identifier for memory isolation.
            limit: Maximum number of memories to include.
            filter_by_mode: Whether to filter by current mode (default True).

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
        # Fetch extra results to account for filtering
        fetch_limit = limit * 2 if filter_by_mode else limit

        memories = self.memory.search(
            query=query,
            user_id=user_id,
            limit=fetch_limit,
        )

        if not memories:
            return ""

        # Filter by mode if enabled
        if filter_by_mode:
            memories = self._filter_by_mode(memories)

        # Limit to requested count
        memories = memories[:limit]

        return self._format_context(memories)

    def get_relevant_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        min_score: float = 0.0,
        filter_by_mode: bool = True,
        agent: Optional[str] = None,
    ) -> List[MemoryResult]:
        """Get relevant memories as MemoryResult objects.

        Similar to get_relevant_context but returns structured
        objects instead of formatted string.

        Filters results based on current mode:
        - WORK mode: returns work + general memories
        - PERSONAL mode: returns personal + general memories
        - GENERAL mode: returns all memories

        Args:
            query: The search query.
            user_id: User identifier for memory isolation.
            limit: Maximum number of memories to return.
            min_score: Minimum relevance score threshold (0.0 to 1.0).
            filter_by_mode: Whether to filter by current mode (default True).
            agent: Filter to memories from specific agent (e.g., "code_lead").

        Returns:
            List of MemoryResult objects filtered by score, mode, and agent.
        """
        # Fetch extra results to account for filtering
        fetch_limit = limit * 3 if (filter_by_mode or agent) else limit

        memories = self.memory.search(
            query=query,
            user_id=user_id,
            limit=fetch_limit,
        )

        # Filter by agent if specified
        if agent:
            memories = [m for m in memories if m.metadata.get("agent") == agent]

        # Filter by mode if enabled
        if filter_by_mode:
            memories = self._filter_by_mode(memories)

        # Filter by minimum score
        if min_score > 0:
            memories = [m for m in memories if m.relevance_score >= min_score]

        # Limit to requested count
        return memories[:limit]

    def get_agent_memories(
        self,
        agent: str,
        user_id: str,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryResult]:
        """Get memories created by a specific agent.

        Useful for Domain Leads to retrieve their own stored knowledge.

        Args:
            agent: The agent identifier (e.g., "code_lead", "research_lead").
            user_id: User identifier for memory isolation.
            query: Optional search query to filter by relevance.
            limit: Maximum number of memories to return.

        Returns:
            List of MemoryResult objects from the specified agent.

        Example:
            >>> memories = handler.get_agent_memories(
            ...     agent="code_lead",
            ...     user_id="emperor_user",
            ...     query="python testing"
            ... )
        """
        if query:
            return self.memory.search_by_agent(
                query=query,
                agent=agent,
                user_id=user_id,
                limit=limit,
            )
        else:
            # Get all memories and filter by agent
            all_memories = self.memory.get_all(user_id=user_id)
            agent_memories = [
                m for m in all_memories
                if m.get("metadata", {}).get("agent") == agent
            ]
            return agent_memories[:limit]

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

    def _filter_by_mode(self, memories: List[MemoryResult]) -> List[MemoryResult]:
        """Filter memories based on current mode.

        Mode filtering rules:
        - WORK mode: returns memories with context in ["work", "general"]
        - PERSONAL mode: returns memories with context in ["personal", "general"]
        - GENERAL mode: returns all memories

        Args:
            memories: List of MemoryResult objects to filter.

        Returns:
            Filtered list of MemoryResult objects.
        """
        current_mode = get_current_mode()
        allowed_contexts = MODE_CONTEXTS.get(current_mode, ["work", "personal", "general"])

        filtered = []
        for mem in memories:
            # Get the context from metadata, default to "general"
            mem_context = mem.metadata.get("context", "general")

            # Include if context is in allowed list
            if mem_context in allowed_contexts:
                filtered.append(mem)

        return filtered

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
