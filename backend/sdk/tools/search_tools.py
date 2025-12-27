"""Search tools for SDK agents.

Provides tools for searching files, content, and the web.
Used by Research Lead, Code Lead, and other agents that need search capabilities.
"""

import asyncio
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from config import settings, get_logger
from .base import BaseTool, ToolParameter, ParameterType

logger = get_logger(__name__)


class GrepTool(BaseTool):
    """Search for a pattern in files."""

    name = "grep"
    description = (
        "Search for a regex pattern in files within a directory. "
        "Returns matching lines with file paths and line numbers. "
        "Use this to find code patterns, function definitions, or text content."
    )
    parameters = [
        ToolParameter(
            name="pattern",
            type=ParameterType.STRING,
            description="Regular expression pattern to search for",
        ),
        ToolParameter(
            name="path",
            type=ParameterType.STRING,
            description="Directory or file to search in",
        ),
        ToolParameter(
            name="file_pattern",
            type=ParameterType.STRING,
            description="Glob pattern for files to search (e.g., '*.py', '*.ts')",
            required=False,
            default="*",
        ),
        ToolParameter(
            name="case_sensitive",
            type=ParameterType.BOOLEAN,
            description="Whether the search is case-sensitive",
            required=False,
            default=True,
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of results to return",
            required=False,
            default=50,
        ),
    ]

    async def execute(
        self,
        pattern: str,
        path: str,
        file_pattern: str = "*",
        case_sensitive: bool = True,
        max_results: int = 50,
    ) -> str:
        """
        Search for pattern in files.

        Args:
            pattern: Regex pattern to search for
            path: Directory or file to search
            file_pattern: Glob pattern for file filtering
            case_sensitive: Case sensitivity
            max_results: Maximum results

        Returns:
            Formatted search results
        """
        search_path = Path(path)

        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        logger.debug(f"Grep search: '{pattern}' in {path}")

        # Try to use ripgrep if available (faster)
        rg_path = shutil.which("rg")
        if rg_path:
            return await self._search_with_ripgrep(
                pattern, search_path, file_pattern, case_sensitive, max_results
            )

        # Fallback to Python implementation
        return await self._search_with_python(
            pattern, search_path, file_pattern, case_sensitive, max_results
        )

    async def _search_with_ripgrep(
        self,
        pattern: str,
        path: Path,
        file_pattern: str,
        case_sensitive: bool,
        max_results: int,
    ) -> str:
        """Use ripgrep for fast searching."""
        cmd = ["rg", "--line-number", "--no-heading", "--color=never"]

        if not case_sensitive:
            cmd.append("-i")

        if file_pattern != "*":
            cmd.extend(["-g", file_pattern])

        cmd.extend(["-m", str(max_results), pattern, str(path)])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30,
            )

            if process.returncode == 0:
                output = stdout.decode("utf-8", errors="replace")
                lines = output.strip().split("\n")
                return self._format_results(lines, pattern, max_results)
            elif process.returncode == 1:
                # No matches found
                return f"No matches found for pattern: {pattern}"
            else:
                # Error occurred, fall back to Python
                logger.warning(f"ripgrep error: {stderr.decode()}")
                return await self._search_with_python(
                    pattern, path, file_pattern, case_sensitive, max_results
                )

        except asyncio.TimeoutError:
            return "Search timed out after 30 seconds"

    async def _search_with_python(
        self,
        pattern: str,
        path: Path,
        file_pattern: str,
        case_sensitive: bool,
        max_results: int,
    ) -> str:
        """Python fallback for grep functionality."""
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        results = []

        # Get files to search
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob(file_pattern))

        # Filter out binary files and hidden files
        files = [
            f for f in files
            if f.is_file()
            and not f.name.startswith(".")
            and not any(part.startswith(".") for part in f.parts)
        ]

        for file_path in files:
            if len(results) >= max_results:
                break

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            rel_path = file_path.relative_to(path) if path.is_dir() else file_path.name
                            results.append(f"{rel_path}:{line_num}:{line.rstrip()}")
                            if len(results) >= max_results:
                                break
            except (PermissionError, OSError):
                continue

        return self._format_results(results, pattern, max_results)

    def _format_results(
        self,
        lines: list[str],
        pattern: str,
        max_results: int,
    ) -> str:
        """Format search results."""
        if not lines or (len(lines) == 1 and not lines[0]):
            return f"No matches found for pattern: {pattern}"

        output = [f"Search results for: {pattern}", ""]

        for line in lines[:max_results]:
            if line:
                output.append(line)

        if len(lines) >= max_results:
            output.append(f"\n... (showing first {max_results} results)")

        output.append(f"\nTotal: {len(lines)} matches")

        return "\n".join(output)


class GlobTool(BaseTool):
    """Find files matching a glob pattern."""

    name = "glob"
    description = (
        "Find files matching a glob pattern in a directory. "
        "Supports patterns like '*.py', '**/*.ts', 'src/**/*.tsx'. "
        "Use this to locate files by name or extension."
    )
    parameters = [
        ToolParameter(
            name="pattern",
            type=ParameterType.STRING,
            description="Glob pattern (e.g., '*.py', '**/*.ts', 'src/**/*.js')",
        ),
        ToolParameter(
            name="path",
            type=ParameterType.STRING,
            description="Directory to search in",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="max_results",
            type=ParameterType.INTEGER,
            description="Maximum number of results to return",
            required=False,
            default=100,
        ),
    ]

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 100,
    ) -> str:
        """
        Find files matching glob pattern.

        Args:
            pattern: Glob pattern
            path: Directory to search
            max_results: Maximum results

        Returns:
            List of matching file paths
        """
        search_path = Path(path)

        if not search_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not search_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        logger.debug(f"Glob search: '{pattern}' in {path}")

        # Find matching files
        matches = list(search_path.glob(pattern))

        # Filter out hidden files
        matches = [
            m for m in matches
            if not m.name.startswith(".")
            and not any(part.startswith(".") for part in m.parts)
        ]

        # Sort by path
        matches = sorted(matches, key=lambda x: str(x).lower())

        # Format output
        lines = [f"Files matching: {pattern}", ""]

        for match in matches[:max_results]:
            rel_path = match.relative_to(search_path)
            if match.is_dir():
                lines.append(f"📁 {rel_path}/")
            else:
                size = match.stat().st_size
                lines.append(f"📄 {rel_path} ({self._format_size(size)})")

        if len(matches) > max_results:
            lines.append(f"\n... and {len(matches) - max_results} more")

        lines.append(f"\nTotal: {len(matches)} matches")

        return "\n".join(lines)

    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# Web Search - Use Anthropic's Built-in Tool
# =============================================================================
#
# For web search, use Anthropic's built-in web_search tool instead of a custom
# implementation. Add it to your tools list like this:
#
#     tools = [
#         {
#             "type": "web_search_20250305",
#             "name": "web_search",
#             "max_uses": 5,  # Optional: limit searches per request
#             "allowed_domains": ["docs.python.org"],  # Optional: restrict domains
#         }
#     ]
#
# Cost: $10 per 1,000 searches (plus token costs)
# Features: Automatic citations, real-time results, server-side execution
#
# See: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool
# =============================================================================


def get_web_search_tool_definition(
    max_uses: int = 5,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get the Anthropic built-in web search tool definition.

    Add this to your agent's tools list for web search capability.

    Args:
        max_uses: Maximum searches per request (default 5)
        allowed_domains: Only include results from these domains (optional)
        blocked_domains: Never include results from these domains (optional)

    Returns:
        Tool definition dict for Anthropic API

    Example:
        >>> tools = other_tools + [get_web_search_tool_definition(max_uses=3)]
    """
    tool: dict[str, Any] = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": max_uses,
    }

    if allowed_domains:
        tool["allowed_domains"] = allowed_domains
    if blocked_domains:
        tool["blocked_domains"] = blocked_domains

    return tool


# Tool instances for easy access
grep = GrepTool()
glob_search = GlobTool()

# All search tools (web search is built-in, not a custom tool)
SEARCH_TOOLS = [grep, glob_search]
