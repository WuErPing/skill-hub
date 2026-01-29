"""Utility functions for skill-hub."""

import hashlib
import re
from pathlib import Path
from typing import Optional


def expand_home(path: str) -> Path:
    """
    Expand ~ to home directory cross-platform.

    Args:
        path: Path string that may contain ~

    Returns:
        Resolved Path object with home directory expanded
    """
    return Path(path).expanduser().resolve()


def validate_skill_name(name: str) -> bool:
    """
    Validate skill name format.

    Name must:
    - Be 1-64 characters
    - Be lowercase alphanumeric with single hyphen separators
    - Not start or end with -
    - Not contain consecutive --

    Args:
        name: Skill name to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    return bool(re.match(pattern, name)) and 1 <= len(name) <= 64


def validate_description(description: str) -> bool:
    """
    Validate skill description length.

    Args:
        description: Description to validate

    Returns:
        True if valid (1-1024 characters), False otherwise
    """
    return 1 <= len(description) <= 1024


def compute_checksum(content: str) -> str:
    """
    Compute SHA-256 checksum of content.

    Args:
        content: String content to checksum

    Returns:
        Hex string of SHA-256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_git_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find git repository root by walking up directory tree.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Path to git root if found, None otherwise
    """
    current = start_path or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, creating if needed.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def safe_write_file(path: Path, content: str) -> None:
    """
    Safely write file using atomic rename.

    Args:
        path: File path to write
        content: Content to write
    """
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)
