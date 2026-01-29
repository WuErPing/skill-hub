"""Qoder adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class QoderAdapter(AgentAdapter):
    """Adapter for Qoder AI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "qoder"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.qoder"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".qoder"
