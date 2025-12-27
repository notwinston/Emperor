"""Permission presets for different security levels.

Provides configurable presets that control which operations
require approval and which are automatically allowed/denied.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .risk_levels import RiskLevel


class PermissionPreset(str, Enum):
    """Available permission presets."""

    STRICT = "strict"
    """
    Maximum security. Requires approval for:
    - All MEDIUM, HIGH, and CRITICAL operations
    - All file writes
    - All shell commands
    Best for: Production environments, sensitive work
    """

    MODERATE = "moderate"
    """
    Balanced security. Requires approval for:
    - HIGH and CRITICAL operations
    - Shell commands
    - System file modifications
    Best for: Development with oversight
    """

    RELAXED = "relaxed"
    """
    Minimal friction. Requires approval for:
    - CRITICAL operations only
    - Destructive commands (rm -rf, etc.)
    Best for: Trusted development environments
    """

    CUSTOM = "custom"
    """User-defined permission settings."""


@dataclass
class PresetConfig:
    """Configuration for a permission preset."""

    name: PermissionPreset
    description: str

    # Which risk levels require approval
    require_approval: set[RiskLevel] = field(default_factory=set)

    # Which risk levels are auto-denied (blocked)
    auto_deny: set[RiskLevel] = field(default_factory=set)

    # Which risk levels are auto-allowed (no approval needed)
    auto_allow: set[RiskLevel] = field(default_factory=set)

    # Tool-specific overrides
    tool_overrides: dict[str, str] = field(default_factory=dict)
    # Values: "allow", "deny", "approve"

    # Allow operations in debug mode without approval
    debug_mode_bypass: bool = False

    # Timeout for approval requests (seconds)
    approval_timeout: int = 300

    # Whether to log all operations (even allowed ones)
    log_all_operations: bool = True


# Preset configurations
PRESET_CONFIGS: dict[PermissionPreset, PresetConfig] = {
    PermissionPreset.STRICT: PresetConfig(
        name=PermissionPreset.STRICT,
        description="Maximum security - requires approval for most operations",
        require_approval={RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL},
        auto_deny=set(),  # Nothing auto-denied, just requires approval
        auto_allow={RiskLevel.LOW},
        tool_overrides={
            # Even low-risk tools might need approval for certain paths
            "write_file": "approve",
            "execute_command": "approve",
            "background_command": "approve",
        },
        debug_mode_bypass=False,
        approval_timeout=300,
        log_all_operations=True,
    ),
    PermissionPreset.MODERATE: PresetConfig(
        name=PermissionPreset.MODERATE,
        description="Balanced security - requires approval for sensitive operations",
        require_approval={RiskLevel.HIGH, RiskLevel.CRITICAL},
        auto_deny=set(),
        auto_allow={RiskLevel.LOW, RiskLevel.MEDIUM},
        tool_overrides={
            "execute_command": "approve",
            "background_command": "approve",
        },
        debug_mode_bypass=False,
        approval_timeout=180,
        log_all_operations=True,
    ),
    PermissionPreset.RELAXED: PresetConfig(
        name=PermissionPreset.RELAXED,
        description="Minimal friction - only blocks critical operations",
        require_approval={RiskLevel.CRITICAL},
        auto_deny=set(),
        auto_allow={RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH},
        tool_overrides={},
        debug_mode_bypass=True,
        approval_timeout=120,
        log_all_operations=False,  # Only log approvals and denials
    ),
}


def get_preset_config(preset: PermissionPreset) -> PresetConfig:
    """
    Get the configuration for a preset.

    Args:
        preset: The preset to get config for

    Returns:
        PresetConfig for the preset

    Raises:
        ValueError: If preset is CUSTOM (requires custom config)
    """
    if preset == PermissionPreset.CUSTOM:
        raise ValueError(
            "CUSTOM preset requires explicit configuration. "
            "Use create_custom_preset() instead."
        )

    return PRESET_CONFIGS[preset]


def create_custom_preset(
    require_approval: Optional[set[RiskLevel]] = None,
    auto_deny: Optional[set[RiskLevel]] = None,
    auto_allow: Optional[set[RiskLevel]] = None,
    tool_overrides: Optional[dict[str, str]] = None,
    debug_mode_bypass: bool = False,
    approval_timeout: int = 180,
    log_all_operations: bool = True,
) -> PresetConfig:
    """
    Create a custom preset configuration.

    Args:
        require_approval: Risk levels that require approval
        auto_deny: Risk levels that are automatically denied
        auto_allow: Risk levels that are automatically allowed
        tool_overrides: Tool-specific permission overrides
        debug_mode_bypass: Whether to bypass approval in debug mode
        approval_timeout: Timeout for approval requests
        log_all_operations: Whether to log all operations

    Returns:
        Custom PresetConfig
    """
    return PresetConfig(
        name=PermissionPreset.CUSTOM,
        description="Custom permission configuration",
        require_approval=require_approval or {RiskLevel.HIGH, RiskLevel.CRITICAL},
        auto_deny=auto_deny or set(),
        auto_allow=auto_allow or {RiskLevel.LOW},
        tool_overrides=tool_overrides or {},
        debug_mode_bypass=debug_mode_bypass,
        approval_timeout=approval_timeout,
        log_all_operations=log_all_operations,
    )
