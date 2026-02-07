"""Windsurf adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class WindsurfAdapter(AgentAdapter):
    """Adapter for Windsurf AI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "windsurf"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.codeium/windsurf"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".windsurf"
