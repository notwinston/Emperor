"""Base Agent class for SDK-based agents in Emperor AI Assistant.

This module provides the abstract base class that all Domain Leads
and Workers extend. It implements the agent loop:
1. Receive task and context
2. Generate response (may include tool calls)
3. Execute tool calls if any
4. Repeat until task complete
5. Return result
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional

from config import get_logger
from .client import get_sdk_client, SDKClient

logger = get_logger(__name__)


class AgentStatus(str, Enum):
    """Status of an agent execution."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentResult:
    """Result of an agent execution."""
    success: bool
    content: str
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ToolCall:
    """A tool call from the agent."""
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool."""
    tool_use_id: str
    content: str
    is_error: bool = False


class BaseAgent(ABC):
    """
    Abstract base class for all SDK-based agents.

    Provides the core agent loop and tool execution framework.
    Subclasses must implement:
    - get_system_prompt(): Return the agent's system prompt
    - get_tools(): Return list of tool definitions

    Optionally override:
    - execute_tool(): Custom tool execution logic
    """

    def __init__(
        self,
        name: str,
        client: Optional[SDKClient] = None,
        model: Optional[str] = None,
        max_turns: int = 10,
    ):
        """
        Initialize the agent.

        Args:
            name: Agent identifier (e.g., "code_lead", "programmer")
            client: SDK client instance. Uses singleton if not provided.
            model: Model override. Uses client default if not provided.
            max_turns: Maximum conversation turns before stopping
        """
        self.name = name
        self.client = client or get_sdk_client()
        self.model = model
        self.max_turns = max_turns
        self.status = AgentStatus.IDLE
        self._conversation_history: list[dict[str, Any]] = []
        self._tool_registry: dict[str, callable] = {}

        logger.debug(f"Agent '{name}' initialized")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the agent's system prompt.

        This defines the agent's role, responsibilities, and behavior.
        Must be implemented by subclasses.

        Returns:
            The system prompt string
        """
        pass

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """
        Return list of tool definitions for this agent.

        Tool definitions follow the Anthropic API format:
        {
            "name": "tool_name",
            "description": "What the tool does",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

        Returns:
            List of tool definition dicts
        """
        pass

    def register_tool(self, name: str, handler: callable) -> None:
        """
        Register a tool handler function.

        Args:
            name: Tool name (must match definition)
            handler: Async function that executes the tool
        """
        self._tool_registry[name] = handler
        logger.debug(f"Registered tool '{name}' for agent '{self.name}'")

    async def run(
        self,
        task: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Execute a task and return the result.

        This is the main agent loop:
        1. Add task to conversation
        2. Get response from Claude
        3. If response has tool calls, execute them and continue
        4. If response is text only, return it
        5. Repeat until max_turns or stop_reason == "end_turn"

        Args:
            task: The task description
            context: Optional additional context

        Returns:
            AgentResult with the outcome
        """
        logger.info(f"Agent '{self.name}' starting task: {task[:50]}...")
        self.status = AgentStatus.RUNNING
        self._conversation_history = []
        tool_results_collected: list[dict[str, Any]] = []

        try:
            # Build initial message
            user_message = self._build_user_message(task, context)
            self._conversation_history.append({
                "role": "user",
                "content": user_message,
            })

            # Agent loop
            for turn in range(self.max_turns):
                logger.debug(f"Agent '{self.name}' turn {turn + 1}/{self.max_turns}")

                # Get response from Claude
                response = await self.client.create_message_async(
                    messages=self._conversation_history,
                    system=self.get_system_prompt(),
                    tools=self.get_tools() or None,
                    model=self.model,
                )

                # Extract content blocks
                content_blocks = response.content
                stop_reason = response.stop_reason

                # Process content blocks
                text_content = ""
                tool_calls: list[ToolCall] = []

                for block in content_blocks:
                    if block.type == "text":
                        text_content += block.text
                    elif block.type == "tool_use":
                        tool_calls.append(ToolCall(
                            id=block.id,
                            name=block.name,
                            input=block.input,
                        ))

                # Add assistant response to history
                self._conversation_history.append({
                    "role": "assistant",
                    "content": content_blocks,
                })

                # If no tool calls, we're done
                if not tool_calls:
                    logger.info(f"Agent '{self.name}' completed task")
                    self.status = AgentStatus.COMPLETED
                    return AgentResult(
                        success=True,
                        content=text_content,
                        tool_results=tool_results_collected,
                        metadata={
                            "turns": turn + 1,
                            "model": response.model,
                            "stop_reason": stop_reason,
                        },
                    )

                # Execute tool calls
                self.status = AgentStatus.WAITING_TOOL
                tool_results: list[ToolResult] = []

                for tool_call in tool_calls:
                    logger.debug(f"Executing tool '{tool_call.name}'")
                    result = await self.execute_tool(tool_call)
                    tool_results.append(result)
                    tool_results_collected.append({
                        "tool": tool_call.name,
                        "input": tool_call.input,
                        "output": result.content,
                        "is_error": result.is_error,
                    })

                # Add tool results to conversation
                self._conversation_history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": r.tool_use_id,
                            "content": r.content,
                            "is_error": r.is_error,
                        }
                        for r in tool_results
                    ],
                })

                self.status = AgentStatus.RUNNING

            # Max turns reached
            logger.warning(f"Agent '{self.name}' reached max turns ({self.max_turns})")
            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                content=text_content if text_content else "Task incomplete - max turns reached",
                tool_results=tool_results_collected,
                metadata={
                    "turns": self.max_turns,
                    "max_turns_reached": True,
                },
            )

        except Exception as e:
            logger.error(f"Agent '{self.name}' error: {e}", exc_info=True)
            self.status = AgentStatus.ERROR
            return AgentResult(
                success=False,
                content="",
                error=str(e),
            )

    async def stream_run(
        self,
        task: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream the agent's response as it generates.

        Note: This is a simplified streaming implementation.
        For full streaming with tool execution, use run() instead.

        Args:
            task: The task description
            context: Optional additional context

        Yields:
            Response text chunks
        """
        # For now, use non-streaming and yield the full result
        # Full streaming implementation would require stream=True API calls
        result = await self.run(task, context)

        if result.success:
            yield result.content
        else:
            yield f"Error: {result.error}"

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Override this method to customize tool execution.
        Default implementation looks up handler in registry.

        Args:
            tool_call: The tool call to execute

        Returns:
            ToolResult with the output
        """
        handler = self._tool_registry.get(tool_call.name)

        if not handler:
            logger.warning(f"No handler for tool '{tool_call.name}'")
            return ToolResult(
                tool_use_id=tool_call.id,
                content=f"Tool '{tool_call.name}' not implemented",
                is_error=True,
            )

        try:
            result = await handler(tool_call.input)
            return ToolResult(
                tool_use_id=tool_call.id,
                content=str(result),
                is_error=False,
            )
        except Exception as e:
            logger.error(f"Tool '{tool_call.name}' error: {e}")
            return ToolResult(
                tool_use_id=tool_call.id,
                content=f"Error executing tool: {e}",
                is_error=True,
            )

    def _build_user_message(
        self,
        task: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Build the initial user message with task and context.

        Args:
            task: The task description
            context: Optional additional context

        Returns:
            Formatted message string
        """
        parts = [f"<task>\n{task}\n</task>"]

        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
            parts.append(f"<context>\n{context_str}\n</context>")

        return "\n\n".join(parts)

    def reset(self) -> None:
        """Reset the agent state for a new task."""
        self._conversation_history = []
        self.status = AgentStatus.IDLE
        logger.debug(f"Agent '{self.name}' reset")
