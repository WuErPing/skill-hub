"""OpenCode adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class OpenCodeAdapter(AgentAdapter):
    """Adapter for OpenCode AI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "opencode"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.config/opencode"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".opencode"
