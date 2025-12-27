"""Risk level classification for tools.

Defines risk levels and provides classification logic for all tools.
"""

from enum import Enum
from typing import Any, Optional

from config import get_logger

logger = get_logger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for tool operations."""

    LOW = "low"
    """Read-only operations, no system impact. Examples: read_file, list_directory"""

    MEDIUM = "medium"
    """Write operations within project scope. Examples: write_file, git commit"""

    HIGH = "high"
    """System-affecting operations. Examples: execute_command, install packages"""

    CRITICAL = "critical"
    """Potentially destructive operations. Examples: rm -rf, sudo, system config changes"""


# Default risk levels for known tools
TOOL_RISK_LEVELS: dict[str, RiskLevel] = {
    # File tools
    "read_file": RiskLevel.LOW,
    "list_directory": RiskLevel.LOW,
    "write_file": RiskLevel.MEDIUM,

    # Search tools
    "grep": RiskLevel.LOW,
    "glob": RiskLevel.LOW,

    # Memory tools
    "remember": RiskLevel.LOW,
    "recall": RiskLevel.LOW,
    "forget": RiskLevel.MEDIUM,
    "list_memories": RiskLevel.LOW,

    # Shell tools
    "execute_command": RiskLevel.HIGH,
    "background_command": RiskLevel.HIGH,

    # Web tools
    "web_search": RiskLevel.LOW,
}


# Patterns that escalate risk level
RISK_ESCALATION_PATTERNS: dict[str, list[tuple[str, RiskLevel]]] = {
    "write_file": [
        # Writing to system directories escalates to CRITICAL
        (r"^/etc/", RiskLevel.CRITICAL),
        (r"^/usr/", RiskLevel.CRITICAL),
        (r"^/bin/", RiskLevel.CRITICAL),
        (r"^/sbin/", RiskLevel.CRITICAL),
        (r"^/var/", RiskLevel.HIGH),
        # Writing executable files
        (r"\.(sh|bash|zsh|py|rb|pl)$", RiskLevel.HIGH),
        # Writing config files
        (r"\.(env|config|conf|ini)$", RiskLevel.HIGH),
    ],
    "execute_command": [
        # Sudo/root commands
        (r"\bsudo\b", RiskLevel.CRITICAL),
        (r"\bsu\b", RiskLevel.CRITICAL),
        # Destructive commands
        (r"\brm\s+-[rfR]", RiskLevel.CRITICAL),
        (r"\brmdir\b", RiskLevel.HIGH),
        (r"\bmkfs\b", RiskLevel.CRITICAL),
        # System commands
        (r"\bsystemctl\b", RiskLevel.CRITICAL),
        (r"\bservice\b", RiskLevel.CRITICAL),
        # Package management
        (r"\bapt\b", RiskLevel.HIGH),
        (r"\byum\b", RiskLevel.HIGH),
        (r"\bbrew\b", RiskLevel.MEDIUM),
        (r"\bpip\s+install\b", RiskLevel.MEDIUM),
        (r"\bnpm\s+install\b", RiskLevel.MEDIUM),
    ],
}


class ToolRiskClassifier:
    """Classifies tool operations by risk level."""

    def __init__(self):
        """Initialize the classifier."""
        import re
        self._patterns: dict[str, list[tuple[re.Pattern, RiskLevel]]] = {}

        # Compile patterns
        for tool_name, patterns in RISK_ESCALATION_PATTERNS.items():
            self._patterns[tool_name] = [
                (re.compile(pattern, re.IGNORECASE), level)
                for pattern, level in patterns
            ]

    def classify(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> RiskLevel:
        """
        Classify the risk level of a tool operation.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            The risk level for this operation
        """
        # Get base risk level
        base_level = TOOL_RISK_LEVELS.get(tool_name, RiskLevel.HIGH)

        # Check for risk escalation based on input
        if input_data and tool_name in self._patterns:
            escalated_level = self._check_escalation(
                tool_name, input_data, base_level
            )
            if escalated_level:
                return escalated_level

        return base_level

    def _check_escalation(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        base_level: RiskLevel,
    ) -> Optional[RiskLevel]:
        """
        Check if input data escalates the risk level.

        Returns:
            Escalated risk level or None
        """
        patterns = self._patterns.get(tool_name, [])

        # Get relevant input values to check
        values_to_check = []

        if tool_name == "write_file":
            if "path" in input_data:
                values_to_check.append(str(input_data["path"]))
        elif tool_name == "execute_command":
            if "command" in input_data:
                values_to_check.append(str(input_data["command"]))

        # Check patterns
        highest_level = base_level
        for value in values_to_check:
            for pattern, level in patterns:
                if pattern.search(value):
                    if self._compare_levels(level, highest_level) > 0:
                        highest_level = level
                        logger.debug(
                            f"Risk escalated for {tool_name}: "
                            f"{base_level.value} -> {level.value} "
                            f"(pattern: {pattern.pattern})"
                        )

        return highest_level if highest_level != base_level else None

    def _compare_levels(self, a: RiskLevel, b: RiskLevel) -> int:
        """
        Compare two risk levels.

        Returns:
            Positive if a > b, negative if a < b, 0 if equal
        """
        order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return order.index(a) - order.index(b)

    def register_tool_risk(self, tool_name: str, risk_level: RiskLevel) -> None:
        """
        Register a risk level for a tool.

        Args:
            tool_name: Name of the tool
            risk_level: Base risk level for the tool
        """
        TOOL_RISK_LEVELS[tool_name] = risk_level
        logger.debug(f"Registered risk level for {tool_name}: {risk_level.value}")

    def add_escalation_pattern(
        self,
        tool_name: str,
        pattern: str,
        risk_level: RiskLevel,
    ) -> None:
        """
        Add a risk escalation pattern for a tool.

        Args:
            tool_name: Name of the tool
            pattern: Regex pattern to match
            risk_level: Risk level when pattern matches
        """
        import re

        if tool_name not in self._patterns:
            self._patterns[tool_name] = []

        self._patterns[tool_name].append(
            (re.compile(pattern, re.IGNORECASE), risk_level)
        )
        logger.debug(
            f"Added escalation pattern for {tool_name}: "
            f"{pattern} -> {risk_level.value}"
        )


# Singleton instance
_classifier: Optional[ToolRiskClassifier] = None


def get_risk_classifier() -> ToolRiskClassifier:
    """Get the singleton risk classifier."""
    global _classifier
    if _classifier is None:
        _classifier = ToolRiskClassifier()
    return _classifier
