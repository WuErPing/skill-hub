"""Synchronization engine implementation."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, Skill, SkillHubMetadata
from skill_hub.utils import compute_checksum, ensure_directory, expand_home

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    operation: str  # pull, push, bi-directional
    skills_synced: int = 0
    skills_skipped: int = 0
    conflicts_detected: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class SyncEngine:
    """Engine for synchronizing skills between hub and agents."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize sync engine.

        Args:
            config: Application configuration
        """
        self.config = config or Config()
        self.adapter_registry = AdapterRegistry(config)
        self.hub_path = expand_home("~/.skills")
        self.metadata_path = self.hub_path / ".skill-hub"

    def initialize_hub(self) -> None:
        """Initialize skill hub directory structure."""
        ensure_directory(self.hub_path)
        ensure_directory(self.metadata_path)
        logger.info(f"Initialized skill hub at {self.hub_path}")

    def pull_from_agents(self) -> SyncResult:
        """
        Pull skills from all agents to hub.

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(operation="pull")
        self.initialize_hub()

        # Discover skills from all enabled adapters
        discovery = DiscoveryEngine()
        search_paths = []

        for adapter in self.adapter_registry.get_enabled_adapters():
            for path in adapter.get_all_search_paths():
                search_paths.append((path, adapter.name))

        registry = discovery.discover_skills(search_paths)

        # Sync each discovered skill to hub
        for skill_name in registry.list_skills():
            skill = registry.get_skill(skill_name)
            if skill:
                try:
                    if self._sync_skill_to_hub(skill):
                        result.skills_synced += 1
                    else:
                        result.skills_skipped += 1
                except Exception as e:
                    error_msg = f"Error syncing skill '{skill_name}': {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        # Check for conflicts
        if registry.has_duplicates():
            result.conflicts_detected = len(registry.duplicates)

        return result

    def push_to_agents(self) -> SyncResult:
        """
        Push skills from hub to all agents.

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(operation="push")

        # Read all skills from hub
        skills_dir = self.hub_path / "skills"
        if not skills_dir.exists():
            logger.warning(f"Skills directory not found: {skills_dir}")
            return result

        # Push to each enabled adapter
        for adapter in self.adapter_registry.get_enabled_adapters():
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue

                try:
                    content = skill_file.read_text(encoding="utf-8")
                    if adapter.write_skill(skill_dir.name, content):
                        result.skills_synced += 1
                    else:
                        result.skills_skipped += 1
                except Exception as e:
                    error_msg = f"Error pushing skill '{skill_dir.name}' to {adapter.name}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        return result

    def sync(self) -> SyncResult:
        """
        Bi-directional sync: pull then push.

        Returns:
            Combined SyncResult
        """
        pull_result = self.pull_from_agents()
        push_result = self.push_to_agents()

        # Combine results
        result = SyncResult(
            operation="bi-directional",
            skills_synced=pull_result.skills_synced + push_result.skills_synced,
            skills_skipped=pull_result.skills_skipped + push_result.skills_skipped,
            conflicts_detected=pull_result.conflicts_detected,
            errors=pull_result.errors + push_result.errors,
        )

        return result

    def _sync_skill_to_hub(self, skill: Skill) -> bool:
        """
        Sync a single skill to the hub.

        Args:
            skill: Skill to sync

        Returns:
            True if synced, False if skipped
        """
        skill_dir = self.hub_path / skill.name
        skill_file = skill_dir / "SKILL.md"
        metadata_file = self.metadata_path / f"{skill.name}.json"

        # Check if skill already exists and unchanged
        if self.config.sync.get("incremental", True) and skill_file.exists():
            existing_content = skill_file.read_text(encoding="utf-8")
            existing_checksum = compute_checksum(existing_content)
            if existing_checksum == skill.checksum:
                logger.debug(f"Skipping unchanged skill: {skill.name}")
                return False

        # Write skill to hub
        ensure_directory(skill_dir)
        skill_file.write_text(skill.content, encoding="utf-8")

        # Write metadata
        metadata = SkillHubMetadata(
            name=skill.name,
            description=skill.metadata.description,
            sources=[
                {
                    "path": str(src.path),
                    "agent": src.agent,
                    "discovered_at": src.discovered_at.isoformat(),
                }
                for src in skill.sources
            ],
            checksum=skill.checksum or "",
            last_sync_at=datetime.now().isoformat(),
        )

        metadata_file.write_text(
            json.dumps(metadata.__dict__, indent=2), encoding="utf-8"
        )

        logger.info(f"Synced skill '{skill.name}' to hub")
        return True

    def list_hub_skills(self) -> List[str]:
        """
        List all skills in the hub.

        Returns:
            List of skill names
        """
        skills_dir = self.hub_path / "skills"
        if not skills_dir.exists():
            return []

        skills = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skills.append(skill_dir.name)

        return sorted(skills)
