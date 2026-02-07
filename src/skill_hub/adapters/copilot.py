"""GitHub Copilot adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class CopilotAdapter(AgentAdapter):
    """Adapter for GitHub Copilot coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "copilot"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.copilot"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".github"
