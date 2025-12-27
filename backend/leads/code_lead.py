"""Code Lead Agent for Emperor AI Assistant.

The Code Lead is a Domain Lead that handles all code-related tasks:
- Architecture decisions and design patterns
- Code reviews and quality assessment
- Refactoring and optimization
- File operations and project structure

The Code Lead has full access to memory tools for storing and
recalling code patterns, project context, and user preferences.
"""

from pathlib import Path
from typing import Any, Optional

from config import get_logger
from sdk.base_agent import BaseAgent, load_prompt
from sdk.tools.base import ToolRegistry
from sdk.tools.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from sdk.tools.memory_tools import create_memory_tools

logger = get_logger(__name__)

# Path to system prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


class CodeLead(BaseAgent):
    """
    Code Lead Agent - Domain Lead for all code-related tasks.

    Uses the inherited run() method for all tasks:
        >>> lead = get_code_lead()
        >>> result = await lead.run("Refactor auth module to use JWT")
        >>> result = await lead.run("Review /path/to/file.py for security")
        >>> result = await lead.run("Create a new API endpoint for users")
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        max_turns: int = 15,
    ):
        """
        Initialize the Code Lead.

        Args:
            client: SDK client instance. Uses singleton if not provided.
            model: Model override. Uses client default if not provided.
            max_turns: Maximum conversation turns (default 15 for complex tasks)
        """
        super().__init__(
            name="code_lead",
            client=client,
            model=model,
            max_turns=max_turns,
        )

        # Initialize tool registry
        self._tool_registry_obj = ToolRegistry()
        self._setup_tools()

        logger.info("Code Lead initialized")

    def _setup_tools(self) -> None:
        """Set up tools available to the Code Lead."""
        # File tools
        self._tool_registry_obj.register(ReadFileTool())
        self._tool_registry_obj.register(WriteFileTool())
        self._tool_registry_obj.register(ListDirectoryTool())

        # Memory tools (configured with agent name)
        for tool in create_memory_tools("code_lead"):
            self._tool_registry_obj.register(tool)

        # Register handlers with base agent
        for name in self._tool_registry_obj.get_tool_names():
            self.register_tool(name, self._tool_registry_obj.create_handler(name))

        logger.debug(f"Code Lead tools: {self._tool_registry_obj.get_tool_names()}")

    def get_system_prompt(self) -> str:
        """Load and return the Code Lead's system prompt from prompts/code_lead.md."""
        return load_prompt(PROMPTS_DIR, "code_lead")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for the Anthropic API."""
        return self._tool_registry_obj.get_definitions()


# Singleton instance
_code_lead: Optional[CodeLead] = None


def get_code_lead() -> CodeLead:
    """
    Get the Code Lead singleton.

    Returns:
        The shared CodeLead instance.
    """
    global _code_lead
    if _code_lead is None:
        _code_lead = CodeLead()
    return _code_lead


def reset_code_lead() -> None:
    """Reset the Code Lead singleton."""
    global _code_lead
    _code_lead = None
