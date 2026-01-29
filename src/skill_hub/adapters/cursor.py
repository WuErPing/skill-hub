"""Cursor adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class CursorAdapter(AgentAdapter):
    """Adapter for Cursor AI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "cursor"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.cursor"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".cursor"
