"""Memory Service for Emperor AI Assistant.

Central service wrapping mem0 for all memory operations.
Provides a clean interface for storing, searching, and managing memories.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from mem0 import Memory

from .config import get_config, validate_config


@dataclass
class MemoryResult:
    """Structured memory retrieval result."""

    id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat(),
        }


class MemoryService:
    """Central memory service using mem0.

    Provides a unified interface for memory operations:
    - add: Store new memories (auto-extracts facts)
    - search: Semantic similarity search
    - get_all: List all memories for a user
    - update: Modify existing memories
    - delete: Remove specific memories
    - delete_all: Clear all user memories
    - get_history: Version history for a memory

    Example:
        >>> service = MemoryService()
        >>> service.add("I prefer Python 3.11", user_id="user123")
        >>> results = service.search("programming language", user_id="user123")
        >>> print(results[0].content)
        "I prefer Python 3.11"
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, use_local: bool = True):
        """Initialize the memory service.

        Args:
            config: Custom mem0 configuration. If None, uses default based on use_local.
            use_local: If True and config is None, uses local config (no external APIs).
        """
        if config is None:
            config = get_config(use_local=use_local)

        # Validate configuration if using full config
        if not use_local and config is not None:
            validate_config(config)

        self.memory = Memory.from_config(config)
        self._default_user_id = "default"

    def set_default_user(self, user_id: str) -> None:
        """Set the default user context for operations.

        Args:
            user_id: The user ID to use when not explicitly provided.
        """
        self._default_user_id = user_id

    def _get_user_id(self, user_id: Optional[str]) -> str:
        """Get the user ID, falling back to default if not provided."""
        return user_id or self._default_user_id

    def add(
        self,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        agent: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a memory.

        mem0 automatically:
        - Extracts facts and entities from the content
        - Builds knowledge graph relationships (v1.1)
        - Handles deduplication of similar memories
        - Updates existing memories if contradicting info found

        Args:
            content: The text content to remember.
            user_id: User identifier for memory isolation.
            metadata: Optional metadata (category, tags, etc.).
            agent: The agent that created this memory (e.g., "code_lead", "research_lead").
            source: The activity that produced this memory (e.g., "code_analysis", "web_search").

        Returns:
            Dict containing the new memory ID and extracted memories.

        Example:
            >>> result = service.add(
            ...     "User prefers pytest over unittest",
            ...     user_id="emperor_user",
            ...     metadata={"category": "preference"},
            ...     agent="code_lead",
            ...     source="code_review"
            ... )
            >>> print(result["id"])
            "mem_abc123"
        """
        uid = self._get_user_id(user_id)

        # Build metadata with agent/source tags
        meta = metadata.copy() if metadata else {}
        if agent:
            meta["agent"] = agent
        if source:
            meta["source"] = source

        return self.memory.add(
            content,
            user_id=uid,
            metadata=meta,
        )

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryResult]:
        """Search memories with semantic similarity.

        Converts the query to a vector and finds similar memories
        using cosine similarity. Results are ranked by relevance.

        Args:
            query: The search query (natural language).
            user_id: User identifier for memory isolation.
            limit: Maximum number of results to return.

        Returns:
            List of MemoryResult objects sorted by relevance score.

        Example:
            >>> results = service.search("python preferences", user_id="user123")
            >>> for r in results:
            ...     print(f"{r.content} (score: {r.relevance_score:.2f})")
        """
        uid = self._get_user_id(user_id)
        response = self.memory.search(
            query,
            user_id=uid,
            limit=limit,
        )

        # mem0 returns {'results': [...]} or list directly depending on version
        if isinstance(response, dict):
            results = response.get("results", [])
        else:
            results = response

        return [
            MemoryResult(
                id=r.get("id", "") if isinstance(r, dict) else "",
                content=r.get("memory", "") if isinstance(r, dict) else str(r),
                metadata=r.get("metadata", {}) if isinstance(r, dict) else {},
                relevance_score=r.get("score", 0.0) if isinstance(r, dict) else 0.0,
                created_at=self._parse_datetime(r.get("created_at") if isinstance(r, dict) else None),
            )
            for r in results
        ]

    def search_by_agent(
        self,
        query: str,
        agent: str,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryResult]:
        """Search memories created by a specific agent.

        Args:
            query: The search query (natural language).
            agent: Filter to memories from this agent (e.g., "code_lead").
            user_id: User identifier for memory isolation.
            limit: Maximum number of results to return.

        Returns:
            List of MemoryResult objects from the specified agent.
        """
        results = self.search(query, user_id=user_id, limit=limit * 2)  # Get extra for filtering
        filtered = [r for r in results if r.metadata.get("agent") == agent]
        return filtered[:limit]

    def get_all(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all memories for a user.

        Args:
            user_id: User identifier for memory isolation.

        Returns:
            List of all memory dictionaries for the user.
        """
        uid = self._get_user_id(user_id)
        return self.memory.get_all(user_id=uid)

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID.

        Args:
            memory_id: The unique memory identifier.

        Returns:
            Memory dictionary if found, None otherwise.
        """
        try:
            return self.memory.get(memory_id)
        except Exception:
            return None

    def update(self, memory_id: str, content: str) -> Dict[str, Any]:
        """Update an existing memory.

        The previous version is preserved in history.

        Args:
            memory_id: The unique memory identifier.
            content: The new content for the memory.

        Returns:
            Dict containing the updated memory information.
        """
        return self.memory.update(memory_id, content)

    def delete(self, memory_id: str) -> bool:
        """Delete a specific memory.

        Args:
            memory_id: The unique memory identifier.

        Returns:
            True if deleted successfully, False otherwise.
        """
        try:
            self.memory.delete(memory_id)
            return True
        except Exception:
            return False

    def delete_all(self, user_id: Optional[str] = None) -> bool:
        """Delete all memories for a user.

        Args:
            user_id: User identifier for memory isolation.

        Returns:
            True if deleted successfully, False otherwise.
        """
        uid = self._get_user_id(user_id)
        try:
            self.memory.delete_all(user_id=uid)
            return True
        except Exception:
            return False

    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get version history of a memory.

        Shows all previous versions when a memory was updated.

        Args:
            memory_id: The unique memory identifier.

        Returns:
            List of historical versions, newest first.
        """
        try:
            return self.memory.history(memory_id)
        except Exception:
            return []

    def _parse_datetime(self, dt_str: Optional[str]) -> datetime:
        """Parse datetime string, returning now() if invalid."""
        if not dt_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()


# Module-level singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service(use_local: bool = True) -> MemoryService:
    """Get the memory service singleton.

    Args:
        use_local: If True, uses local config (no external APIs).
                   Only applies on first initialization.

    Returns:
        The shared MemoryService instance.
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(use_local=use_local)
    return _memory_service


def reset_memory_service() -> None:
    """Reset the memory service singleton.

    Useful for testing or reinitializing with different config.
    """
    global _memory_service
    _memory_service = None
