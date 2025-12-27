"""Research Lead Agent for Emperor AI Assistant.

The Research Lead is a Domain Lead that handles all research and analysis tasks:
- Web research and information gathering
- Document analysis and summarization
- Source tracking and citations
- Knowledge synthesis

The Research Lead uses Anthropic's built-in web search tool for real-time
web access with automatic citations.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, ListDirectoryTool
from sdk.tools.search_tools import GrepTool, GlobTool
from sdk.tools.memory_tools import create_memory_tools

logger = get_logger(__name__)

# Path to system prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


class ResearchLead(BaseAgent):
    """
    Research Lead Agent - Domain Lead for research and analysis tasks.

    Uses the inherited run() method for all tasks:
        >>> lead = get_research_lead()
        >>> result = await lead.run("What are the best practices for OAuth2 in Python?")
        >>> result = await lead.run("Summarize the architecture of this codebase")
        >>> result = await lead.run("Find documentation for FastAPI WebSockets")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 15,
        max_web_searches: int = 5,
    ):
        """
        Initialize the Research Lead.

        Args:
            client: SDK client instance. Uses singleton if not provided.
            model: Model override. Uses client default if not provided.
            max_turns: Maximum conversation turns (default 15 for complex research)
            max_web_searches: Maximum web searches per request (default 5)
        """
        super().__init__(
            name="research_lead",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._max_web_searches = max_web_searches

        # Initialize tool registry
        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.info("Research Lead initialized")

    def _setup_tools(self) -> None:
        """Set up tools available to the Research Lead."""
        # File reading (no write access for research)
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())

        # Search tools for codebase exploration
        self._tool_registry_obj.register(GrepTool())
        self._tool_registry_obj.register(GlobTool())

        # Memory tools (configured with agent name)
        for tool in create_memory_tools("research_lead"):
            self._tool_registry_obj.register(tool)

        # Register handlers with base agent
        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

        logger.debug(f"Research Lead tools: {self._tool_registry_obj.get_tool_names()}")

    def get_system_prompt(self) -> str:
        """Load and return the Research Lead's system prompt from prompts/research_lead.md."""
        return load_prompt(PROMPTS_DIR, "research_lead")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions including Anthropic's built-in web search."""
        # Get custom tool definitions
        tools = self._tool_registry_obj.get_definitions()

        # Add Anthropic's built-in web search tool
        tools.append({
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": self._max_web_searches,
        })

        return tools


# Singleton instance
_research_lead: Optional[ResearchLead] = None


def get_research_lead() -> ResearchLead:
    """
    Get the Research Lead singleton.

    Returns:
        The shared ResearchLead instance.
    """
    global _research_lead
    if _research_lead is None:
        _research_lead = ResearchLead()
    return _research_lead


def reset_research_lead() -> None:
    """Reset the Research Lead singleton."""
    global _research_lead
    _research_lead = None
