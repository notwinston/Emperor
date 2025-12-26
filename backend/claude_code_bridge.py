"""Claude Code CLI Bridge for Emperor AI Assistant.

This module provides a bridge to the Claude Code CLI, enabling:
- OAuth-based authentication (max billing mode)
- Query execution via subprocess
- Agent spawning capabilities
- Streaming response support
"""

import asyncio
import json
import shutil
import subprocess
from typing import AsyncIterator, Optional

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


class RateLimitError(BridgeError):
    """Raised when rate limited by Claude API."""

    pass


class QueryTimeoutError(BridgeError):
    """Raised when a query times out."""

    pass


# Default configuration
DEFAULT_TIMEOUT = 120  # 2 minutes
DEFAULT_MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # Exponential backoff base


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

        For Claude Code CLI v2.x, we verify by making a simple test query
        since the old `auth status` command no longer exists.

        Raises:
            AuthenticationError: If not authenticated or token invalid
        """
        try:
            # In v2.x, test authentication by making a simple query
            process = await asyncio.create_subprocess_exec(
                "claude",
                "--print",
                "--output-format", "text",
                "-p", "Reply with exactly: AUTH_OK",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30,
            )

            output = stdout.decode()
            error = stderr.decode().lower()

            # Check for authentication issues in error output
            if process.returncode != 0:
                if "unauthorized" in error or "authentication" in error or "api key" in error:
                    raise AuthenticationError(
                        "Claude Code is not authenticated.\n"
                        "Run: claude setup-token"
                    )
                elif "rate limit" in error:
                    # Rate limited means we ARE authenticated, just throttled
                    logger.info("Claude Code authentication verified (rate limited)")
                    return
                else:
                    raise AuthenticationError(
                        f"Claude Code auth check failed: {stderr.decode()}"
                    )

            # If we got a response, auth is working
            if output.strip():
                logger.info("Claude Code authentication verified")
                return

            raise AuthenticationError(
                "Claude Code returned empty response.\n"
                "Run: claude setup-token"
            )

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

    # =========================================================================
    # Query Execution Methods
    # =========================================================================

    async def query(
        self,
        prompt: str,
        timeout: int = DEFAULT_TIMEOUT,
        allowed_tools: list[str] | None = None,
        model: str | None = None,
        max_turns: int = 1,
    ) -> str:
        """
        Send a prompt to Claude and get a response.

        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait (seconds)
            allowed_tools: List of tools Claude can use (None = default, [] = none)
            model: Model to use (sonnet, opus, haiku)
            max_turns: Maximum conversation turns

        Returns:
            The response text from Claude

        Raises:
            BridgeError: If query fails
            QueryTimeoutError: If query times out
            RateLimitError: If rate limited
        """
        self.ensure_verified()

        cmd = self._build_command(
            prompt=prompt,
            output_format="text",
            allowed_tools=allowed_tools,
            model=model,
            max_turns=max_turns,
        )

        logger.debug(f"Executing query: {prompt[:50]}...")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            # Check for errors
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                self._handle_error(error_msg)

            response = stdout.decode().strip()
            logger.debug(f"Query response: {response[:100]}...")

            return response

        except asyncio.TimeoutError:
            logger.error(f"Query timed out after {timeout}s")
            raise QueryTimeoutError(
                f"Query timed out after {timeout} seconds. "
                "Try a simpler prompt or increase timeout."
            )

        except BridgeError:
            raise

        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            raise BridgeError(f"Query failed: {e}")

    async def stream_query(
        self,
        prompt: str,
        timeout: int = DEFAULT_TIMEOUT,
        allowed_tools: list[str] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a response from Claude chunk by chunk.

        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait for first chunk
            allowed_tools: List of tools Claude can use
            model: Model to use

        Yields:
            Response text chunks as they arrive

        Raises:
            BridgeError: If query fails
            QueryTimeoutError: If query times out
        """
        self.ensure_verified()

        cmd = self._build_command(
            prompt=prompt,
            output_format="stream-json",
            allowed_tools=allowed_tools,
            model=model,
            max_turns=1,
        )

        logger.debug(f"Starting streaming query: {prompt[:50]}...")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            accumulated_text = ""

            # Read stdout line by line
            while True:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=timeout,
                    )

                    if not line:
                        break

                    # Parse JSON chunk
                    try:
                        chunk = json.loads(line.decode().strip())
                    except json.JSONDecodeError:
                        continue

                    # Handle different chunk types from Claude Code CLI
                    chunk_type = chunk.get("type", "")

                    if chunk_type == "stream_event":
                        # Unwrap the nested event from Claude Code CLI format
                        event = chunk.get("event", {})
                        event_type = event.get("type", "")

                        if event_type == "content_block_delta":
                            # Extract text from delta
                            delta = event.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                accumulated_text += text
                                yield text

                        elif event_type == "message_delta":
                            # Message metadata update
                            pass

                        elif event_type == "error":
                            error_msg = event.get("error", {}).get("message", "Unknown error")
                            raise BridgeError(f"Stream error: {error_msg}")

                    elif chunk_type == "result":
                        # Final result - streaming complete
                        if chunk.get("is_error"):
                            raise BridgeError(f"CLI error: {chunk.get('result', 'Unknown error')}")

                    elif chunk_type == "error":
                        # Top-level error
                        error_msg = chunk.get("error", {}).get("message", "Unknown error")
                        raise BridgeError(f"Stream error: {error_msg}")

                except asyncio.TimeoutError:
                    if not accumulated_text:
                        raise QueryTimeoutError(
                            f"No response received within {timeout}s"
                        )
                    break

            # Check for process errors
            await process.wait()
            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode().strip()
                if error_msg and not accumulated_text:
                    self._handle_error(error_msg)

            logger.debug(f"Streaming complete. Total length: {len(accumulated_text)}")

        except BridgeError:
            raise

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise BridgeError(f"Streaming failed: {e}")

    async def query_with_retry(
        self,
        prompt: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT,
        allowed_tools: list[str] | None = None,
        model: str | None = None,
    ) -> str:
        """
        Query with automatic retry on transient failures.

        Args:
            prompt: The prompt to send
            max_retries: Maximum retry attempts
            timeout: Timeout per attempt
            allowed_tools: List of tools Claude can use
            model: Model to use

        Returns:
            The response text from Claude

        Raises:
            BridgeError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.query(
                    prompt=prompt,
                    timeout=timeout,
                    allowed_tools=allowed_tools,
                    model=model,
                )

            except RateLimitError as e:
                last_error = e
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

            except QueryTimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{max_retries}). Retrying..."
                )

            except BridgeError as e:
                # Non-retryable errors
                if "authentication" in str(e).lower():
                    raise
                last_error = e
                logger.warning(f"Error (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(1)

        raise BridgeError(f"Query failed after {max_retries} attempts: {last_error}")

    async def query_with_context(
        self,
        prompt: str,
        system_context: str | None = None,
        conversation_history: list[dict] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        allowed_tools: list[str] | None = None,
    ) -> str:
        """
        Query with additional context.

        Args:
            prompt: The user's prompt
            system_context: System instructions/context
            conversation_history: Previous messages for context
            timeout: Maximum time to wait
            allowed_tools: List of tools Claude can use

        Returns:
            The response text from Claude
        """
        # Build full prompt with context
        parts = []

        if system_context:
            parts.append(f"<system>\n{system_context}\n</system>")

        if conversation_history:
            parts.append("<conversation>")
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"<{role}>{content}</{role}>")
            parts.append("</conversation>")

        parts.append(f"<user_request>\n{prompt}\n</user_request>")

        full_prompt = "\n\n".join(parts)

        return await self.query(
            prompt=full_prompt,
            timeout=timeout,
            allowed_tools=allowed_tools,
        )

    def _build_command(
        self,
        prompt: str,
        output_format: str = "text",
        allowed_tools: list[str] | None = None,
        model: str | None = None,
        max_turns: int = 1,
    ) -> list[str]:
        """
        Build the CLI command array.

        Args:
            prompt: The prompt to send
            output_format: Output format (text, json, stream-json)
            allowed_tools: List of allowed tools
            model: Model to use
            max_turns: Maximum conversation turns

        Returns:
            Command array for subprocess
        """
        cmd = [
            "claude",
            "--print",
            "--output-format", output_format,
            "--max-turns", str(max_turns),
        ]

        # stream-json requires --verbose and --include-partial-messages for streaming
        if output_format == "stream-json":
            cmd.extend(["--verbose", "--include-partial-messages"])

        # Add model if specified
        if model:
            cmd.extend(["--model", model])

        # Add tool restrictions
        if allowed_tools is not None:
            if len(allowed_tools) == 0:
                cmd.extend(["--allowedTools", ""])
            else:
                cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        # Add prompt last
        cmd.extend(["-p", prompt])

        return cmd

    def _handle_error(self, error_msg: str) -> None:
        """
        Handle error messages from CLI and raise appropriate exceptions.

        Args:
            error_msg: The error message from stderr

        Raises:
            RateLimitError: If rate limited
            AuthenticationError: If auth issue
            BridgeError: For other errors
        """
        error_lower = error_msg.lower()

        if "rate limit" in error_lower or "too many requests" in error_lower:
            raise RateLimitError(
                "Rate limited by Claude API. Please wait and try again."
            )

        if "authentication" in error_lower or "unauthorized" in error_lower:
            raise AuthenticationError(
                "Authentication failed. Run: claude auth login"
            )

        if "not found" in error_lower or "invalid model" in error_lower:
            raise BridgeError(f"Invalid request: {error_msg}")

        raise BridgeError(f"Claude CLI error: {error_msg}")


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
