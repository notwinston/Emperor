"""Claude Code CLI Bridge for Emperor AI Assistant.

This module provides a bridge to the Claude Code CLI, enabling:
- OAuth-based authentication (max billing mode)
- Query execution via subprocess
- Agent spawning capabilities
- Streaming response support
"""

import asyncio
import shutil
import subprocess
from typing import Optional

from config import settings, get_logger

logger = get_logger(__name__)


class BridgeError(Exception):
    """Base exception for Claude Code Bridge errors."""

    pass


class CLINotInstalledError(BridgeError):
    """Raised when Claude Code CLI is not installed."""

    pass


class AuthenticationError(BridgeError):
    """Raised when Claude Code is not authenticated."""

    pass


class ClaudeCodeBridge:
    """
    Bridge to Claude Code CLI for AI interactions.

    This class wraps the Claude Code CLI to provide:
    - Verified connection to Claude
    - Query execution with proper error handling
    - Agent spawning for complex tasks
    """

    def __init__(self):
        """Initialize the bridge (does not verify yet)."""
        self.cli_path: Optional[str] = None
        self.cli_version: Optional[str] = None
        self.is_verified: bool = False

    async def verify(self) -> None:
        """
        Verify Claude Code CLI is installed and authenticated.

        Raises:
            CLINotInstalledError: If Claude Code CLI is not installed
            AuthenticationError: If not authenticated with Claude
            BridgeError: If verification fails for other reasons
        """
        logger.info("Verifying Claude Code Bridge...")

        # Step 1: Check CLI is installed
        self._check_cli_installed()

        # Step 2: Check authentication
        await self._check_authenticated()

        # Step 3: Optional test query
        if settings.debug:
            await self._test_connection()

        self.is_verified = True
        logger.info("Claude Code Bridge verified and ready")

    def _check_cli_installed(self) -> None:
        """
        Verify Claude Code CLI is installed and accessible.

        Raises:
            CLINotInstalledError: If CLI is not found or not working
        """
        # Check if 'claude' command exists in PATH
        self.cli_path = shutil.which("claude")

        if not self.cli_path:
            raise CLINotInstalledError(
                "Claude Code CLI not found in PATH.\n"
                "Install with: npm install -g @anthropic-ai/claude-code\n"
                "Or: brew install claude-code"
            )

        logger.debug(f"Found Claude CLI at: {self.cli_path}")

        # Check version to verify it works
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise CLINotInstalledError(
                    f"Claude Code CLI returned error: {result.stderr}"
                )

            self.cli_version = result.stdout.strip()
            logger.info(f"Claude Code CLI version: {self.cli_version}")

        except subprocess.TimeoutExpired:
            raise CLINotInstalledError("Claude Code CLI timed out during version check")

        except FileNotFoundError:
            raise CLINotInstalledError(
                "Claude Code CLI not found.\n"
                "Install with: npm install -g @anthropic-ai/claude-code"
            )

    async def _check_authenticated(self) -> None:
        """
        Verify user is authenticated with Claude.

        Raises:
            AuthenticationError: If not authenticated or token invalid
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "claude",
                "auth",
                "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=15,
            )

            output = stdout.decode().lower()
            error = stderr.decode().lower()

            # Check for authentication issues
            if process.returncode != 0:
                if "not authenticated" in output or "not authenticated" in error:
                    raise AuthenticationError(
                        "Claude Code is not authenticated.\n"
                        "Run: claude auth login"
                    )
                elif "expired" in output or "expired" in error:
                    raise AuthenticationError(
                        "Claude Code authentication has expired.\n"
                        "Run: claude auth login"
                    )
                else:
                    raise AuthenticationError(
                        f"Claude Code auth check failed: {stderr.decode()}"
                    )

            # Check for explicit "not authenticated" in success output
            if "not authenticated" in output:
                raise AuthenticationError(
                    "Claude Code is not authenticated.\n"
                    "Run: claude auth login"
                )

            logger.info("Claude Code authentication verified")

        except asyncio.TimeoutError:
            raise BridgeError("Authentication check timed out")

    async def _test_connection(self) -> None:
        """
        Test the connection with a simple query.

        This is optional and only runs in debug mode.

        Raises:
            BridgeError: If test query fails
        """
        logger.debug("Testing Claude Code connection...")

        try:
            process = await asyncio.create_subprocess_exec(
                "claude",
                "--print",
                "--output-format", "text",
                "-p", "Reply with exactly: OK",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30,
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise BridgeError(f"Test query failed: {error_msg}")

            response = stdout.decode().strip()
            logger.debug(f"Test query response: {response[:50]}...")
            logger.info("Claude Code connection test passed")

        except asyncio.TimeoutError:
            raise BridgeError("Test query timed out (30s)")

    def ensure_verified(self) -> None:
        """
        Ensure the bridge has been verified before use.

        Raises:
            BridgeError: If bridge has not been verified
        """
        if not self.is_verified:
            raise BridgeError(
                "Claude Code Bridge not verified. "
                "Call await bridge.verify() first."
            )

    @property
    def status(self) -> dict:
        """Return current bridge status."""
        return {
            "verified": self.is_verified,
            "cli_path": self.cli_path,
            "cli_version": self.cli_version,
        }


# Singleton instance
bridge: Optional[ClaudeCodeBridge] = None


def get_bridge() -> ClaudeCodeBridge:
    """Get the singleton bridge instance."""
    global bridge
    if bridge is None:
        bridge = ClaudeCodeBridge()
    return bridge


async def init_bridge() -> ClaudeCodeBridge:
    """Initialize and verify the bridge."""
    b = get_bridge()
    await b.verify()
    return b
