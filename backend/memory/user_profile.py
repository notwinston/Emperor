"""User Profile Manager for Emperor AI Assistant.

Builds and manages user profiles derived from memories.
Supports mode-based filtering (work, personal, general) for
context-aware memory retrieval.

Single-user design optimized for desktop use.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .memory_service import MemoryService, MemoryResult


# Default user ID for single-user desktop app
DEFAULT_USER_ID = "emperor_user"


class Mode(str, Enum):
    """Context modes for memory filtering."""

    WORK = "work"
    PERSONAL = "personal"
    GENERAL = "general"  # Sees all memories


# Which contexts each mode can access
MODE_CONTEXTS: Dict[Mode, List[str]] = {
    Mode.WORK: ["work", "general"],
    Mode.PERSONAL: ["personal", "general"],
    Mode.GENERAL: ["work", "personal", "general"],  # Everything
}


@dataclass
class UserProfile:
    """User profile aggregated from memories.

    Attributes:
        mode: Current context mode (work, personal, general).
        preferences: User preferences that apply across contexts.
        facts: List of known facts about the user.
        work_context: Work-related information (projects, team, etc.).
        personal_context: Personal information and projects.
    """

    mode: Mode = Mode.GENERAL
    preferences: Dict[str, str] = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)
    work_context: Dict[str, str] = field(default_factory=dict)
    personal_context: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "mode": self.mode.value,
            "preferences": self.preferences,
            "facts": self.facts,
            "work_context": self.work_context,
            "personal_context": self.personal_context,
        }


class UserProfileManager:
    """Manages user profile derived from memories.

    Builds structured profiles by querying memories and organizing
    them into categories. Supports mode-based filtering for
    context-aware responses.

    Single-user design - no user_id required for most operations.

    Example:
        >>> manager = UserProfileManager(memory_service)
        >>> profile = manager.build_profile(mode=Mode.WORK)
        >>> print(profile.work_context)
        {"React project": "Working on a React 18 project"}

        >>> context = manager.get_profile_context(mode=Mode.WORK)
        >>> print(context)
        "User Profile (work mode):\\n\\nPreferences:\\n  - Prefers dark mode"
    """

    # Queries used to build different aspects of the profile
    PROFILE_QUERIES = [
        ("preferences", "user preferences and settings"),
        ("work", "user's work projects and professional context"),
        ("personal", "user's personal projects and hobbies"),
        ("tools", "user's coding style tools and technologies"),
        ("general", "user's general information"),
    ]

    # Keywords for categorizing memories
    PREFERENCE_KEYWORDS = ["prefer", "like", "want", "always", "never", "hate", "love"]
    WORK_KEYWORDS = ["work", "job", "company", "team", "sprint", "deadline", "meeting", "client"]
    PERSONAL_KEYWORDS = ["hobby", "personal", "home", "family", "weekend", "free time"]

    def __init__(self, memory_service: MemoryService):
        """Initialize the profile manager.

        Args:
            memory_service: The MemoryService instance for querying memories.
        """
        self.memory = memory_service
        self._current_mode = Mode.GENERAL

    @property
    def current_mode(self) -> Mode:
        """Get the current context mode."""
        return self._current_mode

    def set_mode(self, mode: Mode) -> None:
        """Set the current context mode.

        Args:
            mode: The mode to switch to (work, personal, general).
        """
        self._current_mode = mode

    def build_profile(self, mode: Optional[Mode] = None) -> UserProfile:
        """Build a user profile from stored memories.

        Aggregates information from multiple memory searches
        and organizes into structured categories.

        Args:
            mode: Context mode for filtering. Uses current_mode if None.

        Returns:
            UserProfile with categorized information.
        """
        active_mode = mode or self._current_mode
        allowed_contexts = MODE_CONTEXTS[active_mode]

        profile = UserProfile(mode=active_mode)
        seen_content = set()  # Avoid duplicates

        for query_type, query in self.PROFILE_QUERIES:
            memories = self.memory.search(query, limit=5)

            for mem in memories:
                # Skip duplicates
                if mem.content in seen_content:
                    continue
                seen_content.add(mem.content)

                # Check if memory's context is allowed in current mode
                mem_context = mem.metadata.get("context", "general")
                if mem_context not in allowed_contexts:
                    continue

                # Categorize the memory
                self._categorize_memory(mem.content, mem.metadata, profile)

        return profile

    def get_profile_context(self, mode: Optional[Mode] = None) -> str:
        """Get formatted profile for prompt injection.

        Builds a profile and formats it as a string suitable
        for including in system prompts.

        Args:
            mode: Context mode for filtering. Uses current_mode if None.

        Returns:
            Formatted string representation of the profile.
        """
        profile = self.build_profile(mode)
        return self._format_profile(profile)

    def get_preferences(self, mode: Optional[Mode] = None) -> Dict[str, str]:
        """Get just the user's preferences.

        Args:
            mode: Context mode for filtering.

        Returns:
            Dictionary of preferences.
        """
        profile = self.build_profile(mode)
        return profile.preferences

    def get_work_context(self) -> Dict[str, str]:
        """Get work-related context.

        Returns:
            Dictionary of work context information.
        """
        profile = self.build_profile(Mode.WORK)
        return profile.work_context

    def get_personal_context(self) -> Dict[str, str]:
        """Get personal context.

        Returns:
            Dictionary of personal context information.
        """
        profile = self.build_profile(Mode.PERSONAL)
        return profile.personal_context

    def _categorize_memory(
        self,
        content: str,
        metadata: Dict[str, Any],
        profile: UserProfile,
    ) -> None:
        """Categorize memory content into profile sections.

        Uses keyword detection and metadata to sort memories
        into appropriate profile categories.

        Args:
            content: The memory content text.
            metadata: Memory metadata including context.
            profile: The UserProfile to update.
        """
        content_lower = content.lower()
        mem_context = metadata.get("context", "general")

        # Create a short key from content (first 50 chars)
        key = content[:50].strip()

        # Detect preferences (apply across all contexts)
        if any(kw in content_lower for kw in self.PREFERENCE_KEYWORDS):
            profile.preferences[key] = content

        # Detect work context
        if mem_context == "work" or any(kw in content_lower for kw in self.WORK_KEYWORDS):
            profile.work_context[key] = content

        # Detect personal context
        if mem_context == "personal" or any(kw in content_lower for kw in self.PERSONAL_KEYWORDS):
            profile.personal_context[key] = content

        # Always add to facts list
        profile.facts.append(content)

    def _format_profile(self, profile: UserProfile) -> str:
        """Format a profile as a context string.

        Args:
            profile: The UserProfile to format.

        Returns:
            Formatted string for prompt injection.
        """
        parts = [f"User Profile ({profile.mode.value} mode):"]

        # Preferences (always shown, limited to 5)
        if profile.preferences:
            parts.append("\nPreferences:")
            for value in list(profile.preferences.values())[:5]:
                parts.append(f"  - {value}")

        # Work context (if in work or general mode)
        if profile.mode in [Mode.WORK, Mode.GENERAL] and profile.work_context:
            parts.append("\nWork Context:")
            for value in list(profile.work_context.values())[:5]:
                parts.append(f"  - {value}")

        # Personal context (if in personal or general mode)
        if profile.mode in [Mode.PERSONAL, Mode.GENERAL] and profile.personal_context:
            parts.append("\nPersonal Context:")
            for value in list(profile.personal_context.values())[:5]:
                parts.append(f"  - {value}")

        # If no content, indicate empty profile
        if len(parts) == 1:
            parts.append("\nNo profile information stored yet.")

        return "\n".join(parts)


# Module-level singleton
_profile_manager: Optional[UserProfileManager] = None


def get_profile_manager(
    memory_service: Optional[MemoryService] = None,
) -> UserProfileManager:
    """Get the profile manager singleton.

    Args:
        memory_service: Optional MemoryService instance.
                        If None, uses get_memory_service().

    Returns:
        The shared UserProfileManager instance.
    """
    global _profile_manager

    if _profile_manager is None:
        if memory_service is None:
            from .memory_service import get_memory_service
            memory_service = get_memory_service()
        _profile_manager = UserProfileManager(memory_service)

    return _profile_manager


def reset_profile_manager() -> None:
    """Reset the profile manager singleton."""
    global _profile_manager
    _profile_manager = None


def set_mode(mode: Mode) -> None:
    """Convenience function to set the current mode.

    Args:
        mode: The mode to switch to.
    """
    get_profile_manager().set_mode(mode)


def get_current_mode() -> Mode:
    """Convenience function to get the current mode.

    Returns:
        The current context mode.
    """
    return get_profile_manager().current_mode
