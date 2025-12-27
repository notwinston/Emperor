"""Audit logging for permission system.

Provides immutable audit logs for all tool executions,
permission decisions, and approval requests.
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from config import settings, get_logger

logger = get_logger(__name__)


class AuditAction(str, Enum):
    """Types of auditable actions."""

    TOOL_EXECUTED = "tool_executed"
    TOOL_DENIED = "tool_denied"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_TIMEOUT = "approval_timeout"
    PERMISSION_CHECK = "permission_check"
    PRESET_CHANGED = "preset_changed"


@dataclass
class AuditEntry:
    """A single audit log entry."""

    id: Optional[int] = None
    timestamp: str = ""
    action: str = ""
    agent_name: str = ""
    tool_name: str = ""
    risk_level: str = ""
    input_data: str = ""  # JSON string
    result: str = ""
    approved_by: Optional[str] = None  # "user", "auto", "preset"
    denial_reason: Optional[str] = None
    metadata: str = ""  # JSON string

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: tuple) -> "AuditEntry":
        """Create from database row."""
        return cls(
            id=row[0],
            timestamp=row[1],
            action=row[2],
            agent_name=row[3],
            tool_name=row[4],
            risk_level=row[5],
            input_data=row[6],
            result=row[7],
            approved_by=row[8],
            denial_reason=row[9],
            metadata=row[10],
        )


class AuditLog:
    """
    Immutable audit log for permission system.

    Stores all permission decisions and tool executions
    in an append-only SQLite database.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the audit log.

        Args:
            db_path: Path to the SQLite database
        """
        if db_path is None:
            db_path = settings.data_dir / "audit.db"

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    input_data TEXT,
                    result TEXT,
                    approved_by TEXT,
                    denial_reason TEXT,
                    metadata TEXT
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action
                ON audit_log(action)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_agent
                ON audit_log(agent_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_tool
                ON audit_log(tool_name)
            """)

            conn.commit()

        logger.debug(f"Audit log initialized at {self.db_path}")

    def log(
        self,
        action: AuditAction,
        agent_name: str,
        tool_name: str,
        risk_level: str,
        input_data: Optional[dict[str, Any]] = None,
        result: str = "",
        approved_by: Optional[str] = None,
        denial_reason: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        Log an audit entry.

        Args:
            action: The action being logged
            agent_name: Name of the agent performing the action
            tool_name: Name of the tool being used
            risk_level: Risk level of the operation
            input_data: Tool input parameters
            result: Result of the operation
            approved_by: Who approved the operation
            denial_reason: Reason for denial if applicable
            metadata: Additional metadata

        Returns:
            The ID of the created entry
        """
        entry = AuditEntry(
            action=action.value,
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level,
            input_data=json.dumps(self._sanitize_input(input_data or {})),
            result=result[:1000] if result else "",  # Truncate long results
            approved_by=approved_by,
            denial_reason=denial_reason,
            metadata=json.dumps(metadata or {}),
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_log (
                    timestamp, action, agent_name, tool_name, risk_level,
                    input_data, result, approved_by, denial_reason, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.timestamp,
                    entry.action,
                    entry.agent_name,
                    entry.tool_name,
                    entry.risk_level,
                    entry.input_data,
                    entry.result,
                    entry.approved_by,
                    entry.denial_reason,
                    entry.metadata,
                ),
            )
            conn.commit()
            entry_id = cursor.lastrowid

        logger.debug(
            f"Audit: {action.value} | {agent_name} | {tool_name} | {risk_level}"
        )

        return entry_id

    def _sanitize_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize input data for logging.

        Removes or truncates sensitive/large values.
        """
        sanitized = {}

        for key, value in input_data.items():
            # Skip potentially sensitive keys
            if any(s in key.lower() for s in ["password", "secret", "token", "key"]):
                sanitized[key] = "[REDACTED]"
            # Truncate long strings
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "... [truncated]"
            else:
                sanitized[key] = value

        return sanitized

    def log_tool_executed(
        self,
        agent_name: str,
        tool_name: str,
        risk_level: str,
        input_data: dict[str, Any],
        result: str = "",
        approved_by: str = "auto",
    ) -> int:
        """Log a successful tool execution."""
        return self.log(
            action=AuditAction.TOOL_EXECUTED,
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level,
            input_data=input_data,
            result=result,
            approved_by=approved_by,
        )

    def log_tool_denied(
        self,
        agent_name: str,
        tool_name: str,
        risk_level: str,
        input_data: dict[str, Any],
        denial_reason: str,
    ) -> int:
        """Log a denied tool execution."""
        return self.log(
            action=AuditAction.TOOL_DENIED,
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level,
            input_data=input_data,
            denial_reason=denial_reason,
        )

    def log_approval_requested(
        self,
        agent_name: str,
        tool_name: str,
        risk_level: str,
        input_data: dict[str, Any],
    ) -> int:
        """Log an approval request."""
        return self.log(
            action=AuditAction.APPROVAL_REQUESTED,
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level,
            input_data=input_data,
        )

    def log_approval_response(
        self,
        agent_name: str,
        tool_name: str,
        risk_level: str,
        approved: bool,
        reason: Optional[str] = None,
    ) -> int:
        """Log an approval response."""
        action = (
            AuditAction.APPROVAL_GRANTED if approved else AuditAction.APPROVAL_DENIED
        )
        return self.log(
            action=action,
            agent_name=agent_name,
            tool_name=tool_name,
            risk_level=risk_level,
            approved_by="user" if approved else None,
            denial_reason=reason if not approved else None,
        )

    def get_entries(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        action: Optional[AuditAction] = None,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """
        Query audit log entries.

        Args:
            since: Start timestamp filter
            until: End timestamp filter
            action: Filter by action type
            agent_name: Filter by agent
            tool_name: Filter by tool
            limit: Maximum entries to return
            offset: Offset for pagination

        Returns:
            List of matching audit entries
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        if until:
            query += " AND timestamp <= ?"
            params.append(until.isoformat())

        if action:
            query += " AND action = ?"
            params.append(action.value)

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [AuditEntry.from_row(row) for row in rows]

    def get_statistics(
        self,
        since: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Get audit statistics.

        Args:
            since: Start timestamp for statistics

        Returns:
            Dictionary with statistics
        """
        base_query = "SELECT COUNT(*) FROM audit_log"
        params: list[Any] = []

        if since:
            base_query += " WHERE timestamp >= ?"
            params = [since.isoformat()]

        with sqlite3.connect(self.db_path) as conn:
            # Total entries
            cursor = conn.execute(base_query, params)
            total = cursor.fetchone()[0]

            # By action
            by_action: dict[str, int] = {}
            for action in AuditAction:
                query = base_query.replace("1=1", f"action = '{action.value}'")
                if since:
                    query += " AND timestamp >= ?"
                cursor = conn.execute(query, params)
                count = cursor.fetchone()[0]
                if count > 0:
                    by_action[action.value] = count

            # By risk level
            by_risk: dict[str, int] = {}
            for level in ["low", "medium", "high", "critical"]:
                query = base_query.replace("1=1", f"risk_level = '{level}'")
                if since:
                    query += " AND timestamp >= ?"
                cursor = conn.execute(query, params)
                count = cursor.fetchone()[0]
                if count > 0:
                    by_risk[level] = count

        return {
            "total_entries": total,
            "by_action": by_action,
            "by_risk_level": by_risk,
            "since": since.isoformat() if since else None,
        }

    def export_to_json(
        self,
        output_path: Path,
        since: Optional[datetime] = None,
    ) -> int:
        """
        Export audit log to JSON file.

        Args:
            output_path: Path to write JSON
            since: Optional start timestamp

        Returns:
            Number of entries exported
        """
        entries = self.get_entries(since=since, limit=10000)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                [e.to_dict() for e in entries],
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"Exported {len(entries)} audit entries to {output_path}")
        return len(entries)


# Singleton instance
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """Get the singleton audit log."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


def reset_audit_log() -> None:
    """Reset the singleton audit log."""
    global _audit_log
    _audit_log = None
