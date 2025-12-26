"""Base Tool class for SDK agent tools.

This module provides the abstract base class for defining tools
that SDK agents can use. Tools follow the Anthropic API format
for tool definitions and include input validation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from config import get_logger

logger = get_logger(__name__)


class ParameterType(str, Enum):
    """JSON Schema types for tool parameters."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    enum: Optional[list[str]] = None
    default: Optional[Any] = None
    items: Optional[dict[str, Any]] = None  # For array types

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.default is not None:
            schema["default"] = self.default

        if self.items and self.type == ParameterType.ARRAY:
            schema["items"] = self.items

        return schema


@dataclass
class ToolDefinition:
    """Complete tool definition for Anthropic API."""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)

    def to_api_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic API tool definition format.

        Returns:
            Dict matching Anthropic's tool definition schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class BaseTool(ABC):
    """
    Abstract base class for SDK agent tools.

    Subclasses must implement:
    - name: Tool identifier
    - description: What the tool does
    - parameters: List of ToolParameter definitions
    - execute(): The tool logic

    Example:
        class ReadFileTool(BaseTool):
            name = "read_file"
            description = "Read contents of a file"
            parameters = [
                ToolParameter(
                    name="path",
                    type=ParameterType.STRING,
                    description="Path to the file",
                ),
            ]

            async def execute(self, path: str) -> str:
                with open(path, 'r') as f:
                    return f.read()
    """

    # Subclasses must define these
    name: str
    description: str
    parameters: list[ToolParameter] = []

    # Optional Pydantic model for input validation
    input_model: Optional[type[BaseModel]] = None

    def get_definition(self) -> ToolDefinition:
        """
        Get the tool definition.

        Returns:
            ToolDefinition for this tool
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def to_api_format(self) -> dict[str, Any]:
        """
        Get the API format for this tool.

        Returns:
            Dict matching Anthropic's tool definition schema
        """
        return self.get_definition().to_api_format()

    def validate_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate input data against the tool's schema.

        Args:
            input_data: Input dict from the tool call

        Returns:
            Validated input data

        Raises:
            ValueError: If validation fails
        """
        # Use Pydantic model if defined
        if self.input_model:
            try:
                validated = self.input_model(**input_data)
                return validated.model_dump()
            except ValidationError as e:
                raise ValueError(f"Invalid input: {e}")

        # Basic validation against parameters
        validated = {}
        for param in self.parameters:
            if param.name in input_data:
                validated[param.name] = input_data[param.name]
            elif param.required:
                raise ValueError(f"Missing required parameter: {param.name}")
            elif param.default is not None:
                validated[param.name] = param.default

        return validated

    async def run(self, input_data: dict[str, Any]) -> str:
        """
        Run the tool with validation.

        Args:
            input_data: Input dict from the tool call

        Returns:
            Tool output as string

        Raises:
            ValueError: If validation fails
            Exception: If execution fails
        """
        logger.debug(f"Running tool '{self.name}' with input: {input_data}")

        # Validate input
        validated_input = self.validate_input(input_data)

        # Execute tool
        try:
            result = await self.execute(**validated_input)
            logger.debug(f"Tool '{self.name}' completed successfully")
            return str(result)
        except Exception as e:
            logger.error(f"Tool '{self.name}' failed: {e}")
            raise

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool logic.

        Args:
            **kwargs: Validated input parameters

        Returns:
            Tool output (will be converted to string)
        """
        pass


class ToolRegistry:
    """
    Registry for managing available tools.

    Provides a central place to register and retrieve tools,
    generate tool definitions for API calls, and create
    handler functions for agent tool execution.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: The tool instance to register
        """
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> None:
        """
        Unregister a tool.

        Args:
            name: Name of the tool to remove
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            The tool instance or None
        """
        return self._tools.get(name)

    def get_definitions(self) -> list[dict[str, Any]]:
        """
        Get API definitions for all registered tools.

        Returns:
            List of tool definitions in Anthropic API format
        """
        return [tool.to_api_format() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """
        Get names of all registered tools.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    async def execute(self, name: str, input_data: dict[str, Any]) -> str:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            input_data: Input data for the tool

        Returns:
            Tool output as string

        Raises:
            ValueError: If tool not found
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        return await tool.run(input_data)

    def create_handler(self, name: str) -> callable:
        """
        Create an async handler function for a tool.

        Useful for registering with BaseAgent.register_tool().

        Args:
            name: Tool name

        Returns:
            Async handler function
        """
        async def handler(input_data: dict[str, Any]) -> str:
            return await self.execute(name, input_data)

        return handler
