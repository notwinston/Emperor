"""Reviewer Worker for Emperor AI Assistant.

A focused worker that reviews code for issues and improvements.
Spawned by Code Lead for code review tasks.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, ListDirectoryTool
from sdk.tools.search_tools import GrepTool
from sdk.tools.memory_tools import RecallTool

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Reviewer(BaseAgent):
    """
    Reviewer Worker - Reviews code for issues.

    Has read-only tools focused on code analysis:
    - File reading
    - Code searching
    - Memory recall

    Usage:
        >>> reviewer = Reviewer()
        >>> result = await reviewer.run("Review auth.py for security issues")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 10,
    ):
        super().__init__(
            name="reviewer",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.debug("Reviewer worker initialized")

    def _setup_tools(self) -> None:
        """Set up tools - read-only for review."""
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())
        self._tool_registry_obj.register(GrepTool())

        # Read-only memory access
        self._tool_registry_obj.register(RecallTool("reviewer"))

        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

    def get_system_prompt(self) -> str:
        return load_prompt(PROMPTS_DIR, "reviewer")

    def get_tools(self) -> list[dict[str, Any]]:
        return self._tool_registry_obj.get_definitions()
