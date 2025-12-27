"""Permission System for Emperor AI Assistant.

Provides comprehensive access control:
- Tool risk classification (LOW, MEDIUM, HIGH, CRITICAL)
- Permission presets (STRICT, MODERATE, RELAXED)
- Approval workflows for sensitive operations
- Audit logging for all tool executions

Usage:
    >>> from permissions import get_permission_manager, RiskLevel
    >>> pm = get_permission_manager()
    >>> await pm.check_permission("write_file", {"path": "/etc/hosts"})
"""

from .risk_levels import RiskLevel, ToolRiskClassifier
from .presets import PermissionPreset, get_preset_config
from .manager import PermissionManager, get_permission_manager, reset_permission_manager
from .audit import AuditLog, AuditEntry, get_audit_log

__all__ = [
    # Risk classification
    "RiskLevel",
    "ToolRiskClassifier",
    # Presets
    "PermissionPreset",
    "get_preset_config",
    # Manager
    "PermissionManager",
    "get_permission_manager",
    "reset_permission_manager",
    # Audit
    "AuditLog",
    "AuditEntry",
    "get_audit_log",
]
