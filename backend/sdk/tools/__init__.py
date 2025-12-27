"""Tool definitions for SDK-based agents.

This module provides the tool infrastructure for Domain Leads and Workers:
- Base tool class with validation
- Common tool implementations
- Tool registry for agent use
"""

from .base import (
    BaseTool,
    ToolDefinition,
    ToolParameter,
    ParameterType,
    ToolRegistry,
)

# File tools
from .file_tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    read_file,
    write_file,
    list_directory,
    FILE_TOOLS,
)

# Search tools
from .search_tools import (
    GrepTool,
    GlobTool,
    grep,
    glob_search,
    get_web_search_tool_definition,
    SEARCH_TOOLS,
)

# Shell tools
from .shell_tools import (
    ExecuteCommandTool,
    BackgroundCommandTool,
    execute_command,
    background_command,
    set_approval_callback,
    SHELL_TOOLS,
)

# Memory tools
from .memory_tools import (
    RememberTool,
    RecallTool,
    ForgetTool,
    ListMemoriesTool,
    create_memory_tools,
    remember,
    recall,
    forget,
    list_memories,
    MEMORY_TOOLS,
)

# All tools combined
ALL_TOOLS = FILE_TOOLS + SEARCH_TOOLS + SHELL_TOOLS + MEMORY_TOOLS


def get_all_tool_definitions() -> list[dict]:
    """Get API definitions for all common tools."""
    return [tool.to_api_format() for tool in ALL_TOOLS]


def create_default_registry() -> ToolRegistry:
    """Create a registry with all common tools registered."""
    registry = ToolRegistry()
    for tool in ALL_TOOLS:
        registry.register(tool)
    return registry


__all__ = [
    # Base
    "BaseTool",
    "ToolDefinition",
    "ToolParameter",
    "ParameterType",
    "ToolRegistry",
    # File tools
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "read_file",
    "write_file",
    "list_directory",
    "FILE_TOOLS",
    # Search tools
    "GrepTool",
    "GlobTool",
    "grep",
    "glob_search",
    "get_web_search_tool_definition",
    "SEARCH_TOOLS",
    # Shell tools
    "ExecuteCommandTool",
    "BackgroundCommandTool",
    "execute_command",
    "background_command",
    "set_approval_callback",
    "SHELL_TOOLS",
    # Memory tools
    "RememberTool",
    "RecallTool",
    "ForgetTool",
    "ListMemoriesTool",
    "create_memory_tools",
    "remember",
    "recall",
    "forget",
    "list_memories",
    "MEMORY_TOOLS",
    # Utilities
    "ALL_TOOLS",
    "get_all_tool_definitions",
    "create_default_registry",
]
