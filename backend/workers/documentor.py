"""Documentor Worker for Emperor AI Assistant.

A focused worker that writes documentation and comments.
Spawned by Code Lead for documentation tasks.
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


class Documentor(BaseAgent):
    """
    Documentor Worker - Writes documentation.

    Has tools focused on documentation:
    - File read/write
    - Memory recall

    Usage:
        >>> documentor = Documentor()
        >>> result = await documentor.run("Write API docs for auth module")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 10,
    ):
        super().__init__(
            name="documentor",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.debug("Documentor worker initialized")

    def _setup_tools(self) -> None:
        """Set up tools - focused on documentation."""
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(WriteFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())

        # Read-only memory access
        self._tool_registry_obj.register(RecallTool("documentor"))

        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

    def get_system_prompt(self) -> str:
        return load_prompt(PROMPTS_DIR, "documentor")

    def get_tools(self) -> list[dict[str, Any]]:
        return self._tool_registry_obj.get_definitions()
