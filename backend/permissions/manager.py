"""Permission Manager for Emperor AI Assistant.

Central manager for permission checking, approval workflows,
and coordination between risk classification, presets, and audit logging.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from config import settings, get_logger
from .risk_levels import RiskLevel, ToolRiskClassifier, get_risk_classifier
from .presets import PermissionPreset, PresetConfig, get_preset_config
from .audit import AuditLog, AuditAction, get_audit_log

logger = get_logger(__name__)


@dataclass
class PermissionResult:
    """Result of a permission check."""

    allowed: bool
    risk_level: RiskLevel
    reason: str
    requires_approval: bool = False
    approval_granted: Optional[bool] = None


@dataclass
class ApprovalRequest:
    """A pending approval request."""

    id: str
    agent_name: str
    tool_name: str
    risk_level: RiskLevel
    input_data: dict[str, Any]
    reason: str
    created_at: datetime
    timeout: int  # seconds
    future: asyncio.Future


# Type for approval callback
ApprovalCallback = Callable[[str, str, str, dict[str, Any]], asyncio.Future[bool]]


class PermissionManager:
    """
    Central permission manager for the Emperor system.

    Handles:
    - Permission checking for tool executions
    - Approval workflows for sensitive operations
    - Preset configuration
    - Audit logging integration
    """

    def __init__(
        self,
        preset: PermissionPreset = PermissionPreset.MODERATE,
        custom_config: Optional[PresetConfig] = None,
    ):
        """
        Initialize the permission manager.

        Args:
            preset: The permission preset to use
            custom_config: Custom config if preset is CUSTOM
        """
        self._classifier = get_risk_classifier()
        self._audit_log = get_audit_log()
        self._approval_callback: Optional[ApprovalCallback] = None
        self._pending_approvals: dict[str, ApprovalRequest] = {}

        # Set preset configuration
        if preset == PermissionPreset.CUSTOM:
            if custom_config is None:
                raise ValueError("CUSTOM preset requires custom_config")
            self._config = custom_config
        else:
            self._config = get_preset_config(preset)

        logger.info(f"Permission manager initialized with preset: {self._config.name.value}")

    @property
    def preset(self) -> PermissionPreset:
        """Get the current preset."""
        return self._config.name

    @property
    def config(self) -> PresetConfig:
        """Get the current configuration."""
        return self._config

    def set_preset(self, preset: PermissionPreset) -> None:
        """
        Change the active preset.

        Args:
            preset: The new preset to use
        """
        old_preset = self._config.name
        self._config = get_preset_config(preset)

        # Log the change
        self._audit_log.log(
            action=AuditAction.PRESET_CHANGED,
            agent_name="system",
            tool_name="",
            risk_level="",
            metadata={
                "old_preset": old_preset.value,
                "new_preset": preset.value,
            },
        )

        logger.info(f"Permission preset changed: {old_preset.value} -> {preset.value}")

    def set_approval_callback(self, callback: ApprovalCallback) -> None:
        """
        Set the callback for approval requests.

        The callback receives:
        - tool_name: Name of the tool
        - risk_level: Risk level string
        - reason: Why approval is needed
        - input_data: Tool input parameters

        And should return an awaitable bool (True = approved).

        Args:
            callback: The async approval callback
        """
        self._approval_callback = callback
        logger.debug("Approval callback registered")

    async def check_permission(
        self,
        agent_name: str,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> PermissionResult:
        """
        Check if a tool execution is permitted.

        Args:
            agent_name: Name of the agent requesting permission
            tool_name: Name of the tool to execute
            input_data: Tool input parameters

        Returns:
            PermissionResult indicating if the operation is allowed
        """
        input_data = input_data or {}

        # Classify the risk level
        risk_level = self._classifier.classify(tool_name, input_data)

        # Log the permission check
        if self._config.log_all_operations:
            self._audit_log.log(
                action=AuditAction.PERMISSION_CHECK,
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=risk_level.value,
                input_data=input_data,
            )

        # Check tool-specific overrides first
        if tool_name in self._config.tool_overrides:
            override = self._config.tool_overrides[tool_name]

            if override == "deny":
                return PermissionResult(
                    allowed=False,
                    risk_level=risk_level,
                    reason=f"Tool '{tool_name}' is blocked by preset configuration",
                )
            elif override == "allow":
                return PermissionResult(
                    allowed=True,
                    risk_level=risk_level,
                    reason="Tool allowed by preset override",
                )
            elif override == "approve":
                # Fall through to approval workflow
                pass

        # Check if auto-denied
        if risk_level in self._config.auto_deny:
            self._audit_log.log_tool_denied(
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=risk_level.value,
                input_data=input_data,
                denial_reason=f"Risk level {risk_level.value} is auto-denied",
            )
            return PermissionResult(
                allowed=False,
                risk_level=risk_level,
                reason=f"Operations with {risk_level.value} risk are automatically denied",
            )

        # Check if auto-allowed
        if risk_level in self._config.auto_allow:
            return PermissionResult(
                allowed=True,
                risk_level=risk_level,
                reason=f"Operations with {risk_level.value} risk are automatically allowed",
            )

        # Check if requires approval
        if risk_level in self._config.require_approval:
            # Check debug mode bypass
            if self._config.debug_mode_bypass and settings.debug:
                logger.warning(
                    f"DEBUG MODE: Bypassing approval for {tool_name} ({risk_level.value})"
                )
                return PermissionResult(
                    allowed=True,
                    risk_level=risk_level,
                    reason="Approval bypassed in debug mode",
                )

            return PermissionResult(
                allowed=False,
                risk_level=risk_level,
                reason=f"Operations with {risk_level.value} risk require approval",
                requires_approval=True,
            )

        # Default: allow
        return PermissionResult(
            allowed=True,
            risk_level=risk_level,
            reason="Operation permitted by preset configuration",
        )

    async def request_approval(
        self,
        agent_name: str,
        tool_name: str,
        input_data: dict[str, Any],
        risk_level: RiskLevel,
        reason: str,
    ) -> bool:
        """
        Request approval for a sensitive operation.

        Args:
            agent_name: Name of the requesting agent
            tool_name: Name of the tool
            input_data: Tool input parameters
            risk_level: Risk level of the operation
            reason: Why approval is needed

        Returns:
            True if approved, False otherwise
        """
        # Log the request
        self._audit_log.log_approval_requested(
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level.value,
            input_data=input_data,
        )

        # Check if callback is configured
        if not self._approval_callback:
            logger.warning("No approval callback configured, denying by default")

            self._audit_log.log_approval_response(
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=risk_level.value,
                approved=False,
                reason="No approval callback configured",
            )

            return False

        # Request approval via callback
        try:
            approved = await asyncio.wait_for(
                self._approval_callback(
                    tool_name,
                    risk_level.value,
                    reason,
                    input_data,
                ),
                timeout=self._config.approval_timeout,
            )

            # Log the response
            self._audit_log.log_approval_response(
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=risk_level.value,
                approved=approved,
                reason="User response" if not approved else None,
            )

            return approved

        except asyncio.TimeoutError:
            logger.warning(f"Approval request timed out for {tool_name}")

            self._audit_log.log(
                action=AuditAction.APPROVAL_TIMEOUT,
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=risk_level.value,
                input_data=input_data,
            )

            return False

        except Exception as e:
            logger.error(f"Error in approval callback: {e}")
            return False

    async def execute_with_permission(
        self,
        agent_name: str,
        tool_name: str,
        input_data: dict[str, Any],
        executor: Callable[..., Any],
    ) -> tuple[bool, Any]:
        """
        Execute a tool with permission checking.

        This is a convenience method that combines permission checking,
        approval workflow, and execution.

        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            input_data: Tool input parameters
            executor: Async function to execute the tool

        Returns:
            Tuple of (success, result_or_error)
        """
        # Check permission
        result = await self.check_permission(agent_name, tool_name, input_data)

        # If requires approval, request it
        if result.requires_approval:
            approved = await self.request_approval(
                agent_name=agent_name,
                tool_name=tool_name,
                input_data=input_data,
                risk_level=result.risk_level,
                reason=result.reason,
            )

            if not approved:
                return False, f"Permission denied: {result.reason}"

            result.approval_granted = True

        # If not allowed and doesn't require approval, deny
        if not result.allowed and not result.requires_approval:
            self._audit_log.log_tool_denied(
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=result.risk_level.value,
                input_data=input_data,
                denial_reason=result.reason,
            )
            return False, f"Permission denied: {result.reason}"

        # Execute the tool
        try:
            output = await executor(**input_data)

            # Log successful execution
            self._audit_log.log_tool_executed(
                agent_name=agent_name,
                tool_name=tool_name,
                risk_level=result.risk_level.value,
                input_data=input_data,
                result=str(output)[:500],
                approved_by="user" if result.approval_granted else "auto",
            )

            return True, output

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return False, str(e)

    def get_risk_level(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> RiskLevel:
        """
        Get the risk level for a tool operation.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            The risk level
        """
        return self._classifier.classify(tool_name, input_data)

    def register_tool_risk(self, tool_name: str, risk_level: RiskLevel) -> None:
        """
        Register a risk level for a custom tool.

        Args:
            tool_name: Name of the tool
            risk_level: Base risk level
        """
        self._classifier.register_tool_risk(tool_name, risk_level)

    def get_audit_statistics(self, since: Optional[datetime] = None) -> dict[str, Any]:
        """
        Get audit statistics.

        Args:
            since: Start timestamp

        Returns:
            Statistics dictionary
        """
        return self._audit_log.get_statistics(since)


# Singleton instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """
    Get the singleton permission manager.

    Returns:
        The shared PermissionManager instance
    """
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def reset_permission_manager() -> None:
    """Reset the singleton permission manager."""
    global _permission_manager
    _permission_manager = None


def configure_permissions(
    preset: PermissionPreset = PermissionPreset.MODERATE,
    custom_config: Optional[PresetConfig] = None,
) -> PermissionManager:
    """
    Configure and return the permission manager.

    Args:
        preset: The permission preset to use
        custom_config: Custom config if preset is CUSTOM

    Returns:
        The configured PermissionManager
    """
    global _permission_manager
    _permission_manager = PermissionManager(preset, custom_config)
    return _permission_manager
