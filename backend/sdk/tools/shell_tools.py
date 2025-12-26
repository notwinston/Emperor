"""Shell execution tools for SDK agents.

Provides tools for executing shell commands with safety controls.
Used by Task Lead, Executor, and other agents that need system access.

IMPORTANT: Dangerous commands require user approval before execution.
"""

import asyncio
import re
import shlex
from typing import Any, Callable, Optional

from config import settings, get_logger
from .base import BaseTool, ToolParameter, ParameterType

logger = get_logger(__name__)


# Dangerous command patterns that require approval
DANGEROUS_PATTERNS = [
    # Destructive file operations
    r"\brm\s+(-[rfR]+\s+)?/",  # rm with absolute paths
    r"\brm\s+-[rfR]*\s",  # rm with recursive/force flags
    r"\brmdir\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r"\bformat\b",

    # Privilege escalation
    r"\bsudo\b",
    r"\bsu\b",
    r"\bdoas\b",

    # Permission changes
    r"\bchmod\s+777\b",
    r"\bchown\b.*root",
    r"\bchgrp\b",

    # System modifications
    r"\bsystemctl\s+(stop|disable|mask)\b",
    r"\bservice\s+\w+\s+(stop|disable)\b",
    r"\bkill\s+-9\b",
    r"\bkillall\b",
    r"\bpkill\b",

    # Network operations
    r"\biptables\b",
    r"\bfirewall\b",

    # Dangerous redirects
    r">\s*/dev/",
    r">\s*/etc/",
    r">\s*/sys/",
    r">\s*/proc/",

    # Package management (can break system)
    r"\bapt\s+(remove|purge|autoremove)\b",
    r"\byum\s+(remove|erase)\b",
    r"\bbrew\s+uninstall\b",
    r"\bpip\s+uninstall\b",
    r"\bnpm\s+uninstall\s+-g\b",

    # Git destructive operations
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-fd\b",

    # SSH/Remote
    r"\bssh\b.*rm\b",
]

# Commands that are always blocked
BLOCKED_COMMANDS = [
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    ":(){ :|:& };:",  # Fork bomb
]

# Safe command prefixes (don't require approval)
SAFE_PREFIXES = [
    "echo",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "grep",
    "find",
    "ls",
    "pwd",
    "cd",
    "which",
    "whereis",
    "type",
    "file",
    "wc",
    "sort",
    "uniq",
    "diff",
    "date",
    "cal",
    "whoami",
    "hostname",
    "uname",
    "env",
    "printenv",
    "python --version",
    "python3 --version",
    "node --version",
    "npm --version",
    "git status",
    "git log",
    "git diff",
    "git branch",
    "git remote -v",
]


# Type for approval callback
ApprovalCallback = Callable[[str, str], asyncio.Future[bool]]

# Global approval callback (set by the application)
_approval_callback: Optional[ApprovalCallback] = None


def set_approval_callback(callback: ApprovalCallback) -> None:
    """
    Set the callback for requesting command approval.

    Args:
        callback: Async function that takes (command, reason) and returns bool
    """
    global _approval_callback
    _approval_callback = callback


class ExecuteCommandTool(BaseTool):
    """Execute a shell command with safety controls."""

    name = "execute_command"
    description = (
        "Execute a shell command and return the output. "
        "Dangerous commands require user approval before execution. "
        "Use this to run build commands, tests, git operations, etc."
    )
    parameters = [
        ToolParameter(
            name="command",
            type=ParameterType.STRING,
            description="The shell command to execute",
        ),
        ToolParameter(
            name="working_dir",
            type=ParameterType.STRING,
            description="Working directory for the command",
            required=False,
        ),
        ToolParameter(
            name="timeout",
            type=ParameterType.INTEGER,
            description="Timeout in seconds (default 60, max 300)",
            required=False,
            default=60,
        ),
    ]

    def __init__(self):
        """Initialize the tool."""
        super().__init__()
        self._dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

    async def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 60,
    ) -> str:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            working_dir: Working directory
            timeout: Timeout in seconds

        Returns:
            Command output (stdout + stderr)
        """
        # Validate timeout
        timeout = min(max(timeout, 1), 300)  # Between 1 and 300 seconds

        # Check for blocked commands
        if self._is_blocked(command):
            raise PermissionError(
                f"Command blocked for safety: {command}\n"
                "This command is not allowed as it could harm the system."
            )

        # Check if command is dangerous
        is_dangerous, reason = self._is_dangerous(command)

        if is_dangerous:
            logger.warning(f"Dangerous command detected: {command} ({reason})")

            # Request approval
            approved = await self._request_approval(command, reason)

            if not approved:
                return f"Command rejected by user: {command}\nReason: {reason}"

            logger.info(f"Dangerous command approved: {command}")

        # Execute the command
        logger.debug(f"Executing command: {command}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Format result
            result_parts = []

            if stdout_str:
                result_parts.append(f"STDOUT:\n{stdout_str}")

            if stderr_str:
                result_parts.append(f"STDERR:\n{stderr_str}")

            result_parts.append(f"\nExit code: {process.returncode}")

            result = "\n".join(result_parts)

            # Truncate if too long
            max_output = 50000
            if len(result) > max_output:
                result = result[:max_output] + f"\n\n... (output truncated at {max_output} characters)"

            return result

        except asyncio.TimeoutError:
            return f"Command timed out after {timeout} seconds: {command}"

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return f"Error executing command: {e}"

    def _is_blocked(self, command: str) -> bool:
        """Check if command is in the blocked list."""
        command_lower = command.lower().strip()

        for blocked in BLOCKED_COMMANDS:
            if blocked in command_lower:
                return True

        return False

    def _is_dangerous(self, command: str) -> tuple[bool, str]:
        """
        Check if command matches dangerous patterns.

        Returns:
            (is_dangerous, reason)
        """
        # Check if it's a known safe command
        command_stripped = command.strip()
        for safe in SAFE_PREFIXES:
            if command_stripped.startswith(safe):
                return False, ""

        # Check dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern.search(command):
                return True, f"Matches dangerous pattern: {pattern.pattern}"

        return False, ""

    async def _request_approval(self, command: str, reason: str) -> bool:
        """
        Request user approval for a dangerous command.

        Args:
            command: The command to approve
            reason: Why approval is needed

        Returns:
            True if approved, False otherwise
        """
        global _approval_callback

        if _approval_callback:
            try:
                return await _approval_callback(command, reason)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
                return False

        # No callback configured - deny by default in production
        if not settings.debug:
            logger.warning("No approval callback configured, denying dangerous command")
            return False

        # In debug mode, log and allow (for testing)
        logger.warning(f"DEBUG MODE: Auto-approving dangerous command: {command}")
        return True


class BackgroundCommandTool(BaseTool):
    """Execute a command in the background."""

    name = "background_command"
    description = (
        "Start a long-running command in the background. "
        "Returns immediately with a process ID for monitoring. "
        "Use this for servers, watch processes, or long builds."
    )
    parameters = [
        ToolParameter(
            name="command",
            type=ParameterType.STRING,
            description="The shell command to run in background",
        ),
        ToolParameter(
            name="working_dir",
            type=ParameterType.STRING,
            description="Working directory for the command",
            required=False,
        ),
    ]

    # Track background processes
    _processes: dict[int, asyncio.subprocess.Process] = {}

    async def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
    ) -> str:
        """
        Start a background command.

        Args:
            command: Command to run
            working_dir: Working directory

        Returns:
            Process info message
        """
        logger.debug(f"Starting background command: {command}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            # Track the process
            self._processes[process.pid] = process

            return (
                f"Background process started\n"
                f"PID: {process.pid}\n"
                f"Command: {command}\n\n"
                f"Use 'kill {process.pid}' to stop the process"
            )

        except Exception as e:
            logger.error(f"Failed to start background command: {e}")
            return f"Error starting background command: {e}"

    @classmethod
    def get_process(cls, pid: int) -> Optional[asyncio.subprocess.Process]:
        """Get a tracked background process by PID."""
        return cls._processes.get(pid)

    @classmethod
    def stop_process(cls, pid: int) -> bool:
        """Stop a background process."""
        process = cls._processes.get(pid)
        if process:
            process.terminate()
            del cls._processes[pid]
            return True
        return False


# Tool instances for easy access
execute_command = ExecuteCommandTool()
background_command = BackgroundCommandTool()

# All shell tools
SHELL_TOOLS = [execute_command, background_command]
