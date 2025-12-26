"""Orchestrator implementation for Emperor AI Assistant.

The Orchestrator routes user messages through the Claude Code CLI,
classifies intent, and delegates to SDK-based Domain Leads when needed.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from config import settings, get_logger
from claude_code_bridge import get_bridge, BridgeError
from .intent_classifier import (
    IntentClassifier,
    IntentType,
    IntentResult,
    DelegationTarget,
    get_classifier,
)
from .delegation import (
    DelegationType,
    DelegationContext,
    DelegationRequest,
    DelegationResult,
    DelegationManager,
    get_delegation_manager,
    Priority,
)
from .memory_integration import (
    MemoryContext,
    MemoryRetriever,
    get_memory_retriever,
)

logger = get_logger(__name__)


@dataclass
class OrchestratorResult:
    """Result from orchestrator processing."""
    content: str
    delegation: DelegationType = DelegationType.NONE
    delegation_task: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Delegation pattern matcher
DELEGATION_PATTERN = re.compile(
    r"\[DELEGATE:(CODE|RESEARCH|TASK)\]\s*(.+?)(?:\n|$)",
    re.IGNORECASE
)


class Orchestrator:
    """
    Main orchestrator for Emperor AI Assistant.

    Uses Claude Code CLI to:
    - Process user messages
    - Classify intent
    - Delegate to Domain Leads when needed
    - Return responses to users
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self._system_prompt: Optional[str] = None
        self._conversation_history: list[dict[str, str]] = []
        self._max_history = 10  # Keep last N messages for context
        self._classifier = get_classifier()
        self._delegation_manager = get_delegation_manager()
        self._memory_retriever = get_memory_retriever()
        self._last_intent: Optional[IntentResult] = None
        self._last_memory_context: Optional[MemoryContext] = None
        self._session_id: Optional[str] = None

    def _build_delegation_context(
        self,
        memory_context: Optional[MemoryContext] = None,
    ) -> DelegationContext:
        """Build context for delegation requests."""
        ctx = DelegationContext(
            conversation_history=self._conversation_history[-self._max_history:],
            session_id=self._session_id,
            memory_context=memory_context or self._last_memory_context,
        )

        # Populate legacy fields from memory context for backwards compatibility
        if ctx.memory_context:
            ctx.user_profile = ctx.memory_context.user_profile.to_prompt_string() if ctx.memory_context.user_profile.name else {}
            ctx.related_facts = [f.value for f in ctx.memory_context.relevant_facts]

        return ctx

    def _create_delegation_request(
        self,
        delegation_type: DelegationType,
        task: str,
        original_message: str,
        priority: Priority = Priority.MEDIUM,
    ) -> DelegationRequest:
        """Create a delegation request with full context."""
        return DelegationRequest(
            delegation_type=delegation_type,
            task=task,
            original_message=original_message,
            context=self._build_delegation_context(),
            priority=priority,
        )

    def _retrieve_memory_context(self, message: str) -> MemoryContext:
        """
        Retrieve memory context for the current request.

        Args:
            message: The user's message

        Returns:
            MemoryContext with user profile, relevant facts, and session history
        """
        try:
            context = self._memory_retriever.retrieve_context(
                query=message,
                include_profile=True,
                include_facts=True,
                include_sessions=True,
                max_facts=10,
                max_sessions=3,
            )

            self._last_memory_context = context

            if context.has_context():
                logger.debug(
                    f"Memory context retrieved: "
                    f"profile={context.user_profile.name is not None}, "
                    f"facts={len(context.relevant_facts)}, "
                    f"sessions={len(context.recent_sessions)}"
                )
            else:
                logger.debug("No memory context found")

            return context

        except Exception as e:
            logger.warning(f"Failed to retrieve memory context: {e}")
            return MemoryContext()

    def _extract_memories_from_conversation(
        self,
        message: str,
        response: str,
    ) -> None:
        """
        Extract and store facts from the conversation.

        Called after processing to capture new information.
        """
        try:
            stored_keys = self._memory_retriever.extract_and_store_facts(
                message=message,
                response=response,
            )
            if stored_keys:
                logger.debug(f"Extracted memories: {stored_keys}")
        except Exception as e:
            logger.warning(f"Failed to extract memories: {e}")

    @property
    def last_memory_context(self) -> Optional[MemoryContext]:
        """Get the last retrieved memory context."""
        return self._last_memory_context

    @property
    def system_prompt(self) -> str:
        """Load and cache the main assistant system prompt."""
        if self._system_prompt is None:
            # Primary: Persistent AI Assistant prompt
            prompt_path = Path(__file__).parent.parent / "config" / "prompts" / "assistant.md"

            # Fallback: Orchestrator-focused prompt
            fallback_path = Path(__file__).parent.parent / "config" / "prompts" / "orchestrator.md"

            if prompt_path.exists():
                self._system_prompt = prompt_path.read_text()
                logger.debug("Loaded assistant system prompt")
            elif fallback_path.exists():
                self._system_prompt = fallback_path.read_text()
                logger.debug("Loaded orchestrator system prompt (fallback)")
            else:
                # Minimal fallback
                self._system_prompt = (
                    "You are Emperor, an AI assistant. "
                    "Help users with their questions and tasks. "
                    "Be helpful, accurate, and concise."
                )
                logger.warning("No system prompt found, using minimal fallback")

        return self._system_prompt

    async def classify_intent(
        self,
        message: str,
        use_llm_fallback: bool = True,
    ) -> IntentResult:
        """
        Classify the intent of a user message.

        Args:
            message: The user's message
            use_llm_fallback: Whether to use LLM for low-confidence classifications

        Returns:
            IntentResult with classification details
        """
        if use_llm_fallback:
            intent = await self._classifier.classify_smart(message)
        else:
            intent = self._classifier.classify(message)

        self._last_intent = intent

        logger.info(
            f"Intent classified: {intent.intent.value} "
            f"(confidence: {intent.confidence:.2f}, delegate: {intent.delegation.value})"
        )

        return intent

    def _map_delegation_target(self, target: DelegationTarget) -> DelegationType:
        """Map DelegationTarget to DelegationType."""
        mapping = {
            DelegationTarget.NONE: DelegationType.NONE,
            DelegationTarget.CODE: DelegationType.CODE,
            DelegationTarget.RESEARCH: DelegationType.RESEARCH,
            DelegationTarget.TASK: DelegationType.TASK,
        }
        return mapping.get(target, DelegationType.NONE)

    @property
    def last_intent(self) -> Optional[IntentResult]:
        """Get the last classified intent."""
        return self._last_intent

    async def process(
        self,
        message: str,
        include_history: bool = True,
        classify_first: bool = True,
        allow_delegation: bool = True,
    ) -> OrchestratorResult:
        """
        Process a user message and return a response.

        Uses intent classification to determine handling strategy.

        Args:
            message: The user's message
            include_history: Whether to include conversation history
            classify_first: Whether to classify intent before processing
            allow_delegation: Whether to allow delegation to leads

        Returns:
            OrchestratorResult with response and delegation info
        """
        logger.info(f"Processing message: {message[:50]}...")

        # Step 0: Retrieve memory context
        memory_context = self._retrieve_memory_context(message)

        # Step 1: Classify intent
        intent: Optional[IntentResult] = None
        if classify_first:
            intent = await self.classify_intent(message, use_llm_fallback=False)

            logger.debug(
                f"Intent: {intent.intent.value}, "
                f"Confidence: {intent.confidence:.2f}, "
                f"Delegation: {intent.delegation.value}"
            )

        # Step 2: Check if delegation is appropriate
        if (
            allow_delegation
            and intent
            and intent.should_delegate
            and intent.is_confident
        ):
            delegation_type = self._map_delegation_target(intent.delegation)
            logger.info(f"Delegating to {delegation_type.value} lead")

            # Create and execute delegation request
            request = self._create_delegation_request(
                delegation_type=delegation_type,
                task=message,
                original_message=message,
            )

            try:
                result = await self._delegation_manager.delegate(request)

                # Update conversation history
                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append({"role": "assistant", "content": result.content})

                # Trim history if too long
                if len(self._conversation_history) > self._max_history * 2:
                    self._conversation_history = self._conversation_history[-self._max_history * 2:]

                return OrchestratorResult(
                    content=result.content,
                    delegation=delegation_type,
                    delegation_task=message,
                    metadata={
                        "intent": {
                            "type": intent.intent.value,
                            "confidence": intent.confidence,
                            "delegation_target": intent.delegation.value,
                        },
                        "delegation_result": {
                            "success": result.success,
                            "lead_name": result.lead_name,
                            "execution_time_ms": result.execution_time_ms,
                        },
                    },
                )

            except Exception as e:
                logger.error(f"Delegation error: {e}", exc_info=True)
                # Fall through to direct handling

        # Step 3: Handle directly via Claude Code CLI
        bridge = get_bridge()
        history = self._conversation_history[-self._max_history:] if include_history else None

        try:
            # Query Claude via CLI with context
            response = await bridge.query_with_context(
                prompt=message,
                system_context=self.system_prompt,
                conversation_history=history,
                timeout=120,
                allowed_tools=None,
            )

            # Update conversation history
            self._conversation_history.append({"role": "user", "content": message})
            self._conversation_history.append({"role": "assistant", "content": response})

            # Trim history if too long
            if len(self._conversation_history) > self._max_history * 2:
                self._conversation_history = self._conversation_history[-self._max_history * 2:]

            # Check for delegation markers in response
            result = self._parse_response(response)

            # Add intent info to metadata
            if intent:
                result.metadata["intent"] = {
                    "type": intent.intent.value,
                    "confidence": intent.confidence,
                    "delegation_target": intent.delegation.value,
                    "reasoning": intent.reasoning,
                }

            # Execute delegation if markers found
            if allow_delegation and result.delegation != DelegationType.NONE and result.delegation_task:
                logger.info(f"Executing delegation from response markers: {result.delegation.value}")

                request = self._create_delegation_request(
                    delegation_type=result.delegation,
                    task=result.delegation_task,
                    original_message=message,
                )

                try:
                    delegation_result = await self._delegation_manager.delegate(request)
                    result.content += f"\n\n{delegation_result.content}"
                    result.metadata["delegation_result"] = {
                        "success": delegation_result.success,
                        "lead_name": delegation_result.lead_name,
                        "execution_time_ms": delegation_result.execution_time_ms,
                    }
                except Exception as e:
                    logger.error(f"Post-response delegation error: {e}")

            # Add memory context info to metadata
            if memory_context and memory_context.has_context():
                result.metadata["memory"] = memory_context.to_dict()

            # Extract and store facts from conversation
            self._extract_memories_from_conversation(message, result.content)

            logger.info(f"Response generated. Delegation: {result.delegation.value}")
            return result

        except BridgeError as e:
            logger.error(f"Bridge error: {e}")
            return OrchestratorResult(
                content=f"I apologize, but I encountered an error: {e}",
                metadata={"error": str(e)},
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return OrchestratorResult(
                content="I apologize, but something went wrong. Please try again.",
                metadata={"error": str(e)},
            )

    async def process_stream(
        self,
        message: str,
        include_history: bool = True,
        classify_first: bool = True,
        allow_delegation: bool = True,
    ) -> AsyncIterator[str]:
        """
        Process a user message and stream the response.

        Uses intent classification to determine handling strategy:
        - Direct intents (casual_chat, question, opinion): Stream response directly
        - Delegation intents (code_task, research_task, automation_task):
          Delegate to appropriate Domain Lead

        Args:
            message: The user's message
            include_history: Whether to include conversation history
            classify_first: Whether to classify intent before processing
            allow_delegation: Whether to allow delegation to leads

        Yields:
            Response text chunks
        """
        logger.info(f"Processing message (streaming): {message[:50]}...")

        # Step 0: Retrieve memory context
        memory_context = self._retrieve_memory_context(message)

        # Step 1: Classify intent (fast pattern matching)
        intent: Optional[IntentResult] = None
        if classify_first:
            intent = await self.classify_intent(message, use_llm_fallback=False)

            logger.debug(
                f"Intent: {intent.intent.value}, "
                f"Confidence: {intent.confidence:.2f}, "
                f"Delegation: {intent.delegation.value}"
            )

        # Step 2: Check if delegation is appropriate
        if (
            allow_delegation
            and intent
            and intent.should_delegate
            and intent.is_confident
        ):
            delegation_type = self._map_delegation_target(intent.delegation)
            logger.info(f"Delegating to {delegation_type.value} lead")

            # Create delegation request
            request = self._create_delegation_request(
                delegation_type=delegation_type,
                task=message,
                original_message=message,
            )

            # Stream delegation response
            try:
                accumulated = ""
                async for chunk in self._delegation_manager.delegate_stream(request):
                    accumulated += chunk
                    yield chunk

                # Update conversation history
                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append({"role": "assistant", "content": accumulated})

                # Trim history if too long
                if len(self._conversation_history) > self._max_history * 2:
                    self._conversation_history = self._conversation_history[-self._max_history * 2:]

                # Extract and store facts from conversation
                self._extract_memories_from_conversation(message, accumulated)

                return  # Exit after delegation

            except Exception as e:
                logger.error(f"Delegation error: {e}", exc_info=True)
                # Fall through to direct handling
                yield f"\n\n*Delegation failed, handling directly...*\n\n"

        # Step 3: Handle directly via Claude Code CLI
        bridge = get_bridge()
        prompt = self._build_prompt_with_context(message, include_history, memory_context)

        try:
            accumulated = ""
            async for chunk in bridge.stream_query(
                prompt=prompt,
                timeout=120,
                allowed_tools=None,
            ):
                accumulated += chunk
                yield chunk

            # Update conversation history after streaming completes
            self._conversation_history.append({"role": "user", "content": message})
            self._conversation_history.append({"role": "assistant", "content": accumulated})

            # Trim history if too long
            if len(self._conversation_history) > self._max_history * 2:
                self._conversation_history = self._conversation_history[-self._max_history * 2:]

            # Step 4: Check if response contains delegation markers
            result = self._parse_response(accumulated)
            if result.delegation != DelegationType.NONE and result.delegation_task:
                logger.info(
                    f"Response contains delegation marker: {result.delegation.value} "
                    f"- Task: {result.delegation_task}"
                )

                # Execute delegation if markers found in response
                if allow_delegation:
                    request = self._create_delegation_request(
                        delegation_type=result.delegation,
                        task=result.delegation_task,
                        original_message=message,
                    )

                    yield "\n\n"  # Separator

                    async for chunk in self._delegation_manager.delegate_stream(request):
                        yield chunk

            # Extract and store facts from conversation
            self._extract_memories_from_conversation(message, accumulated)

        except BridgeError as e:
            logger.error(f"Bridge error during streaming: {e}")
            yield f"I apologize, but I encountered an error: {e}"

        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}", exc_info=True)
            yield "I apologize, but something went wrong. Please try again."

    def _build_prompt_with_context(
        self,
        message: str,
        include_history: bool,
        memory_context: Optional[MemoryContext] = None,
    ) -> str:
        """
        Build a prompt with system context, memory, and history.

        Args:
            message: The user's message
            include_history: Whether to include history
            memory_context: Optional memory context to include

        Returns:
            Full prompt string
        """
        parts = [f"<system>\n{self.system_prompt}\n</system>"]

        # Include memory context if available
        memory_ctx = memory_context or self._last_memory_context
        if memory_ctx and memory_ctx.has_context():
            memory_str = memory_ctx.to_prompt_string()
            if memory_str:
                parts.append(f"<memory>\n{memory_str}\n</memory>")

        if include_history and self._conversation_history:
            history = self._conversation_history[-self._max_history:]
            parts.append("<conversation>")
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"<{role}>{content}</{role}>")
            parts.append("</conversation>")

        parts.append(f"<user_request>\n{message}\n</user_request>")

        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> OrchestratorResult:
        """
        Parse response for delegation markers.

        Args:
            response: The raw response from Claude

        Returns:
            OrchestratorResult with parsed delegation info
        """
        # Look for delegation pattern
        match = DELEGATION_PATTERN.search(response)

        if match:
            delegation_type = match.group(1).upper()
            delegation_task = match.group(2).strip()

            # Map to enum
            delegation_map = {
                "CODE": DelegationType.CODE,
                "RESEARCH": DelegationType.RESEARCH,
                "TASK": DelegationType.TASK,
            }

            delegation = delegation_map.get(delegation_type, DelegationType.NONE)

            # Remove the delegation marker from the response content
            clean_content = DELEGATION_PATTERN.sub("", response).strip()

            # If the response was just the delegation marker, provide context
            if not clean_content:
                clean_content = f"I'll delegate this to the {delegation.value} team."

            return OrchestratorResult(
                content=clean_content,
                delegation=delegation,
                delegation_task=delegation_task,
            )

        # No delegation - direct response
        return OrchestratorResult(content=response)

    async def delegate_to_lead(
        self,
        delegation: DelegationType,
        task: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Delegate a task to the appropriate Domain Lead.

        Note: Domain Leads are not yet implemented (Part 10).
        This method provides the interface for future integration.

        Args:
            delegation: Type of delegation
            task: Task description
            context: Optional additional context

        Returns:
            Result from the Domain Lead
        """
        logger.info(f"Delegating to {delegation.value} lead: {task[:50]}...")

        # TODO: Implement when Domain Leads are ready (Part 10)
        # For now, return a placeholder indicating delegation would happen

        if delegation == DelegationType.CODE:
            # Future: return await code_lead.run(task, context)
            return f"[Code Lead would handle: {task}] - Domain Leads not yet implemented"

        elif delegation == DelegationType.RESEARCH:
            # Future: return await research_lead.run(task, context)
            return f"[Research Lead would handle: {task}] - Domain Leads not yet implemented"

        elif delegation == DelegationType.TASK:
            # Future: return await task_lead.run(task, context)
            return f"[Task Lead would handle: {task}] - Domain Leads not yet implemented"

        else:
            return "Unknown delegation type"

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []
        logger.debug("Conversation history cleared")

    @property
    def history_length(self) -> int:
        """Return current conversation history length."""
        return len(self._conversation_history)


# Singleton instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
