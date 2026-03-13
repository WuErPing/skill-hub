"""Utility functions for skill-hub."""

from pathlib import Path


def expand_home(path: str) -> Path:
    """
    Expand ~ to home directory cross-platform.

    Args:
        path: Path string that may contain ~

    Returns:
        Resolved Path object with home directory expanded
    """
    return Path(path).expanduser().resolve()
