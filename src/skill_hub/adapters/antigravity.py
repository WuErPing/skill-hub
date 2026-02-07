"""Antigravity adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class AntigravityAdapter(AgentAdapter):
    """Adapter for Google Antigravity coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "antigravity"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.gemini/antigravity"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".agent"
