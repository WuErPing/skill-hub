"""Data models for skill-hub."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillMetadata:
    """Metadata for a skill from YAML frontmatter."""

    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[dict] = None
