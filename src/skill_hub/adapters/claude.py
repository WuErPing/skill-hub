"""Claude adapter implementation."""

from skill_hub.adapters.base import AgentAdapter


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude AI coding assistant."""

    @property
    def name(self) -> str:
        """Agent name."""
        return "claude"

    @property
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        return "~/.claude"

    @property
    def project_local_dirname(self) -> str:
        """Project-local directory name."""
        return ".claude"
