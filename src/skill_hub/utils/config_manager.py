"""Configuration management utilities."""

import json
import logging
from pathlib import Path
from typing import Optional

from skill_hub.models import AgentConfig, Config, RepositoryConfig
from skill_hub.utils.path_utils import ensure_directory, expand_home

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and saving."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize config manager.

        Args:
            config_path: Path to config file (default: ~/.skills/.skill-hub/config.json)
        """
        if config_path is None:
            config_path = expand_home("~/.skills/.skill-hub/config.json")
        self.config_path = config_path

    def load(self) -> Config:
        """
        Load configuration from file.

        Returns:
            Config object
        """
        if not self.config_path.exists():
            logger.debug(f"Config file not found: {self.config_path}, using defaults")
            return Config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse agents
            agents = {}
            for agent_name, agent_data in data.get("agents", {}).items():
                agents[agent_name] = AgentConfig(**agent_data)

            # Parse repositories
            repositories = []
            for repo_data in data.get("repositories", []):
                repositories.append(RepositoryConfig(**repo_data))

            # Create config
            config = Config(
                version=data.get("version", "1.0.0"),
                conflict_resolution=data.get("conflict_resolution", "newest"),
                agents=agents,
                repositories=repositories,
                sync=data.get("sync", {}),
            )

            logger.debug(f"Loaded config from {self.config_path}")
            return config

        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return Config()

    def save(self, config: Config) -> bool:
        """
        Save configuration to file.

        Args:
            config: Config object to save

        Returns:
            True if successful
        """
        ensure_directory(self.config_path.parent)

        try:
            # Convert to dict
            data = {
                "version": config.version,
                "conflict_resolution": config.conflict_resolution,
                "agents": {
                    name: {"enabled": agent.enabled, "global_path": agent.global_path}
                    for name, agent in config.agents.items()
                },
                "repositories": [
                    {
                        "url": repo.url,
                        "enabled": repo.enabled,
                        "branch": repo.branch,
                        "path": repo.path,
                        "sync_schedule": repo.sync_schedule,
                    }
                    for repo in config.repositories
                ],
                "sync": config.sync,
            }

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved config to {self.config_path}")
            return True

        except OSError as e:
            logger.error(f"Failed to save config: {e}")
            return False
