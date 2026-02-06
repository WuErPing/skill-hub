"""Base adapter interface for agent integrations."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from skill_hub.models import AgentConfig
from skill_hub.utils import ensure_directory, expand_home, find_git_root

logger = logging.getLogger(__name__)


class AgentAdapter(ABC):
    """Abstract base class for agent adapters."""

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        """
        Initialize adapter with configuration.

        Args:
            config: Agent-specific configuration
        """
        self.config = config or AgentConfig()
        self._enabled = self.config.enabled

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name (e.g., 'cursor', 'claude')."""
        pass

    @property
    @abstractmethod
    def default_global_path(self) -> str:
        """Default global skills directory path."""
        pass

    @property
    @abstractmethod
    def project_local_dirname(self) -> str:
        """Project-local directory name (e.g., '.cursor')."""
        pass

    def is_enabled(self) -> bool:
        """Check if adapter is enabled."""
        return self._enabled

    def get_global_path(self) -> Path:
        """Get global skills directory path."""
        if self.config.global_path:
            return expand_home(self.config.global_path)
        return expand_home(self.default_global_path)

    def get_project_paths(self, start_dir: Optional[Path] = None) -> List[Path]:
        """
        Get project-local skills directory paths.

        Walks up from start_dir to find project root, then looks for
        agent-specific config directory.

        Args:
            start_dir: Starting directory (defaults to cwd)

        Returns:
            List of paths to project-local skill directories
        """
        paths = []
        git_root = find_git_root(start_dir)

        search_dirs = []
        if git_root:
            search_dirs.append(git_root)
        if start_dir:
            search_dirs.append(start_dir)
        else:
            search_dirs.append(Path.cwd())

        for search_dir in search_dirs:
            project_config = search_dir / self.project_local_dirname
            if project_config.exists():
                paths.append(project_config)

        return paths

    def get_shared_skills_path(self, start_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Get shared `.agents` directory path if it exists in project.

        This discovers the agent-agnostic shared skills directory that can be
        used by all AI coding agents in a project. Skills are expected to be
        in `.agents/skills/` subdirectory.

        Args:
            start_dir: Starting directory (defaults to cwd)

        Returns:
            Path to `.agents` if `.agents/skills` exists, None otherwise
        """
        git_root = find_git_root(start_dir)
        if git_root:
            agents_dir = git_root / ".agents"
            skills_dir = agents_dir / "skills"
            if skills_dir.exists():
                return agents_dir
        return None

    def get_all_search_paths(self) -> List[Path]:
        """
        Get all search paths (shared + project-local + global).

        Returns:
            List of all paths to search for skills, in priority order:
            1. Shared `.agents/skills/` (if exists)
            2. Project-local paths (e.g., `.cursor/skills/`)
            3. Global path (e.g., `~/.cursor/skills/`)
        """
        paths = []

        # Add shared skills path (highest priority)
        shared_path = self.get_shared_skills_path()
        if shared_path:
            paths.append(shared_path)

        # Add project-local paths
        paths.extend(self.get_project_paths())

        # Add global path
        global_path = self.get_global_path()
        if global_path.exists() or self.config.sync.get("create_directories", True):
            paths.append(global_path)

        return paths

    def write_skill(self, skill_name: str, content: str) -> bool:
        """
        Write skill to adapter's global directory.

        Args:
            skill_name: Name of the skill
            content: Full SKILL.md content

        Returns:
            True if successful, False otherwise
        """
        try:
            global_path = self.get_global_path()
            skill_dir = global_path / "skills" / skill_name
            ensure_directory(skill_dir)

            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(content, encoding="utf-8")

            logger.info(f"Wrote skill '{skill_name}' to {self.name} at {skill_file}")
            return True

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write skill '{skill_name}' to {self.name}: {e}")
            return False

    def health_check(self) -> dict:
        """
        Perform health check on adapter.

        Returns:
            Dictionary with health check results
        """
        results = {
            "agent": self.name,
            "enabled": self.is_enabled(),
            "global_path": str(self.get_global_path()),
            "global_path_exists": self.get_global_path().exists(),
            "global_path_writable": False,
            "project_paths": [],
            "shared_skills_path": None,
            "shared_skills_exists": False,
        }

        # Check shared skills path
        shared_path = self.get_shared_skills_path()
        if shared_path:
            results["shared_skills_path"] = str(shared_path)
            results["shared_skills_exists"] = True

        # Check if global path is writable
        try:
            global_path = self.get_global_path()
            if global_path.exists():
                test_file = global_path / ".skill-hub-test"
                test_file.touch()
                test_file.unlink()
                results["global_path_writable"] = True
        except (OSError, PermissionError):
            pass

        # Check project paths
        for path in self.get_project_paths():
            results["project_paths"].append(
                {"path": str(path), "exists": path.exists()}
            )

        return results
