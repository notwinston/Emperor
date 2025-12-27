"""Researcher Worker for Emperor AI Assistant.

A focused worker that gathers and analyzes information.
Spawned by Research Lead for research subtasks.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, ListDirectoryTool
from sdk.tools.search_tools import GrepTool, GlobTool
from sdk.tools.memory_tools import RecallTool

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Researcher(BaseAgent):
    """
    Researcher Worker - Gathers information.

    Has tools focused on research:
    - File reading
    - Code/file searching
    - Web search (built-in)
    - Memory recall

    Usage:
        >>> researcher = Researcher()
        >>> result = await researcher.run("Find all usages of JWT in the codebase")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 10,
        max_web_searches: int = 3,
    ):
        super().__init__(
            name="researcher",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._max_web_searches = max_web_searches
        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.debug("Researcher worker initialized")

    def _setup_tools(self) -> None:
        """Set up tools - focused on research."""
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())
        self._tool_registry_obj.register(GrepTool())
        self._tool_registry_obj.register(GlobTool())

        # Read-only memory access
        self._tool_registry_obj.register(RecallTool("researcher"))

        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

    def get_system_prompt(self) -> str:
        return load_prompt(PROMPTS_DIR, "researcher")

    def get_tools(self) -> list[dict[str, Any]]:
        tools = self._tool_registry_obj.get_definitions()

        # Add built-in web search
        tools.append({
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": self._max_web_searches,
        })

        return tools
