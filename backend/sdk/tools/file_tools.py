"""File system tools for SDK agents.

Provides tools for reading, writing, and listing files/directories.
Used by Code Lead, Programmer, and other agents that need file access.
"""

import os
from pathlib import Path
from typing import Any, Optional

from config import settings, get_logger
from .base import BaseTool, ToolParameter, ParameterType

logger = get_logger(__name__)


class ReadFileTool(BaseTool):
    """Read the contents of a file."""

    name = "read_file"
    description = (
        "Read the contents of a file at the given path. "
        "Returns the file contents as a string. "
        "Use this to examine source code, configuration files, or any text file."
    )
    parameters = [
        ToolParameter(
            name="path",
            type=ParameterType.STRING,
            description="Absolute or relative path to the file to read",
        ),
        ToolParameter(
            name="max_lines",
            type=ParameterType.INTEGER,
            description="Maximum number of lines to read (0 for all)",
            required=False,
            default=0,
        ),
    ]

    async def execute(self, path: str, max_lines: int = 0) -> str:
        """
        Read file contents.

        Args:
            path: Path to the file
            max_lines: Maximum lines to read (0 = all)

        Returns:
            File contents as string
        """
        file_path = Path(path)

        # Security: Ensure path is within allowed directories
        if not self._is_path_allowed(file_path):
            raise PermissionError(f"Access denied: {path}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")

        logger.debug(f"Reading file: {path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            if max_lines > 0:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (truncated after {max_lines} lines)")
                        break
                    lines.append(line)
                content = "".join(lines)
            else:
                content = f.read()

        # Truncate very large files
        max_size = 100000  # ~100KB
        if len(content) > max_size:
            content = content[:max_size] + f"\n\n... (truncated, showing first {max_size} characters)"

        return content

    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        # Resolve to absolute path
        try:
            resolved = path.resolve()
        except (OSError, ValueError):
            return False

        # Allow paths within project root
        project_root = settings.project_root.resolve()
        try:
            resolved.relative_to(project_root)
            return True
        except ValueError:
            pass

        # Allow paths within data directory
        data_dir = settings.data_dir.resolve()
        try:
            resolved.relative_to(data_dir)
            return True
        except ValueError:
            pass

        # Allow common safe directories
        home = Path.home()
        allowed_dirs = [
            home / "Documents",
            home / "Projects",
            home / "Code",
            home / "Development",
        ]

        for allowed in allowed_dirs:
            if allowed.exists():
                try:
                    resolved.relative_to(allowed.resolve())
                    return True
                except ValueError:
                    continue

        return False


class WriteFileTool(BaseTool):
    """Write content to a file."""

    name = "write_file"
    description = (
        "Write content to a file at the given path. "
        "Creates the file if it doesn't exist, overwrites if it does. "
        "Use this to create or modify source code, configuration files, etc."
    )
    parameters = [
        ToolParameter(
            name="path",
            type=ParameterType.STRING,
            description="Absolute or relative path to the file to write",
        ),
        ToolParameter(
            name="content",
            type=ParameterType.STRING,
            description="Content to write to the file",
        ),
        ToolParameter(
            name="create_dirs",
            type=ParameterType.BOOLEAN,
            description="Create parent directories if they don't exist",
            required=False,
            default=True,
        ),
    ]

    async def execute(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> str:
        """
        Write content to a file.

        Args:
            path: Path to the file
            content: Content to write
            create_dirs: Whether to create parent directories

        Returns:
            Success message
        """
        file_path = Path(path)

        # Security: Ensure path is within allowed directories
        if not self._is_path_allowed(file_path):
            raise PermissionError(f"Access denied: {path}")

        # Create parent directories if needed
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Writing file: {path} ({len(content)} bytes)")

        # Check if file exists (for logging)
        existed = file_path.exists()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        action = "Updated" if existed else "Created"
        return f"{action} file: {path} ({len(content)} bytes written)"

    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        # Same logic as ReadFileTool
        try:
            resolved = path.resolve() if path.exists() else path.parent.resolve() / path.name
        except (OSError, ValueError):
            return False

        project_root = settings.project_root.resolve()
        try:
            resolved.relative_to(project_root)
            return True
        except ValueError:
            pass

        data_dir = settings.data_dir.resolve()
        try:
            resolved.relative_to(data_dir)
            return True
        except ValueError:
            pass

        return False


class ListDirectoryTool(BaseTool):
    """List contents of a directory."""

    name = "list_directory"
    description = (
        "List files and subdirectories in a directory. "
        "Optionally filter by pattern. "
        "Use this to explore project structure or find files."
    )
    parameters = [
        ToolParameter(
            name="path",
            type=ParameterType.STRING,
            description="Path to the directory to list",
        ),
        ToolParameter(
            name="pattern",
            type=ParameterType.STRING,
            description="Glob pattern to filter results (e.g., '*.py', '**/*.ts')",
            required=False,
            default="*",
        ),
        ToolParameter(
            name="recursive",
            type=ParameterType.BOOLEAN,
            description="List subdirectories recursively",
            required=False,
            default=False,
        ),
        ToolParameter(
            name="include_hidden",
            type=ParameterType.BOOLEAN,
            description="Include hidden files (starting with .)",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        path: str,
        pattern: str = "*",
        recursive: bool = False,
        include_hidden: bool = False,
    ) -> str:
        """
        List directory contents.

        Args:
            path: Directory path
            pattern: Glob pattern for filtering
            recursive: Whether to search recursively
            include_hidden: Whether to include hidden files

        Returns:
            Formatted list of files/directories
        """
        dir_path = Path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        logger.debug(f"Listing directory: {path} (pattern: {pattern})")

        # Get matching files
        if recursive:
            if "**" not in pattern:
                pattern = f"**/{pattern}"
            matches = list(dir_path.glob(pattern))
        else:
            matches = list(dir_path.glob(pattern))

        # Filter hidden files if needed
        if not include_hidden:
            matches = [m for m in matches if not m.name.startswith(".")]

        # Sort: directories first, then files, alphabetically
        dirs = sorted([m for m in matches if m.is_dir()], key=lambda x: x.name.lower())
        files = sorted([m for m in matches if m.is_file()], key=lambda x: x.name.lower())

        # Format output
        lines = [f"Contents of {path}:", ""]

        if dirs:
            lines.append("Directories:")
            for d in dirs[:50]:  # Limit to 50 directories
                rel_path = d.relative_to(dir_path) if recursive else d.name
                lines.append(f"  📁 {rel_path}/")
            if len(dirs) > 50:
                lines.append(f"  ... and {len(dirs) - 50} more directories")
            lines.append("")

        if files:
            lines.append("Files:")
            for f in files[:100]:  # Limit to 100 files
                rel_path = f.relative_to(dir_path) if recursive else f.name
                size = f.stat().st_size
                size_str = self._format_size(size)
                lines.append(f"  📄 {rel_path} ({size_str})")
            if len(files) > 100:
                lines.append(f"  ... and {len(files) - 100} more files")

        if not dirs and not files:
            lines.append("(empty or no matches)")

        lines.append("")
        lines.append(f"Total: {len(dirs)} directories, {len(files)} files")

        return "\n".join(lines)

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# Tool instances for easy access
read_file = ReadFileTool()
write_file = WriteFileTool()
list_directory = ListDirectoryTool()

# All file tools
FILE_TOOLS = [read_file, write_file, list_directory]
