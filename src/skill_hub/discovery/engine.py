"""Skill discovery engine implementation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from skill_hub.models import Skill, SkillMetadata, SkillSource
from skill_hub.utils import compute_checksum, parse_skill_file_from_path

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry of discovered skills."""

    def __init__(self) -> None:
        """Initialize empty skill registry."""
        self.skills: Dict[str, Skill] = {}
        self.duplicates: Dict[str, List[SkillSource]] = {}

    def add_skill(
        self, metadata: SkillMetadata, content: str, source: SkillSource
    ) -> None:
        """
        Add a skill to the registry.

        Args:
            metadata: Skill metadata from frontmatter
            content: Full skill content
            source: Source location information
        """
        name = metadata.name
        checksum = compute_checksum(content)

        if name in self.skills:
            # Skill already exists, add as duplicate source
            existing = self.skills[name]
            existing.sources.append(source)

            # Track duplicates if checksums differ
            if existing.checksum != checksum:
                if name not in self.duplicates:
                    self.duplicates[name] = existing.sources
                else:
                    self.duplicates[name].append(source)

                logger.warning(
                    f"Duplicate skill '{name}' with different content from {source.path}"
                )
        else:
            # New skill
            skill = Skill(
                metadata=metadata,
                content=content,
                sources=[source],
                checksum=checksum,
            )
            self.skills[name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[str]:
        """List all skill names."""
        return list(self.skills.keys())

    def has_duplicates(self) -> bool:
        """Check if any duplicates exist."""
        return len(self.duplicates) > 0

    def export_json(self) -> List[Dict]:
        """Export registry as JSON-serializable list."""
        result = []
        for skill in self.skills.values():
            result.append(
                {
                    "name": skill.name,
                    "description": skill.metadata.description,
                    "sources": [
                        {
                            "path": str(src.path),
                            "agent": src.agent,
                            "discovered_at": src.discovered_at.isoformat(),
                        }
                        for src in skill.sources
                    ],
                    "checksum": skill.checksum,
                }
            )
        return result


class DiscoveryEngine:
    """Engine for discovering skills from agent configurations."""

    def __init__(self) -> None:
        """Initialize discovery engine."""
        self.registry = SkillRegistry()

    def discover_skills(self, search_paths: List[tuple[Path, str]]) -> SkillRegistry:
        """
        Discover skills from multiple search paths.

        Args:
            search_paths: List of (path, agent_name) tuples to search

        Returns:
            SkillRegistry containing all discovered skills
        """
        for base_path, agent in search_paths:
            if not base_path.exists():
                logger.debug(f"Path does not exist: {base_path}")
                continue

            self._scan_directory(base_path, agent)

        return self.registry

    def _scan_directory(self, base_path: Path, agent: str) -> None:
        """
        Recursively scan directory for SKILL.md files.

        Args:
            base_path: Base directory to scan
            agent: Agent name (cursor, claude, qoder, opencode)
        """
        # Look for skills/**/SKILL.md pattern
        skills_dir = base_path / "skills"
        if not skills_dir.exists():
            logger.debug(f"Skills directory not found: {skills_dir}")
            return

        for skill_file in skills_dir.rglob("SKILL.md"):
            self._process_skill_file(skill_file, agent)

    def _process_skill_file(self, skill_path: Path, agent: str) -> None:
        """
        Process a single SKILL.md file.

        Args:
            skill_path: Path to SKILL.md file
            agent: Agent name
        """
        logger.debug(f"Processing {skill_path}")

        result = parse_skill_file_from_path(skill_path)
        if result is None:
            logger.warning(f"Failed to parse skill file: {skill_path}")
            return

        metadata, body = result
        full_content = skill_path.read_text(encoding="utf-8")

        # Verify directory name matches skill name
        skill_dir_name = skill_path.parent.name
        if skill_dir_name != metadata.name:
            logger.warning(
                f"Directory name '{skill_dir_name}' does not match "
                f"skill name '{metadata.name}' in {skill_path}"
            )

        source = SkillSource(
            path=skill_path,
            agent=agent,
            discovered_at=datetime.now(),
        )

        self.registry.add_skill(metadata, full_content, source)
        logger.info(f"Discovered skill '{metadata.name}' from {agent} at {skill_path}")
