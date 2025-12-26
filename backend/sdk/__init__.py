"""Anthropic SDK module for Emperor AI Assistant.

This module provides the SDK infrastructure for Domain Leads and Workers:
- SDK client wrapper for API access
- Base agent class for consistent behavior
- Tool definitions and executors
"""

from .client import SDKClient, get_sdk_client
from .base_agent import BaseAgent, AgentResult, AgentStatus

# Import tool utilities
from .tools import (
    BaseTool,
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ParameterType,
    ALL_TOOLS,
    get_all_tool_definitions,
    create_default_registry,
)

__all__ = [
    # Client
    "SDKClient",
    "get_sdk_client",
    # Agent
    "BaseAgent",
    "AgentResult",
    "AgentStatus",
    # Tools
    "BaseTool",
    "ToolRegistry",
    "ToolDefinition",
    "ToolParameter",
    "ParameterType",
    "ALL_TOOLS",
    "get_all_tool_definitions",
    "create_default_registry",
]
