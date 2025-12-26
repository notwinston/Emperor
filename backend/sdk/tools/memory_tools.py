"""Memory tools for SDK agents.

Provides tools for storing, retrieving, and managing persistent memory.
Used by all agents to remember user preferences, facts, and context.

Note: This provides a simple file-based implementation.
Part 9 (Memory System) will add more sophisticated storage with
vector search, semantic retrieval, and database backing.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config import settings, get_logger
from .base import BaseTool, ToolParameter, ParameterType

logger = get_logger(__name__)


# Memory storage path
MEMORY_DIR = settings.data_dir / "memory"
MEMORY_FILE = MEMORY_DIR / "knowledge.json"


def _ensure_memory_dir() -> None:
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _load_memories() -> dict[str, Any]:
    """Load memories from file."""
    _ensure_memory_dir()

    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading memories: {e}")
            return {"items": {}, "metadata": {"created": datetime.now(timezone.utc).isoformat()}}

    return {"items": {}, "metadata": {"created": datetime.now(timezone.utc).isoformat()}}


def _save_memories(data: dict[str, Any]) -> None:
    """Save memories to file."""
    _ensure_memory_dir()

    data["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class RememberTool(BaseTool):
    """Store information in long-term memory."""

    name = "remember"
    description = (
        "Store information in long-term memory for later retrieval. "
        "Use this to save user preferences, important facts, or context. "
        "Information persists across sessions."
    )
    parameters = [
        ToolParameter(
            name="key",
            type=ParameterType.STRING,
            description="Unique identifier for this memory (e.g., 'user_name', 'project_tech_stack')",
        ),
        ToolParameter(
            name="value",
            type=ParameterType.STRING,
            description="The information to remember",
        ),
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="Category for organization (e.g., 'user', 'project', 'preference')",
            required=False,
            default="general",
        ),
        ToolParameter(
            name="tags",
            type=ParameterType.ARRAY,
            description="Tags for searching",
            required=False,
            items={"type": "string"},
        ),
    ]

    async def execute(
        self,
        key: str,
        value: str,
        category: str = "general",
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        Store a memory.

        Args:
            key: Unique key for the memory
            value: Information to store
            category: Category for organization
            tags: Optional tags for searching

        Returns:
            Confirmation message
        """
        logger.debug(f"Remembering: {key} = {value[:50]}...")

        memories = _load_memories()

        # Check if updating existing memory
        is_update = key in memories["items"]

        # Store the memory
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

        _save_memories(memories)

        action = "Updated" if is_update else "Stored"
        return f"{action} memory: {key}\nCategory: {category}\nValue: {value}"


class RecallTool(BaseTool):
    """Retrieve information from memory."""

    name = "recall"
    description = (
        "Retrieve information from long-term memory. "
        "Can recall by exact key or search by category/tags. "
        "Use this to remember user preferences, project context, etc."
    )
    parameters = [
        ToolParameter(
            name="key",
            type=ParameterType.STRING,
            description="Exact key to retrieve, or search query",
            required=False,
        ),
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="Filter by category",
            required=False,
        ),
        ToolParameter(
            name="tag",
            type=ParameterType.STRING,
            description="Filter by tag",
            required=False,
        ),
        ToolParameter(
            name="list_all",
            type=ParameterType.BOOLEAN,
            description="List all memories (use sparingly)",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        key: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        list_all: bool = False,
    ) -> str:
        """
        Retrieve memories.

        Args:
            key: Exact key or search term
            category: Category filter
            tag: Tag filter
            list_all: List all memories

        Returns:
            Retrieved memories
        """
        memories = _load_memories()
        items = memories["items"]

        if not items:
            return "No memories stored yet."

        # Exact key lookup
        if key and key in items:
            memory = items[key]
            return (
                f"Memory: {key}\n"
                f"Category: {memory['category']}\n"
                f"Tags: {', '.join(memory['tags']) or 'none'}\n"
                f"Value: {memory['value']}\n"
                f"Last updated: {memory['updated']}"
            )

        # Search/filter
        results = []

        for k, v in items.items():
            # Key search (partial match)
            if key and key.lower() not in k.lower():
                # Also check value
                if key.lower() not in v["value"].lower():
                    continue

            # Category filter
            if category and v["category"] != category:
                continue

            # Tag filter
            if tag and tag not in v["tags"]:
                continue

            results.append((k, v))

        if not results:
            if key:
                return f"No memories found matching: {key}"
            elif category:
                return f"No memories in category: {category}"
            elif tag:
                return f"No memories with tag: {tag}"
            else:
                return "No memories found with the given filters."

        # Format results
        lines = [f"Found {len(results)} memories:", ""]

        for k, v in results[:20]:  # Limit to 20 results
            lines.append(f"📝 {k} [{v['category']}]")
            lines.append(f"   {v['value'][:100]}{'...' if len(v['value']) > 100 else ''}")
            lines.append("")

        if len(results) > 20:
            lines.append(f"... and {len(results) - 20} more")

        return "\n".join(lines)


class ForgetTool(BaseTool):
    """Remove information from memory."""

    name = "forget"
    description = (
        "Remove information from long-term memory. "
        "Use this to delete outdated or incorrect information. "
        "Can forget by exact key or clear entire categories."
    )
    parameters = [
        ToolParameter(
            name="key",
            type=ParameterType.STRING,
            description="Exact key to forget",
            required=False,
        ),
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="Clear all memories in a category (requires confirm=true)",
            required=False,
        ),
        ToolParameter(
            name="confirm",
            type=ParameterType.BOOLEAN,
            description="Confirm deletion (required for category-wide deletion)",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        key: Optional[str] = None,
        category: Optional[str] = None,
        confirm: bool = False,
    ) -> str:
        """
        Remove memories.

        Args:
            key: Exact key to delete
            category: Category to clear
            confirm: Confirmation for bulk deletion

        Returns:
            Confirmation of what was deleted
        """
        if not key and not category:
            return "Please specify a key or category to forget."

        memories = _load_memories()
        items = memories["items"]

        # Forget by exact key
        if key:
            if key in items:
                del items[key]
                _save_memories(memories)
                logger.debug(f"Forgot memory: {key}")
                return f"Forgot memory: {key}"
            else:
                return f"Memory not found: {key}"

        # Forget by category
        if category:
            if not confirm:
                # Count affected memories
                count = sum(1 for v in items.values() if v["category"] == category)
                if count == 0:
                    return f"No memories found in category: {category}"
                return (
                    f"This will delete {count} memories in category '{category}'.\n"
                    f"Call again with confirm=true to proceed."
                )

            # Delete all in category
            keys_to_delete = [
                k for k, v in items.items()
                if v["category"] == category
            ]

            for k in keys_to_delete:
                del items[k]

            _save_memories(memories)
            logger.debug(f"Forgot {len(keys_to_delete)} memories in category: {category}")

            return f"Forgot {len(keys_to_delete)} memories in category: {category}"


class ListMemoriesTool(BaseTool):
    """List all memory categories and keys."""

    name = "list_memories"
    description = (
        "List all stored memories organized by category. "
        "Use this to see what information is remembered. "
        "Shows keys and categories without full values."
    )
    parameters = [
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="Filter by category (optional)",
            required=False,
        ),
    ]

    async def execute(self, category: Optional[str] = None) -> str:
        """
        List memories.

        Args:
            category: Optional category filter

        Returns:
            List of memory keys by category
        """
        memories = _load_memories()
        items = memories["items"]

        if not items:
            return "No memories stored yet."

        # Organize by category
        by_category: dict[str, list[str]] = {}

        for k, v in items.items():
            cat = v["category"]
            if category and cat != category:
                continue
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(k)

        if not by_category:
            return f"No memories in category: {category}"

        # Format output
        lines = ["Stored Memories:", ""]

        for cat in sorted(by_category.keys()):
            keys = sorted(by_category[cat])
            lines.append(f"📁 {cat} ({len(keys)} items)")
            for k in keys[:10]:  # Limit to 10 per category
                lines.append(f"   • {k}")
            if len(keys) > 10:
                lines.append(f"   ... and {len(keys) - 10} more")
            lines.append("")

        total = sum(len(keys) for keys in by_category.values())
        lines.append(f"Total: {total} memories in {len(by_category)} categories")

        return "\n".join(lines)


# Tool instances for easy access
remember = RememberTool()
recall = RecallTool()
forget = ForgetTool()
list_memories = ListMemoriesTool()

# All memory tools
MEMORY_TOOLS = [remember, recall, forget, list_memories]
