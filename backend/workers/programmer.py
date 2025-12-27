"""Programmer Worker for Emperor AI Assistant.

A focused worker that writes and modifies code.
Spawned by Code Lead for implementation tasks.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from sdk.tools.memory_tools import RecallTool

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Programmer(BaseAgent):
    """
    Programmer Worker - Writes and modifies code.

    Has limited tools focused on code implementation:
    - File read/write
    - Memory recall (read-only)

    Usage:
        >>> programmer = Programmer()
        >>> result = await programmer.run("Implement a JWT auth decorator")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 10,
    ):
        super().__init__(
            name="programmer",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.debug("Programmer worker initialized")

    def _setup_tools(self) -> None:
        """Set up tools - focused on code writing."""
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(WriteFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())

        # Read-only memory access
        self._tool_registry_obj.register(RecallTool("programmer"))

        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

    def get_system_prompt(self) -> str:
        return load_prompt(PROMPTS_DIR, "programmer")

    def get_tools(self) -> list[dict[str, Any]]:
        return self._tool_registry_obj.get_definitions()
