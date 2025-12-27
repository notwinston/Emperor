"""Memory Integration for Emperor AI Assistant.

This module integrates the mem0-based memory system into the Orchestrator,
providing retrieval of relevant context before processing messages.

Uses the memory module (Part 9) for all storage and retrieval operations.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from config import get_logger

# Import from new mem0-based memory module
from memory import (
    initialize as init_memory,
    get_memory_service,
    get_conversation_handler,
    get_profile_manager,
    get_context,
    get_profile,
    add_memory,
    search_memory,
    set_mode,
    get_current_mode,
    Mode,
    MemoryResult,
)

logger = get_logger(__name__)


# =============================================================================
# Data Structures (kept for backwards compatibility)
# =============================================================================


@dataclass
class UserProfile:
    """User profile information."""

    name: Optional[str] = None
    skill_level: Optional[str] = None
    preferred_language: Optional[str] = None
    preferences: dict[str, Any] = field(default_factory=dict)
    timezone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_prompt_string(self) -> str:
        """Format profile for inclusion in prompt."""
        parts = []

        if self.name:
            parts.append(f"Name: {self.name}")
        if self.skill_level:
            parts.append(f"Skill level: {self.skill_level}")
        if self.preferred_language:
            parts.append(f"Preferred language: {self.preferred_language}")
        if self.preferences:
            prefs = ", ".join(f"{k}: {v}" for k, v in self.preferences.items())
            parts.append(f"Preferences: {prefs}")

        return "\n".join(parts) if parts else "No profile information"


@dataclass
class MemoryItem:
    """A single memory item."""

    key: str
    value: str
    category: str
    tags: list[str] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class SessionSummary:
    """Summary of a past session."""

    session_id: str
    timestamp: str
    summary: str
    topics: list[str] = field(default_factory=list)
    message_count: int = 0


@dataclass
class MemoryContext:
    """
    Complete memory context for a request.

    Retrieved before processing to provide relevant context
    to the LLM and Domain Leads.
    """

    user_profile: UserProfile = field(default_factory=UserProfile)
    relevant_facts: list[MemoryItem] = field(default_factory=list)
    user_memories: list[MemoryItem] = field(default_factory=list)
    recent_sessions: list[SessionSummary] = field(default_factory=list)
    project_context: dict[str, Any] = field(default_factory=dict)
    retrieval_time_ms: int = 0
    total_memories_searched: int = 0

    # New: mem0-based context strings
    memory_context_str: str = ""
    profile_context_str: str = ""
    current_mode: str = "general"

    def has_context(self) -> bool:
        """Check if any context was retrieved."""
        return (
            self.user_profile.name is not None
            or len(self.relevant_facts) > 0
            or len(self.user_memories) > 0
            or len(self.recent_sessions) > 0
            or bool(self.memory_context_str)
            or bool(self.profile_context_str)
        )

    def to_prompt_string(self) -> str:
        """Format memory context for inclusion in system prompt."""
        sections = []

        # Use mem0 context strings if available (preferred)
        if self.profile_context_str:
            sections.append(self.profile_context_str)

        if self.memory_context_str:
            sections.append(self.memory_context_str)

        # Fallback to legacy format if no mem0 context
        if not sections:
            # User profile section
            if self.user_profile.name or self.user_profile.preferences:
                sections.append(f"**User Profile:**\n{self.user_profile.to_prompt_string()}")

            # Relevant facts section
            if self.relevant_facts:
                facts = "\n".join(f"- {item.value}" for item in self.relevant_facts[:10])
                sections.append(f"**Relevant Information:**\n{facts}")

            # User memories section
            if self.user_memories:
                memories = "\n".join(f"- {item.value}" for item in self.user_memories[:5])
                sections.append(f"**User Preferences:**\n{memories}")

            # Project context section
            if self.project_context:
                ctx = "\n".join(f"- {k}: {v}" for k, v in self.project_context.items())
                sections.append(f"**Project Context:**\n{ctx}")

        if not sections:
            return ""

        return "\n\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_profile": {
                "name": self.user_profile.name,
                "skill_level": self.user_profile.skill_level,
                "preferred_language": self.user_profile.preferred_language,
                "preferences": self.user_profile.preferences,
            },
            "relevant_facts": [
                {"key": f.key, "value": f.value, "category": f.category}
                for f in self.relevant_facts
            ],
            "user_memories": [
                {"key": m.key, "value": m.value}
                for m in self.user_memories
            ],
            "memory_context": self.memory_context_str,
            "profile_context": self.profile_context_str,
            "current_mode": self.current_mode,
        }


# =============================================================================
# Memory Retriever (mem0-based)
# =============================================================================


class MemoryRetriever:
    """
    Retrieves relevant memory context for the Orchestrator.

    Uses mem0 for intelligent memory storage and retrieval.
    """

    def __init__(self, use_local: bool = True):
        """Initialize the memory retriever with mem0.

        Args:
            use_local: If True, uses local config (HuggingFace + ChromaDB).
        """
        self._initialized = False
        self._use_local = use_local
        self._initialize()

    def _initialize(self) -> None:
        """Initialize mem0 memory system."""
        if not self._initialized:
            try:
                init_memory(use_local=self._use_local)
                self._initialized = True
                logger.info("Memory system initialized with mem0")
            except Exception as e:
                logger.error(f"Failed to initialize mem0: {e}")
                self._initialized = False

    # =========================================================================
    # Mode Management
    # =========================================================================

    def set_mode(self, mode: str) -> None:
        """Set the current context mode.

        Args:
            mode: One of "work", "personal", "general"
        """
        mode_map = {
            "work": Mode.WORK,
            "personal": Mode.PERSONAL,
            "general": Mode.GENERAL,
        }
        if mode in mode_map:
            set_mode(mode_map[mode])
            logger.debug(f"Memory mode set to: {mode}")

    def get_mode(self) -> str:
        """Get the current context mode."""
        return get_current_mode().value

    # =========================================================================
    # Context Retrieval
    # =========================================================================

    def retrieve_context(
        self,
        query: str,
        include_profile: bool = True,
        include_facts: bool = True,
        include_sessions: bool = True,
        max_facts: int = 10,
        max_sessions: int = 3,
    ) -> MemoryContext:
        """
        Retrieve complete memory context for a query using mem0.

        Args:
            query: The user's message
            include_profile: Include user profile
            include_facts: Search for relevant facts
            include_sessions: Include recent sessions (not used with mem0)
            max_facts: Maximum facts to retrieve
            max_sessions: Maximum sessions (not used with mem0)

        Returns:
            MemoryContext with all relevant information
        """
        import time
        start_time = time.time()

        context = MemoryContext()
        context.current_mode = self.get_mode()

        try:
            # Get memory context using mem0
            if include_facts:
                context.memory_context_str = get_context(query, limit=max_facts)

                # Also get as MemoryResult objects for backwards compatibility
                results = search_memory(query, limit=max_facts)
                context.relevant_facts = [
                    MemoryItem(
                        key=r.id,
                        value=r.content,
                        category=r.metadata.get("category", "general"),
                        relevance_score=r.relevance_score,
                        created=r.created_at.isoformat() if r.created_at else None,
                    )
                    for r in results
                ]
                context.total_memories_searched = len(results)

            # Get user profile using mem0
            if include_profile:
                context.profile_context_str = get_profile()

                # Parse profile into legacy format for backwards compatibility
                profile_manager = get_profile_manager()
                mem0_profile = profile_manager.build_profile()

                # Extract preferences into legacy UserProfile
                context.user_profile = UserProfile(
                    preferences={
                        k[:30]: v for k, v in list(mem0_profile.preferences.items())[:5]
                    }
                )

        except Exception as e:
            logger.warning(f"Failed to retrieve mem0 context: {e}")

        context.retrieval_time_ms = int((time.time() - start_time) * 1000)

        logger.debug(
            f"Memory context retrieved: "
            f"{len(context.relevant_facts)} facts, "
            f"mode={context.current_mode} "
            f"({context.retrieval_time_ms}ms)"
        )

        return context

    # =========================================================================
    # Memory Storage
    # =========================================================================

    def store_memory(
        self,
        key: str,
        value: str,
        category: str = "general",
        tags: Optional[list[str]] = None,
        context: str = "general",
    ) -> None:
        """Store a memory item using mem0.

        Args:
            key: Memory key (used as metadata, not primary key in mem0)
            value: The content to remember
            category: Category tag
            tags: Additional tags (stored in metadata)
            context: Context mode - "work", "personal", or "general"
        """
        try:
            add_memory(
                content=value,
                context=context,
                category=category,
            )
            logger.debug(f"Stored memory via mem0: {key[:30]}...")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")

    def search_memories(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """Search memories using mem0 semantic search.

        Args:
            query: Search query
            category: Category filter (applied post-search)
            tags: Tag filter (not used with mem0)
            limit: Maximum results

        Returns:
            List of matching MemoryItems
        """
        try:
            results = search_memory(query, limit=limit)

            items = []
            for r in results:
                # Filter by category if specified
                mem_category = r.metadata.get("category", "general")
                if category and mem_category != category:
                    continue

                items.append(MemoryItem(
                    key=r.id,
                    value=r.content,
                    category=mem_category,
                    relevance_score=r.relevance_score,
                    created=r.created_at.isoformat() if r.created_at else None,
                ))

            return items

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    # =========================================================================
    # Conversation Processing
    # =========================================================================

    def process_conversation(
        self,
        messages: list[dict[str, str]],
        session_id: Optional[str] = None,
    ) -> None:
        """Process a conversation and extract memories using mem0.

        mem0 automatically extracts facts, preferences, and relationships.

        Args:
            messages: List of message dicts with 'role' and 'content'
            session_id: Optional session identifier
        """
        try:
            handler = get_conversation_handler()
            handler.process_conversation(
                messages=messages,
                user_id="emperor_user",  # Single user
                session_id=session_id,
            )
            logger.debug(f"Processed conversation with {len(messages)} messages")
        except Exception as e:
            logger.error(f"Failed to process conversation: {e}")

    def extract_and_store_facts(
        self,
        message: str,
        response: str,
    ) -> list[str]:
        """Extract and store facts from a conversation turn.

        Uses mem0's automatic extraction instead of regex patterns.

        Args:
            message: User's message
            response: Assistant's response

        Returns:
            Empty list (mem0 handles extraction automatically)
        """
        try:
            self.process_conversation(
                messages=[
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response},
                ]
            )
            # mem0 extracts facts automatically, we don't get keys back
            return []
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            return []

    # =========================================================================
    # User Profile (Legacy Compatibility)
    # =========================================================================

    def get_user_profile(self) -> UserProfile:
        """Get user profile from mem0.

        Returns:
            UserProfile with data from mem0
        """
        try:
            profile_manager = get_profile_manager()
            mem0_profile = profile_manager.build_profile()

            return UserProfile(
                preferences={
                    k[:30]: v for k, v in list(mem0_profile.preferences.items())[:10]
                }
            )
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return UserProfile()

    def update_user_profile(self, **kwargs) -> UserProfile:
        """Update user profile by storing as memories.

        Args:
            **kwargs: Profile fields to update (name, skill_level, etc.)

        Returns:
            Updated UserProfile
        """
        try:
            for key, value in kwargs.items():
                if value:
                    add_memory(
                        content=f"User {key}: {value}",
                        context="general",
                        category="preference",
                    )
            return self.get_user_profile()
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return UserProfile()


# =============================================================================
# Singleton
# =============================================================================

_memory_retriever: Optional[MemoryRetriever] = None


def get_memory_retriever(use_local: bool = True) -> MemoryRetriever:
    """Get the singleton memory retriever instance.

    Args:
        use_local: If True, uses local mem0 config.

    Returns:
        MemoryRetriever instance
    """
    global _memory_retriever
    if _memory_retriever is None:
        _memory_retriever = MemoryRetriever(use_local=use_local)
    return _memory_retriever


def reset_memory_retriever() -> None:
    """Reset the memory retriever singleton."""
    global _memory_retriever
    _memory_retriever = None
