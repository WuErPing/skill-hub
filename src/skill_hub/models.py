"""Data models for skill-hub."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillMetadata:
    """Metadata for a skill from YAML frontmatter."""

    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[dict] = None

    @property
    def version(self) -> Optional[str]:
        """Get skill version from metadata."""
        if self.metadata is None:
            return None
        return self.metadata.get("version")

    @property
    def updateUrl(self) -> Optional[str]:
        """Get skill update URL from metadata."""
        if self.metadata is None:
            return None
        return self.metadata.get("updateUrl")


@dataclass
class Skill:
    """Complete skill with metadata and content."""

    metadata: SkillMetadata
    content: str
    path: Path
    source_directory: Optional[str] = None  # Track which directory this skill came from

    @property
    def name(self) -> str:
        """Get skill name from metadata."""
        return self.metadata.name

    @property
    def description(self) -> str:
        """Get skill description from metadata."""
        return self.metadata.description
