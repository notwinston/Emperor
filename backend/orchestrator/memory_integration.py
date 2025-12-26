"""Memory Integration for Emperor AI Assistant.

This module integrates the memory system into the Orchestrator,
providing retrieval of relevant context before processing messages.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config import settings, get_logger

logger = get_logger(__name__)

# Memory storage paths (same as memory_tools.py)
MEMORY_DIR = settings.data_dir / "memory"
MEMORY_FILE = MEMORY_DIR / "knowledge.json"
USER_PROFILE_FILE = MEMORY_DIR / "user_profile.json"
SESSION_HISTORY_FILE = MEMORY_DIR / "sessions.json"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class UserProfile:
    """User profile information."""

    name: Optional[str] = None
    skill_level: Optional[str] = None  # beginner, intermediate, senior
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
    relevance_score: float = 0.0  # For ranking


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

    # User information
    user_profile: UserProfile = field(default_factory=UserProfile)

    # Retrieved facts (relevant to current query)
    relevant_facts: list[MemoryItem] = field(default_factory=list)

    # All user-category memories (always included)
    user_memories: list[MemoryItem] = field(default_factory=list)

    # Recent session summaries
    recent_sessions: list[SessionSummary] = field(default_factory=list)

    # Project-specific context
    project_context: dict[str, Any] = field(default_factory=dict)

    # Retrieval metadata
    retrieval_time_ms: int = 0
    total_memories_searched: int = 0

    def has_context(self) -> bool:
        """Check if any context was retrieved."""
        return (
            self.user_profile.name is not None
            or len(self.relevant_facts) > 0
            or len(self.user_memories) > 0
            or len(self.recent_sessions) > 0
        )

    def to_prompt_string(self) -> str:
        """Format memory context for inclusion in system prompt."""
        sections = []

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

        # Recent sessions section
        if self.recent_sessions:
            sessions = "\n".join(
                f"- {s.timestamp[:10]}: {s.summary[:100]}"
                for s in self.recent_sessions[:3]
            )
            sections.append(f"**Recent Context:**\n{sessions}")

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
            "recent_sessions": [
                {"session_id": s.session_id, "summary": s.summary}
                for s in self.recent_sessions
            ],
            "project_context": self.project_context,
        }


# =============================================================================
# Memory Retriever
# =============================================================================


class MemoryRetriever:
    """
    Retrieves relevant memory context for the Orchestrator.

    Provides methods to:
    - Load user profile
    - Search for relevant facts
    - Get recent session context
    - Build complete memory context for requests
    """

    def __init__(self):
        """Initialize the memory retriever."""
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure memory directories exist."""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # File Operations
    # =========================================================================

    def _load_json(self, path: Path, default: dict) -> dict:
        """Load JSON from file with fallback."""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading {path}: {e}")
        return default

    def _save_json(self, path: Path, data: dict) -> None:
        """Save JSON to file."""
        self._ensure_dirs()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_memories(self) -> dict:
        """Load all memories from file."""
        return self._load_json(
            MEMORY_FILE,
            {"items": {}, "metadata": {"created": datetime.now(timezone.utc).isoformat()}}
        )

    # =========================================================================
    # User Profile
    # =========================================================================

    def get_user_profile(self) -> UserProfile:
        """Load and return user profile."""
        data = self._load_json(USER_PROFILE_FILE, {})

        return UserProfile(
            name=data.get("name"),
            skill_level=data.get("skill_level"),
            preferred_language=data.get("preferred_language"),
            preferences=data.get("preferences", {}),
            timezone=data.get("timezone"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update_user_profile(self, **kwargs) -> UserProfile:
        """Update user profile with new values."""
        data = self._load_json(USER_PROFILE_FILE, {})

        # Update only provided fields
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "created_at" not in data:
            data["created_at"] = data["updated_at"]

        self._save_json(USER_PROFILE_FILE, data)
        logger.debug(f"Updated user profile: {list(kwargs.keys())}")

        return self.get_user_profile()

    # =========================================================================
    # Memory Search
    # =========================================================================

    def search_memories(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """
        Search memories by query text, category, or tags.

        Uses simple keyword matching. Part 9 will add semantic search.

        Args:
            query: Search query (matches key and value)
            category: Filter by category
            tags: Filter by tags (any match)
            limit: Maximum results to return

        Returns:
            List of matching MemoryItems sorted by relevance
        """
        memories = self._load_memories()
        items = memories.get("items", {})

        if not items:
            return []

        results: list[MemoryItem] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for key, data in items.items():
            # Category filter
            if category and data.get("category") != category:
                continue

            # Tag filter
            if tags:
                item_tags = set(data.get("tags", []))
                if not item_tags.intersection(tags):
                    continue

            # Calculate relevance score
            score = 0.0
            value = data.get("value", "")
            value_lower = value.lower()
            key_lower = key.lower()

            # Exact key match
            if query_lower == key_lower:
                score += 1.0

            # Key contains query
            elif query_lower in key_lower:
                score += 0.8

            # Value contains query
            if query_lower in value_lower:
                score += 0.6

            # Word overlap
            value_words = set(value_lower.split())
            overlap = len(query_words.intersection(value_words))
            if overlap > 0:
                score += 0.1 * overlap

            # Skip if no relevance
            if score == 0:
                continue

            results.append(MemoryItem(
                key=key,
                value=value,
                category=data.get("category", "general"),
                tags=data.get("tags", []),
                created=data.get("created"),
                updated=data.get("updated"),
                relevance_score=score,
            ))

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def get_memories_by_category(
        self,
        category: str,
        limit: int = 20,
    ) -> list[MemoryItem]:
        """Get all memories in a category."""
        memories = self._load_memories()
        items = memories.get("items", {})

        results = []
        for key, data in items.items():
            if data.get("category") == category:
                results.append(MemoryItem(
                    key=key,
                    value=data.get("value", ""),
                    category=category,
                    tags=data.get("tags", []),
                    created=data.get("created"),
                    updated=data.get("updated"),
                ))

        return results[:limit]

    def get_all_memories(self, limit: int = 50) -> list[MemoryItem]:
        """Get all memories (limited)."""
        memories = self._load_memories()
        items = memories.get("items", {})

        results = []
        for key, data in list(items.items())[:limit]:
            results.append(MemoryItem(
                key=key,
                value=data.get("value", ""),
                category=data.get("category", "general"),
                tags=data.get("tags", []),
                created=data.get("created"),
                updated=data.get("updated"),
            ))

        return results

    # =========================================================================
    # Memory Storage
    # =========================================================================

    def store_memory(
        self,
        key: str,
        value: str,
        category: str = "general",
        tags: Optional[list[str]] = None,
    ) -> None:
        """Store a memory item."""
        memories = self._load_memories()

        memories["items"][key] = {
            "value": value,
            "category": category,
            "tags": tags or [],
            "created": memories["items"].get(key, {}).get(
                "created",
                datetime.now(timezone.utc).isoformat()
            ),
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        memories["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
        self._save_json(MEMORY_FILE, memories)

        logger.debug(f"Stored memory: {key}")

    def delete_memory(self, key: str) -> bool:
        """Delete a memory item."""
        memories = self._load_memories()

        if key in memories["items"]:
            del memories["items"][key]
            self._save_json(MEMORY_FILE, memories)
            logger.debug(f"Deleted memory: {key}")
            return True

        return False

    # =========================================================================
    # Session History
    # =========================================================================

    def get_recent_sessions(self, limit: int = 5) -> list[SessionSummary]:
        """Get recent session summaries."""
        data = self._load_json(SESSION_HISTORY_FILE, {"sessions": []})
        sessions = data.get("sessions", [])

        results = []
        for s in sessions[-limit:]:
            results.append(SessionSummary(
                session_id=s.get("session_id", ""),
                timestamp=s.get("timestamp", ""),
                summary=s.get("summary", ""),
                topics=s.get("topics", []),
                message_count=s.get("message_count", 0),
            ))

        return list(reversed(results))  # Most recent first

    def save_session_summary(
        self,
        session_id: str,
        summary: str,
        topics: list[str],
        message_count: int,
    ) -> None:
        """Save a session summary for future reference."""
        data = self._load_json(SESSION_HISTORY_FILE, {"sessions": []})

        data["sessions"].append({
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "topics": topics,
            "message_count": message_count,
        })

        # Keep only last 50 sessions
        data["sessions"] = data["sessions"][-50:]

        self._save_json(SESSION_HISTORY_FILE, data)
        logger.debug(f"Saved session summary: {session_id}")

    # =========================================================================
    # Context Building
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
        Retrieve complete memory context for a query.

        This is the main method called by the Orchestrator before
        processing a message.

        Args:
            query: The user's message
            include_profile: Include user profile
            include_facts: Search for relevant facts
            include_sessions: Include recent sessions
            max_facts: Maximum facts to retrieve
            max_sessions: Maximum sessions to include

        Returns:
            MemoryContext with all relevant information
        """
        import time
        start_time = time.time()

        context = MemoryContext()
        total_searched = 0

        # Get user profile
        if include_profile:
            context.user_profile = self.get_user_profile()

        # Search for relevant facts
        if include_facts:
            memories = self._load_memories()
            total_searched = len(memories.get("items", {}))

            # Search by query
            context.relevant_facts = self.search_memories(
                query=query,
                limit=max_facts,
            )

            # Always include user-category memories
            context.user_memories = self.get_memories_by_category(
                category="user",
                limit=5,
            )

            # Get project context
            project_memories = self.get_memories_by_category(
                category="project",
                limit=10,
            )
            context.project_context = {
                m.key: m.value for m in project_memories
            }

        # Get recent sessions
        if include_sessions:
            context.recent_sessions = self.get_recent_sessions(limit=max_sessions)

        # Record metadata
        context.retrieval_time_ms = int((time.time() - start_time) * 1000)
        context.total_memories_searched = total_searched

        logger.debug(
            f"Memory context retrieved: "
            f"{len(context.relevant_facts)} facts, "
            f"{len(context.user_memories)} user memories, "
            f"{len(context.recent_sessions)} sessions "
            f"({context.retrieval_time_ms}ms)"
        )

        return context

    # =========================================================================
    # Automatic Memory Extraction
    # =========================================================================

    def extract_and_store_facts(self, message: str, response: str) -> list[str]:
        """
        Extract and store facts from conversation.

        Looks for patterns like:
        - "My name is X"
        - "I prefer X"
        - "Remember that X"

        Args:
            message: User's message
            response: Assistant's response

        Returns:
            List of keys for stored facts
        """
        stored_keys = []
        combined = f"{message} {response}".lower()

        # Pattern: "my name is X"
        name_match = re.search(r"my name is (\w+)", combined, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).capitalize()
            self.update_user_profile(name=name)
            stored_keys.append("user_name")
            logger.info(f"Extracted user name: {name}")

        # Pattern: "I prefer X" / "I like X"
        pref_match = re.search(
            r"i (prefer|like|use|work with) (\w+(?:\s+\w+)?)",
            combined,
            re.IGNORECASE
        )
        if pref_match:
            preference = pref_match.group(2)
            key = f"preference_{preference.replace(' ', '_')}"
            self.store_memory(
                key=key,
                value=f"User prefers {preference}",
                category="user",
                tags=["preference"],
            )
            stored_keys.append(key)

        # Pattern: "remember that X" / "remember X"
        remember_match = re.search(
            r"remember (?:that )?(.+?)(?:\.|$)",
            message,
            re.IGNORECASE
        )
        if remember_match:
            fact = remember_match.group(1).strip()
            if len(fact) > 10:  # Avoid storing very short things
                key = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.store_memory(
                    key=key,
                    value=fact,
                    category="fact",
                    tags=["user_requested"],
                )
                stored_keys.append(key)

        return stored_keys


# =============================================================================
# Singleton
# =============================================================================

_memory_retriever: Optional[MemoryRetriever] = None


def get_memory_retriever() -> MemoryRetriever:
    """Get the singleton memory retriever instance."""
    global _memory_retriever
    if _memory_retriever is None:
        _memory_retriever = MemoryRetriever()
    return _memory_retriever
