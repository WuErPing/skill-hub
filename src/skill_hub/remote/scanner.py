"""Skill scanner for remote repositories."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from skill_hub.models import RepositoryConfig, Skill, SkillMetadata, SkillSource
from skill_hub.utils import compute_checksum, parse_skill_file_from_path

logger = logging.getLogger(__name__)


class RepositorySkillScanner:
    """Scans remote repositories for skills."""

    def scan_repository(
        self, repo_dir: Path, config: RepositoryConfig
    ) -> List[tuple[SkillMetadata, str, Path]]:
        """
        Scan repository directory for skills.

        Args:
            repo_dir: Path to cloned repository
            config: Repository configuration

        Returns:
            List of (metadata, content, skill_file_path) tuples
        """
        skills = []

        # Determine search path
        if config.path:
            search_dir = repo_dir / config.path.lstrip("/")
        else:
            # Look for skills directory in root
            skills_dir = repo_dir / "skills"
            if skills_dir.exists():
                search_dir = skills_dir
            else:
                # Scan entire repo
                search_dir = repo_dir

        if not search_dir.exists():
            logger.warning(f"Search directory does not exist: {search_dir}")
            return skills

        # Find all SKILL.md files
        for skill_file in search_dir.rglob("SKILL.md"):
            # Skip .git directory
            if ".git" in skill_file.parts:
                continue

            result = parse_skill_file_from_path(skill_file)
            if result is None:
                logger.warning(f"Failed to parse skill file: {skill_file}")
                continue

            metadata, body = result

            # Read full content
            try:
                content = skill_file.read_text(encoding="utf-8")
                skills.append((metadata, content, skill_file))
                logger.debug(f"Found skill '{metadata.name}' in {skill_file}")
            except OSError as e:
                logger.error(f"Failed to read skill file {skill_file}: {e}")

        logger.info(f"Found {len(skills)} skills in {config.url}")
        return skills

    def create_skill_objects(
        self, scanned_skills: List[tuple[SkillMetadata, str, Path]], repo_url: str
    ) -> List[Skill]:
        """
        Convert scanned skills to Skill objects with remote source tracking.

        Args:
            scanned_skills: List of (metadata, content, path) tuples
            repo_url: Repository URL for source tracking

        Returns:
            List of Skill objects
        """
        skills = []

        for metadata, content, skill_path in scanned_skills:
            # Create source with remote type
            source = SkillSource(
                path=skill_path,
                agent="remote",  # Mark as remote source
                discovered_at=datetime.now(),
            )

            skill = Skill(
                metadata=metadata,
                content=content,
                sources=[source],
                checksum=compute_checksum(content),
            )

            skills.append(skill)

        return skills
