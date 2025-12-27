"""Task Lead Agent for Emperor AI Assistant.

The Task Lead is a Domain Lead that handles automation and system operations:
- Shell command execution
- Workflow automation
- Build and deployment tasks
- System monitoring

The Task Lead has safety controls for dangerous commands and stores
workflow patterns in memory for future reference.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, ListDirectoryTool
from sdk.tools.shell_tools import ExecuteCommandTool, BackgroundCommandTool
from sdk.tools.memory_tools import create_memory_tools

logger = get_logger(__name__)

# Path to system prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


class TaskLead(BaseAgent):
    """
    Task Lead Agent - Domain Lead for automation and system operations.

    Uses the inherited run() method for all tasks:
        >>> lead = get_task_lead()
        >>> result = await lead.run("Run the test suite")
        >>> result = await lead.run("Build the project and check for errors")
        >>> result = await lead.run("Start the development server")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 20,
    ):
        """
        Initialize the Task Lead.

        Args:
            client: SDK client instance. Uses singleton if not provided.
            model: Model override. Uses client default if not provided.
            max_turns: Maximum conversation turns (default 20 for complex workflows)
        """
        super().__init__(
            name="task_lead",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        # Initialize tool registry
        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.info("Task Lead initialized")

    def _setup_tools(self) -> None:
        """Set up tools available to the Task Lead."""
        # File reading for configs
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())

        # Shell execution tools
        self._tool_registry_obj.register(ExecuteCommandTool())
        self._tool_registry_obj.register(BackgroundCommandTool())

        # Memory tools (configured with agent name)
        for tool in create_memory_tools("task_lead"):
            self._tool_registry_obj.register(tool)

        # Register handlers with base agent
        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

        logger.debug(f"Task Lead tools: {self._tool_registry_obj.get_tool_names()}")

    def get_system_prompt(self) -> str:
        """Load and return the Task Lead's system prompt from prompts/task_lead.md."""
        return load_prompt(PROMPTS_DIR, "task_lead")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for the Anthropic API."""
        return self._tool_registry_obj.get_definitions()


# Singleton instance
_task_lead: Optional[TaskLead] = None


def get_task_lead() -> TaskLead:
    """
    Get the Task Lead singleton.

    Returns:
        The shared TaskLead instance.
    """
    global _task_lead
    if _task_lead is None:
        _task_lead = TaskLead()
    return _task_lead


def reset_task_lead() -> None:
    """Reset the Task Lead singleton."""
    global _task_lead
    _task_lead = None
