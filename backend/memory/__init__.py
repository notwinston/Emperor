"""Memory Module for Emperor AI Assistant.

Provides intelligent memory management using mem0 with:
- Automatic fact extraction from conversations
- Semantic search for relevant memories
- Mode-based filtering (work, personal, general)
- Agent tagging for Domain Lead memories
- User profile building from aggregated memories

Single-user design optimized for desktop use.

Quick Start:
    >>> from memory import add_memory, search_memory, set_mode, Mode
    >>>
    >>> # Store a user memory
    >>> add_memory("I prefer dark mode", context="general")
    >>>
    >>> # Store a memory from a Domain Lead
    >>> add_memory("User prefers pytest", agent="code_lead", source="code_review")
    >>>
    >>> # Switch to work mode
    >>> set_mode(Mode.WORK)
    >>>
    >>> # Search all memories
    >>> results = search_memory("testing preferences")
    >>>
    >>> # Search only code_lead's memories
    >>> results = search_memory("testing", agent="code_lead")

Components:
    - MemoryService: Core CRUD operations for memories
    - ConversationMemoryHandler: Auto-extracts memories from conversations
    - UserProfileManager: Builds user profiles from aggregated memories
    - Mode: Context modes (WORK, PERSONAL, GENERAL)

Agent Tagging:
    Domain Leads can store memories with their identity for later retrieval:
    - agent: Which agent stored the memory (e.g., "code_lead", "research_lead")
    - source: What activity produced it (e.g., "code_review", "web_search")
"""

from typing import Optional

# Configuration
from .config import (
    MEM0_CONFIG,
    MEM0_LOCAL_CONFIG,
    get_config,
    validate_config,
)

# Core memory service
from .memory_service import (
    MemoryResult,
    MemoryService,
    get_memory_service,
    reset_memory_service,
)

# Conversation handling
from .conversation_handler import (
    ConversationMemoryHandler,
    get_conversation_handler,
    reset_conversation_handler,
)

# User profiles and modes
from .user_profile import (
    DEFAULT_USER_ID,
    MODE_CONTEXTS,
    Mode,
    UserProfile,
    UserProfileManager,
    get_current_mode,
    get_profile_manager,
    reset_profile_manager,
    set_mode,
)


def initialize(use_local: bool = True) -> None:
    """Initialize all memory components.

    Call this at application startup to ensure all
    singletons are created with consistent configuration.

    Args:
        use_local: If True, uses local config (HuggingFace + ChromaDB).
                   If False, uses full config (OpenAI + Neo4j).

    Example:
        >>> from memory import initialize
        >>> initialize(use_local=True)
    """
    get_memory_service(use_local=use_local)
    get_conversation_handler()
    get_profile_manager()


def reset() -> None:
    """Reset all memory singletons.

    Useful for testing or reinitializing with different config.
    Does not delete stored memories, only resets Python objects.

    Example:
        >>> from memory import reset, initialize
        >>> reset()
        >>> initialize(use_local=False)  # Reinitialize with full config
    """
    reset_memory_service()
    reset_conversation_handler()
    reset_profile_manager()


def add_memory(
    content: str,
    context: Optional[str] = None,
    category: Optional[str] = None,
    agent: Optional[str] = None,
    source: Optional[str] = None,
) -> dict:
    """Convenience function to add a memory.

    Args:
        content: The text content to remember.
        context: Context mode - "work", "personal", or "general".
                 Uses current mode if not specified.
        category: Optional category tag.
        agent: The agent storing this memory (e.g., "code_lead", "research_lead").
        source: The activity that produced this memory (e.g., "code_review", "web_search").

    Returns:
        Dict with memory ID and extraction results.

    Example:
        >>> from memory import add_memory, set_mode, Mode
        >>> set_mode(Mode.WORK)
        >>> add_memory("Sprint ends Friday")  # Stored as "work" context
        >>> add_memory("I prefer TypeScript", context="general", category="preference")
        >>> # Domain Lead storing a memory:
        >>> add_memory("User prefers pytest", agent="code_lead", source="code_review")
    """
    memory = get_memory_service()

    # Use current mode if context not specified
    if context is None:
        context = get_current_mode().value

    metadata = {"context": context}
    if category:
        metadata["category"] = category

    return memory.add(
        content,
        user_id=DEFAULT_USER_ID,
        metadata=metadata,
        agent=agent,
        source=source,
    )


def search_memory(
    query: str,
    limit: int = 5,
    filter_by_mode: bool = True,
    agent: Optional[str] = None,
) -> list:
    """Convenience function to search memories.

    Respects the current mode setting for filtering:
    - WORK mode: returns work + general memories
    - PERSONAL mode: returns personal + general memories
    - GENERAL mode: returns all memories

    Args:
        query: Natural language search query.
        limit: Maximum results to return.
        filter_by_mode: Whether to filter by current mode (default True).
        agent: Filter to memories from specific agent (e.g., "code_lead").

    Returns:
        List of MemoryResult objects.

    Example:
        >>> from memory import search_memory, set_mode, Mode
        >>> set_mode(Mode.WORK)
        >>> results = search_memory("project deadlines")
        >>> # Returns only work + general memories
        >>> # Search only code_lead's memories:
        >>> results = search_memory("testing preferences", agent="code_lead")
    """
    handler = get_conversation_handler()
    return handler.get_relevant_memories(
        query=query,
        user_id=DEFAULT_USER_ID,
        limit=limit,
        filter_by_mode=filter_by_mode,
        agent=agent,
    )


def get_agent_memories(agent: str, query: Optional[str] = None, limit: int = 10) -> list:
    """Get memories created by a specific Domain Lead.

    Useful for agents to retrieve their own stored knowledge
    or for the orchestrator to understand what an agent knows.

    Args:
        agent: The agent identifier (e.g., "code_lead", "research_lead").
        query: Optional search query to filter by relevance.
        limit: Maximum memories to return.

    Returns:
        List of memories from the specified agent.

    Example:
        >>> from memory import get_agent_memories
        >>> # Get all code_lead memories
        >>> memories = get_agent_memories("code_lead")
        >>> # Search code_lead memories for testing info
        >>> memories = get_agent_memories("code_lead", query="testing framework")
    """
    handler = get_conversation_handler()
    return handler.get_agent_memories(
        agent=agent,
        user_id=DEFAULT_USER_ID,
        query=query,
        limit=limit,
    )


def get_context(query: str, limit: int = 5, filter_by_mode: bool = True) -> str:
    """Convenience function to get formatted context for prompts.

    Respects the current mode setting for filtering:
    - WORK mode: returns work + general memories
    - PERSONAL mode: returns personal + general memories
    - GENERAL mode: returns all memories

    Args:
        query: The user's current query/message.
        limit: Maximum memories to include.
        filter_by_mode: Whether to filter by current mode (default True).

    Returns:
        Formatted string of relevant memories.

    Example:
        >>> from memory import get_context, set_mode, Mode
        >>> set_mode(Mode.WORK)
        >>> context = get_context("How should I structure my components?")
        >>> # Returns only work + general memories
    """
    handler = get_conversation_handler()
    return handler.get_relevant_context(
        query=query,
        user_id=DEFAULT_USER_ID,
        limit=limit,
        filter_by_mode=filter_by_mode,
    )


def get_profile(mode: Optional[Mode] = None) -> str:
    """Convenience function to get formatted user profile.

    Args:
        mode: Optional mode override. Uses current mode if None.

    Returns:
        Formatted profile string for prompt injection.

    Example:
        >>> from memory import get_profile, Mode
        >>> profile = get_profile(Mode.WORK)
        >>> print(profile)
        "User Profile (work mode):

        Preferences:
          - I prefer dark mode

        Work Context:
          - Working on Emperor project"
    """
    manager = get_profile_manager()
    return manager.get_profile_context(mode)


# Public API
__all__ = [
    # Configuration
    "MEM0_CONFIG",
    "MEM0_LOCAL_CONFIG",
    "get_config",
    "validate_config",
    # Memory Service
    "MemoryResult",
    "MemoryService",
    "get_memory_service",
    "reset_memory_service",
    # Conversation Handler
    "ConversationMemoryHandler",
    "get_conversation_handler",
    "reset_conversation_handler",
    # User Profile
    "DEFAULT_USER_ID",
    "MODE_CONTEXTS",
    "Mode",
    "UserProfile",
    "UserProfileManager",
    "get_profile_manager",
    "reset_profile_manager",
    "set_mode",
    "get_current_mode",
    # Convenience Functions
    "initialize",
    "reset",
    "add_memory",
    "search_memory",
    "get_agent_memories",
    "get_context",
    "get_profile",
]
