"""Memory tools for SDK agents.

Provides tools for storing, retrieving, and managing persistent memory
using the mem0-based memory system. Used by Domain Leads and Workers
to remember user preferences, facts, code patterns, and context.

These tools integrate with the Part 9 memory system:
- Stores memories with agent tagging for source tracking
- Supports mode-based filtering (work/personal/general)
- Uses semantic search for intelligent retrieval
"""

from typing import Any, Optional, List

from config import get_logger
from .base import BaseTool, ToolParameter, ParameterType

logger = get_logger(__name__)


class RememberTool(BaseTool):
    """Store information in long-term memory using mem0."""

    name = "remember"
    description = (
        "Store important information in long-term memory for future reference. "
        "Use this to save user preferences, code patterns, learned facts, or project context. "
        "Information persists across sessions and is searchable semantically."
    )
    parameters = [
        ToolParameter(
            name="content",
            type=ParameterType.STRING,
            description="The information to remember (be specific and descriptive)",
        ),
        ToolParameter(
            name="category",
            type=ParameterType.STRING,
            description="Category of memory",
            required=False,
            default="general",
            enum=["preference", "fact", "code_pattern", "workflow", "project", "general"],
        ),
        ToolParameter(
            name="context",
            type=ParameterType.STRING,
            description="Context mode for filtering",
            required=False,
            default="work",
            enum=["work", "personal", "general"],
        ),
    ]

    def __init__(self, agent_name: str = "unknown"):
        """
        Initialize with agent identity for tagging.

        Args:
            agent_name: Name of the agent using this tool (e.g., "code_lead")
        """
        super().__init__()
        self.agent_name = agent_name

    async def execute(
        self,
        content: str,
        category: str = "general",
        context: str = "work",
    ) -> str:
        """
        Store a memory using mem0.

        Args:
            content: Information to store
            category: Category for organization
            context: Context mode (work/personal/general)

        Returns:
            Confirmation message with memory details
        """
        # Import here to avoid circular imports
        from memory import add_memory

        logger.debug(f"Agent '{self.agent_name}' remembering: {content[:50]}...")

        try:
            result = add_memory(
                content=content,
                context=context,
                category=category,
                agent=self.agent_name,
                source="agent_tool",
            )

            # Extract memory ID if available
            memory_id = "unknown"
            if isinstance(result, dict):
                # mem0 returns different formats
                if "results" in result and result["results"]:
                    memory_id = result["results"][0].get("id", "stored")
                elif "id" in result:
                    memory_id = result["id"]

            return (
                f"Stored memory successfully.\n"
                f"Content: {content}\n"
                f"Category: {category}\n"
                f"Context: {context}\n"
                f"Agent: {self.agent_name}"
            )

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return f"Failed to store memory: {str(e)}"


class RecallTool(BaseTool):
    """Retrieve relevant memories using semantic search."""

    name = "recall"
    description = (
        "Search and retrieve relevant memories using semantic similarity. "
        "Use this to find user preferences, past decisions, code patterns, or context. "
        "Describe what you're looking for in natural language."
    )
    parameters = [
        ToolParameter(
            name="query",
            type=ParameterType.STRING,
            description="What to search for in memory (natural language)",
        ),
        ToolParameter(
            name="limit",
            type=ParameterType.INTEGER,
            description="Maximum number of results to return",
            required=False,
            default=5,
        ),
        ToolParameter(
            name="agent_only",
            type=ParameterType.BOOLEAN,
            description="Only return memories from this agent",
            required=False,
            default=False,
        ),
    ]

    def __init__(self, agent_name: str = "unknown"):
        """
        Initialize with agent identity.

        Args:
            agent_name: Name of the agent using this tool
        """
        super().__init__()
        self.agent_name = agent_name

    async def execute(
        self,
        query: str,
        limit: int = 5,
        agent_only: bool = False,
    ) -> str:
        """
        Search memories using semantic search.

        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            agent_only: Filter to only this agent's memories

        Returns:
            Formatted list of relevant memories
        """
        from memory import search_memory, get_agent_memories

        logger.debug(f"Agent '{self.agent_name}' recalling: {query}")

        try:
            if agent_only:
                results = get_agent_memories(
                    agent=self.agent_name,
                    query=query,
                    limit=limit,
                )
            else:
                results = search_memory(
                    query=query,
                    limit=limit,
                    agent=None,  # Search all agents
                )

            if not results:
                return f"No memories found for: {query}"

            # Format results
            lines = [f"Found {len(results)} relevant memories:", ""]

            for i, mem in enumerate(results, 1):
                # Handle both MemoryResult objects and dicts
                if hasattr(mem, "content"):
                    content = mem.content
                    score = getattr(mem, "relevance_score", 0.0)
                    metadata = getattr(mem, "metadata", {})
                else:
                    content = mem.get("memory", mem.get("content", str(mem)))
                    score = mem.get("score", 0.0)
                    metadata = mem.get("metadata", {})

                agent = metadata.get("agent", "user")
                category = metadata.get("category", "general")

                lines.append(f"{i}. [{category}] (from: {agent})")
                lines.append(f"   {content}")
                if score > 0:
                    lines.append(f"   Relevance: {score:.0%}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return f"Failed to recall memories: {str(e)}"


class ForgetTool(BaseTool):
    """Remove a specific memory by ID."""

    name = "forget"
    description = (
        "Delete a specific memory by its ID. "
        "Use this to remove outdated or incorrect information. "
        "First use 'recall' to find the memory ID you want to delete."
    )
    parameters = [
        ToolParameter(
            name="memory_id",
            type=ParameterType.STRING,
            description="ID of the memory to delete",
        ),
    ]

    def __init__(self, agent_name: str = "unknown"):
        """Initialize with agent identity."""
        super().__init__()
        self.agent_name = agent_name

    async def execute(self, memory_id: str) -> str:
        """
        Delete a memory by ID.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            Confirmation or error message
        """
        from memory import get_memory_service

        logger.debug(f"Agent '{self.agent_name}' forgetting: {memory_id}")

        try:
            service = get_memory_service()
            success = service.delete(memory_id)

            if success:
                return f"Successfully deleted memory: {memory_id}"
            else:
                return f"Failed to delete memory: {memory_id} (not found or already deleted)"

        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return f"Failed to delete memory: {str(e)}"


class ListMemoriesTool(BaseTool):
    """List all memories, optionally filtered by agent."""

    name = "list_memories"
    description = (
        "List all stored memories. "
        "Use this to see what information has been remembered. "
        "Can filter to show only memories from a specific agent."
    )
    parameters = [
        ToolParameter(
            name="agent_filter",
            type=ParameterType.STRING,
            description="Filter by agent name (optional)",
            required=False,
        ),
        ToolParameter(
            name="limit",
            type=ParameterType.INTEGER,
            description="Maximum number of memories to show",
            required=False,
            default=20,
        ),
    ]

    def __init__(self, agent_name: str = "unknown"):
        """Initialize with agent identity."""
        super().__init__()
        self.agent_name = agent_name

    async def execute(
        self,
        agent_filter: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """
        List memories.

        Args:
            agent_filter: Optional agent name to filter by
            limit: Maximum memories to show

        Returns:
            Formatted list of memories
        """
        from memory import get_memory_service
        from memory.user_profile import DEFAULT_USER_ID

        logger.debug(f"Agent '{self.agent_name}' listing memories")

        try:
            service = get_memory_service()
            all_memories = service.get_all(user_id=DEFAULT_USER_ID)

            if not all_memories:
                return "No memories stored yet."

            # Handle mem0 response format
            if isinstance(all_memories, dict):
                memories = all_memories.get("results", [])
            else:
                memories = all_memories

            # Filter by agent if specified
            if agent_filter:
                memories = [
                    m for m in memories
                    if m.get("metadata", {}).get("agent") == agent_filter
                ]

            if not memories:
                if agent_filter:
                    return f"No memories found from agent: {agent_filter}"
                return "No memories stored yet."

            # Organize by agent
            by_agent: dict[str, list] = {}
            for mem in memories:
                agent = mem.get("metadata", {}).get("agent", "user")
                if agent not in by_agent:
                    by_agent[agent] = []
                by_agent[agent].append(mem)

            # Format output
            lines = ["Stored Memories:", ""]

            count = 0
            for agent in sorted(by_agent.keys()):
                agent_mems = by_agent[agent]
                lines.append(f"📁 {agent} ({len(agent_mems)} memories)")

                for mem in agent_mems[:5]:  # Show first 5 per agent
                    if count >= limit:
                        break
                    content = mem.get("memory", mem.get("content", ""))[:80]
                    category = mem.get("metadata", {}).get("category", "general")
                    lines.append(f"   • [{category}] {content}...")
                    count += 1

                if len(agent_mems) > 5:
                    lines.append(f"   ... and {len(agent_mems) - 5} more")
                lines.append("")

                if count >= limit:
                    break

            total = len(memories)
            lines.append(f"Total: {total} memories from {len(by_agent)} agents")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return f"Failed to list memories: {str(e)}"


def create_memory_tools(agent_name: str) -> List[BaseTool]:
    """
    Create memory tools configured for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., "code_lead")

    Returns:
        List of configured memory tool instances
    """
    return [
        RememberTool(agent_name),
        RecallTool(agent_name),
        ForgetTool(agent_name),
        ListMemoriesTool(agent_name),
    ]


# Default tool instances (for backward compatibility)
remember = RememberTool("unknown")
recall = RecallTool("unknown")
forget = ForgetTool("unknown")
list_memories = ListMemoriesTool("unknown")

# All memory tools (default instances)
MEMORY_TOOLS = [remember, recall, forget, list_memories]
