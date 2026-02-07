"""Codex adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class CodexAdapter(AgentAdapter):
    """Adapter for OpenAI Codex coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "codex"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.codex"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".codex"
