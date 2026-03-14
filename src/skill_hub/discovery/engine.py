"""Skill discovery engine for ~/.agents/skills."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from skill_hub.models import Skill, SkillMetadata
from skill_hub.utils import parse_skill_file_from_path

logger = logging.getLogger(__name__)


def discover_local_skills_dirs(base_path: Optional[Path] = None) -> List[Tuple[Path, str]]:
    """Discover all local skill directories matching .*/skills pattern.
    
    Args:
        base_path: Base directory to search (default: current working directory)
        
    Returns:
        List of tuples (skills_directory_path, tool_name)
        where tool_name is the name of the tool (e.g., 'opencode', 'agents')
    """
    if base_path is None:
        base_path = Path.cwd()
    
    skill_dirs: List[Tuple[Path, str]] = []
    
    # Look for hidden directories that contain a 'skills' subdirectory
    for item in base_path.iterdir():
        if item.is_dir() and item.name.startswith("."):
            skills_dir = item / "skills"
            if skills_dir.exists() and skills_dir.is_dir():
                # Extract tool name from directory name (e.g., '.opencode' -> 'opencode')
                tool_name = item.name[1:]  # Remove leading dot
                skill_dirs.append((skills_dir, tool_name))
    
    return skill_dirs


def discover_all_local_skills(base_path: Optional[Path] = None) -> Dict[str, List[Skill]]:
    """Discover all skills from all local skill directories.
    
    Args:
        base_path: Base directory to search (default: current working directory)
        
    Returns:
        Dictionary mapping tool_name to list of skills
    """
    if base_path is None:
        base_path = Path.cwd()
    
    result: Dict[str, List[Skill]] = {}
    skill_dirs = discover_local_skills_dirs(base_path)
    
    for skills_dir, tool_name in skill_dirs:
        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()
        if skills:
            result[tool_name] = skills
    
    return result


class DiscoveryEngine:
    """Engine for discovering skills from ~/.agents/skills."""

    def __init__(self, skills_path: Path) -> None:
        """
        Initialize discovery engine.

        Args:
            skills_path: Path to the skills directory (~/.agents/skills)
        """
        self.skills_path = skills_path
        self.skills: List[Skill] = []

    def discover_skills(self) -> List[Skill]:
        """
        Discover skills from the skills directory.

        Returns:
            List of discovered Skill objects
        """
        if not self.skills_path.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_path}")
            return []

        self._scan_directory(self.skills_path)
        return self.skills

    def discover_skills_with_updates(self) -> List[Skill]:
        """
        Discover skills and check for updates.
        
        Returns:
            List of Skill objects with update status
        """
        skills = self.discover_skills()
        
        for skill in skills:
            # Add update check metadata
            skill_path = skill.path.parent
            skill_md = skill.path
            
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()
                
                import re
                match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
                if match:
                    frontmatter = match.group(1)
                    
                    # Extract version
                    version_match = re.search(r"version:\s*([^\n]+)", frontmatter)
                    skill._update_status = {
                        "current_version": version_match.group(1).strip() if version_match else None,
                    }
            except Exception:
                skill._update_status = {"current_version": None}
        
        return skills

    def _scan_directory(self, base_path: Path) -> None:
        """
        Recursively scan directory for SKILL.md files.

        Args:
            base_path: Base directory to scan
        """
        for skill_file in base_path.rglob("SKILL.md"):
            self._process_skill_file(skill_file)

    def _process_skill_file(self, skill_path: Path) -> None:
        """
        Process a single SKILL.md file.

        Args:
            skill_path: Path to SKILL.md file
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

        skill = Skill(
            metadata=metadata,
            content=full_content,
            path=skill_path,
        )

        self.skills.append(skill)
        logger.info(f"Discovered skill '{metadata.name}' at {skill_path}")
