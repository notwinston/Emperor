"""Intent Classification for Emperor AI Assistant.

This module classifies user messages to determine the appropriate
handling strategy - direct response or delegation to a Domain Lead.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from config import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Types of user intents."""

    # Direct handling intents
    CASUAL_CHAT = "casual_chat"      # Greetings, small talk
    QUESTION = "question"            # Factual questions, explanations
    OPINION = "opinion"              # Asking for suggestions/advice

    # Delegation intents
    CODE_TASK = "code_task"          # Programming tasks
    RESEARCH_TASK = "research_task"  # Research and analysis
    AUTOMATION_TASK = "automation_task"  # System commands, file ops

    # Fallback
    UNKNOWN = "unknown"              # Couldn't classify


class DelegationTarget(str, Enum):
    """Target for task delegation."""

    NONE = "none"          # Handle directly
    CODE = "code"          # Code Lead
    RESEARCH = "research"  # Research Lead
    TASK = "task"          # Task Lead


@dataclass
class IntentResult:
    """Result of intent classification."""

    intent: IntentType
    confidence: float  # 0.0 to 1.0
    delegation: DelegationTarget = DelegationTarget.NONE
    reasoning: Optional[str] = None
    keywords_matched: list[str] = field(default_factory=list)

    @property
    def should_delegate(self) -> bool:
        """Check if this intent should be delegated."""
        return self.delegation != DelegationTarget.NONE

    @property
    def is_confident(self) -> bool:
        """Check if classification confidence is high enough."""
        return self.confidence >= 0.7


# =============================================================================
# Pattern Definitions
# =============================================================================

# Casual chat patterns
CASUAL_PATTERNS = [
    r"^(hi|hello|hey|howdy|greetings|sup|yo)[\s!.,?]*$",
    r"^good\s*(morning|afternoon|evening|night)[\s!.,?]*$",
    r"^(thanks|thank\s*you|thx|ty)[\s!.,?]*",
    r"^(bye|goodbye|see\s*you|later|cya)[\s!.,?]*$",
    r"^how\s*(are|r)\s*(you|u)[\s?]*$",
    r"^what'?s\s*up[\s?]*$",
    r"^(ok|okay|sure|alright|got\s*it|understood)[\s!.,?]*$",
    r"^(yes|no|yeah|nope|yep|nah)[\s!.,?]*$",
    r"^(nice|cool|awesome|great|perfect)[\s!.,?]*$",
]

# Question patterns (factual, explanatory)
QUESTION_PATTERNS = [
    r"^what\s+(is|are|was|were|does|do)\s+",
    r"^how\s+(does|do|is|are|can|could|would)\s+",
    r"^why\s+(is|are|does|do|did|would|can)\s+",
    r"^when\s+(is|are|was|were|did|does)\s+",
    r"^where\s+(is|are|was|were|can|do)\s+",
    r"^who\s+(is|are|was|were)\s+",
    r"^can\s+you\s+(explain|tell|describe)\s+",
    r"^(explain|describe|define)\s+",
    r"^what'?s\s+the\s+(difference|meaning|definition)",
]

# Opinion/advice patterns
OPINION_PATTERNS = [
    r"^what\s+(do\s+you\s+think|would\s+you\s+(suggest|recommend))",
    r"^(should|would)\s+(i|we)\s+",
    r"^(is\s+it|would\s+it\s+be)\s+(better|good|okay|wise)\s+to\s+",
    r"^(any\s+)?(suggestions?|recommendations?|advice|tips)\s+",
    r"^which\s+(one|option|approach)\s+(should|would|is)",
    r"^do\s+you\s+(think|recommend|suggest)\s+",
    r"^what'?s\s+(your|the\s+best)\s+(opinion|take|view)\s+",
]

# Code task patterns
CODE_PATTERNS = [
    r"\b(write|create|implement|build|make)\s+(a\s+)?(function|class|method|script|program|code|module)",
    r"\b(fix|debug|solve|resolve)\s+(this|the|my)?\s*(bug|error|issue|problem)",
    r"\b(refactor|optimize|improve|clean\s*up)\s+(this|the|my)?\s*(code|function|class)",
    r"\b(review|check|analyze)\s+(this|the|my)?\s*(code|implementation|pr|pull\s*request)",
    r"\b(add|implement)\s+(a\s+)?(feature|functionality|method|endpoint)",
    r"\b(convert|transform|migrate)\s+.*(to|from)\s+(python|javascript|typescript|rust|go)",
    r"\b(unit\s*)?test(s|ing)?\s+(for|the|this|my)",
    r"```[\s\S]*```",  # Code blocks in message
    r"\b(python|javascript|typescript|rust|go|java|c\+\+|ruby)\s+(code|function|script)",
    r"\b(api|endpoint|route|handler)\s+(for|to|that)",
    r"\bset\s*up\s+(a\s+)?(project|repo|environment|dev)",
]

# Research task patterns
RESEARCH_PATTERNS = [
    r"^research\s+",
    r"\b(research|investigate|look\s*into|find\s*out\s*about)\s+",
    r"\b(compare|comparison|versus|vs\.?)\s+",
    r"\b(analyze|analysis)\s+(of\s+)?",
    r"\b(what\s+are\s+the\s+)?(best\s+practices|trends|options)\s+(for|in)",
    r"\b(summarize|summary\s+of)\s+",
    r"\b(find|search\s+for)\s+(information|articles|papers|resources)\s+(on|about)",
    r"\bpros\s+and\s+cons\s+",
    r"\b(state\s+of\s+the\s+art|latest|current)\s+(in|for|on)\s+",
    r"\bcit(e|ation|ations)\s+",
]

# Automation/task patterns
AUTOMATION_PATTERNS = [
    r"^run\s+(the\s+)?(tests?|build|script|command)",
    r"\b(execute|run)\s+(this|the|a)?\s*(command|script|shell)",
    r"\b(create|make|new)\s+(a\s+)?(folder|directory|file)",
    r"\b(delete|remove|rm)\s+(the\s+)?(file|folder|directory)",
    r"\b(move|copy|rename)\s+(the\s+)?(file|folder)",
    r"\b(install|uninstall|update)\s+(the\s+)?",
    r"\b(start|stop|restart)\s+(the\s+)?(server|service|process)",
    r"\b(deploy|push|pull)\s+(to|from)?\s*",
    r"\bgit\s+(commit|push|pull|merge|rebase|checkout|branch)",
    r"\b(npm|yarn|pip|cargo|brew)\s+(install|run|build)",
    r"\b(set\s*up|configure|initialize)\s+(the\s+)?(env|environment|database|db)",
    r"\b(clean|clear|reset)\s+(the\s+)?(cache|logs|build)",
]


# =============================================================================
# Intent Classifier
# =============================================================================

class IntentClassifier:
    """
    Classifies user message intent using pattern matching.

    Uses a two-phase approach:
    1. Pattern matching for common, clear intents (fast, no API call)
    2. LLM fallback for ambiguous cases (slower, more accurate)
    """

    def __init__(self):
        """Initialize the classifier with compiled patterns."""
        self._casual_patterns = [re.compile(p, re.IGNORECASE) for p in CASUAL_PATTERNS]
        self._question_patterns = [re.compile(p, re.IGNORECASE) for p in QUESTION_PATTERNS]
        self._opinion_patterns = [re.compile(p, re.IGNORECASE) for p in OPINION_PATTERNS]
        self._code_patterns = [re.compile(p, re.IGNORECASE) for p in CODE_PATTERNS]
        self._research_patterns = [re.compile(p, re.IGNORECASE) for p in RESEARCH_PATTERNS]
        self._automation_patterns = [re.compile(p, re.IGNORECASE) for p in AUTOMATION_PATTERNS]

    def classify(self, message: str) -> IntentResult:
        """
        Classify a user message's intent.

        Args:
            message: The user's message text

        Returns:
            IntentResult with classified intent and metadata
        """
        message = message.strip()

        if not message:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Empty message"
            )

        # Check patterns in order of specificity
        # (more specific patterns first to avoid false positives)

        # 1. Check for code tasks (high specificity)
        result = self._check_patterns(
            message,
            self._code_patterns,
            IntentType.CODE_TASK,
            DelegationTarget.CODE
        )
        if result and result.confidence >= 0.7:
            return result

        # 2. Check for automation tasks
        result = self._check_patterns(
            message,
            self._automation_patterns,
            IntentType.AUTOMATION_TASK,
            DelegationTarget.TASK
        )
        if result and result.confidence >= 0.7:
            return result

        # 3. Check for research tasks
        result = self._check_patterns(
            message,
            self._research_patterns,
            IntentType.RESEARCH_TASK,
            DelegationTarget.RESEARCH
        )
        if result and result.confidence >= 0.7:
            return result

        # 4. Check for casual chat (usually short messages)
        result = self._check_patterns(
            message,
            self._casual_patterns,
            IntentType.CASUAL_CHAT,
            DelegationTarget.NONE
        )
        if result and result.confidence >= 0.8:
            return result

        # 5. Check for opinion requests
        result = self._check_patterns(
            message,
            self._opinion_patterns,
            IntentType.OPINION,
            DelegationTarget.NONE
        )
        if result and result.confidence >= 0.7:
            return result

        # 6. Check for questions
        result = self._check_patterns(
            message,
            self._question_patterns,
            IntentType.QUESTION,
            DelegationTarget.NONE
        )
        if result and result.confidence >= 0.6:
            return result

        # 7. Heuristic fallbacks based on message characteristics
        return self._heuristic_classify(message)

    def _check_patterns(
        self,
        message: str,
        patterns: list[re.Pattern],
        intent: IntentType,
        delegation: DelegationTarget,
    ) -> Optional[IntentResult]:
        """
        Check message against a list of patterns.

        Args:
            message: The message to check
            patterns: List of compiled regex patterns
            intent: The intent type if matched
            delegation: The delegation target if matched

        Returns:
            IntentResult if any pattern matches, None otherwise
        """
        matched_keywords = []

        for pattern in patterns:
            match = pattern.search(message)
            if match:
                matched_keywords.append(match.group(0))

        if not matched_keywords:
            return None

        # Calculate confidence based on number of matches and message length
        base_confidence = 0.6
        match_bonus = min(len(matched_keywords) * 0.1, 0.3)

        # Shorter messages that match are more confident
        length_factor = 1.0 if len(message) < 50 else 0.9 if len(message) < 100 else 0.8

        confidence = min((base_confidence + match_bonus) * length_factor, 0.95)

        return IntentResult(
            intent=intent,
            confidence=confidence,
            delegation=delegation,
            reasoning=f"Matched patterns: {matched_keywords[:3]}",
            keywords_matched=matched_keywords,
        )

    def _heuristic_classify(self, message: str) -> IntentResult:
        """
        Apply heuristic rules for messages that don't match patterns.

        Args:
            message: The message to classify

        Returns:
            IntentResult based on heuristics
        """
        message_lower = message.lower()
        word_count = len(message.split())

        # Very short messages are likely casual
        if word_count <= 3:
            return IntentResult(
                intent=IntentType.CASUAL_CHAT,
                confidence=0.5,
                delegation=DelegationTarget.NONE,
                reasoning="Short message, likely casual"
            )

        # Messages ending with ? are likely questions
        if message.strip().endswith("?"):
            return IntentResult(
                intent=IntentType.QUESTION,
                confidence=0.6,
                delegation=DelegationTarget.NONE,
                reasoning="Message ends with question mark"
            )

        # Check for code-related keywords
        code_keywords = ["code", "function", "bug", "error", "api", "database", "script"]
        if any(kw in message_lower for kw in code_keywords):
            return IntentResult(
                intent=IntentType.CODE_TASK,
                confidence=0.5,
                delegation=DelegationTarget.CODE,
                reasoning="Contains code-related keywords"
            )

        # Check for research keywords
        research_keywords = ["research", "find out", "learn about", "information on"]
        if any(kw in message_lower for kw in research_keywords):
            return IntentResult(
                intent=IntentType.RESEARCH_TASK,
                confidence=0.5,
                delegation=DelegationTarget.RESEARCH,
                reasoning="Contains research keywords"
            )

        # Check for task/automation keywords
        task_keywords = ["run", "execute", "create folder", "delete", "install"]
        if any(kw in message_lower for kw in task_keywords):
            return IntentResult(
                intent=IntentType.AUTOMATION_TASK,
                confidence=0.5,
                delegation=DelegationTarget.TASK,
                reasoning="Contains automation keywords"
            )

        # Default: treat as a question (most common intent)
        return IntentResult(
            intent=IntentType.QUESTION,
            confidence=0.4,
            delegation=DelegationTarget.NONE,
            reasoning="Default classification - treating as question"
        )

    async def classify_with_llm(
        self,
        message: str,
        pattern_result: Optional[IntentResult] = None,
    ) -> IntentResult:
        """
        Use LLM for intent classification when patterns are uncertain.

        This is called when pattern matching returns low confidence.
        Uses a fast, cheap model (Haiku) for quick classification.

        Args:
            message: The message to classify
            pattern_result: Optional result from pattern matching

        Returns:
            IntentResult from LLM classification
        """
        from claude_code_bridge import get_bridge

        bridge = get_bridge()

        if not bridge.is_verified:
            # Can't use LLM, return pattern result or default
            return pattern_result or IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.3,
                reasoning="LLM not available, pattern matching inconclusive"
            )

        classification_prompt = f"""Classify this user message into exactly ONE category.

Message: "{message}"

Categories:
- casual_chat: Greetings, thanks, small talk (e.g., "Hi", "Thanks!", "How are you?")
- question: Factual questions, asking for explanations (e.g., "What is X?", "How does Y work?")
- opinion: Asking for suggestions or advice (e.g., "What do you think?", "Should I...?")
- code_task: Programming tasks - writing, fixing, reviewing code
- research_task: Research, analysis, comparisons, finding information
- automation_task: Running commands, file operations, system tasks

Respond with ONLY the category name, nothing else."""

        try:
            response = await bridge.query(
                prompt=classification_prompt,
                timeout=15,
                allowed_tools=[],  # No tools needed for classification
                model="haiku",  # Fast, cheap model
                max_turns=1,
            )

            # Parse the response
            category = response.strip().lower().replace("-", "_")

            intent_map = {
                "casual_chat": (IntentType.CASUAL_CHAT, DelegationTarget.NONE),
                "question": (IntentType.QUESTION, DelegationTarget.NONE),
                "opinion": (IntentType.OPINION, DelegationTarget.NONE),
                "code_task": (IntentType.CODE_TASK, DelegationTarget.CODE),
                "research_task": (IntentType.RESEARCH_TASK, DelegationTarget.RESEARCH),
                "automation_task": (IntentType.AUTOMATION_TASK, DelegationTarget.TASK),
            }

            if category in intent_map:
                intent, delegation = intent_map[category]
                return IntentResult(
                    intent=intent,
                    confidence=0.85,
                    delegation=delegation,
                    reasoning=f"LLM classified as {category}"
                )

            # Couldn't parse LLM response
            logger.warning(f"Unexpected LLM classification: {response}")
            return pattern_result or IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.4,
                reasoning=f"LLM returned unexpected: {response[:50]}"
            )

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return pattern_result or IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.3,
                reasoning=f"LLM classification error: {e}"
            )

    async def classify_smart(self, message: str) -> IntentResult:
        """
        Smart classification: pattern matching first, LLM for uncertain cases.

        Args:
            message: The message to classify

        Returns:
            IntentResult with best available classification
        """
        # First try pattern matching
        pattern_result = self.classify(message)

        logger.debug(
            f"Pattern classification: {pattern_result.intent.value} "
            f"(confidence: {pattern_result.confidence:.2f})"
        )

        # If confident enough, use pattern result
        if pattern_result.is_confident:
            return pattern_result

        # Low confidence - try LLM classification
        logger.debug("Low confidence, using LLM classification")
        return await self.classify_with_llm(message, pattern_result)


# Singleton instance
_classifier: Optional[IntentClassifier] = None


def get_classifier() -> IntentClassifier:
    """Get the singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
