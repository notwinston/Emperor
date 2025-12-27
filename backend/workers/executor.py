"""Executor Worker for Emperor AI Assistant.

A focused worker that runs shell commands and scripts.
Spawned by Task Lead for execution subtasks.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, ListDirectoryTool
from sdk.tools.shell_tools import ExecuteCommandTool
from sdk.tools.memory_tools import RecallTool

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Executor(BaseAgent):
    """
    Executor Worker - Runs commands and scripts.

    Has tools focused on execution:
    - Shell command execution
    - File reading (for scripts/configs)
    - Memory recall

    Usage:
        >>> executor = Executor()
        >>> result = await executor.run("Run npm test")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 10,
    ):
        super().__init__(
            name="executor",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.debug("Executor worker initialized")

    def _setup_tools(self) -> None:
        """Set up tools - focused on execution."""
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())
        self._tool_registry_obj.register(ExecuteCommandTool())

        # Read-only memory access
        self._tool_registry_obj.register(RecallTool("executor"))

        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

    def get_system_prompt(self) -> str:
        return load_prompt(PROMPTS_DIR, "executor")

    def get_tools(self) -> list[dict[str, Any]]:
        return self._tool_registry_obj.get_definitions()
