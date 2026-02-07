"""Gemini CLI adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class GeminiAdapter(AgentAdapter):
    """Adapter for Gemini CLI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "gemini"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.gemini"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".gemini"
