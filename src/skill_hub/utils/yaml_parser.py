"""YAML frontmatter parser for SKILL.md files."""

import re
from typing import Tuple

import yaml

from skill_hub.models import SkillMetadata


class SkillParseError(Exception):
    """Error parsing skill file."""

    pass


def parse_skill_file(content: str) -> Tuple[SkillMetadata, str]:
    """
    Parse SKILL.md file into metadata and content.

    Args:
        content: Full content of SKILL.md file

    Returns:
        Tuple of (SkillMetadata, remaining_content)

    Raises:
        SkillParseError: If frontmatter is missing or invalid
    """
    # Match YAML frontmatter between --- delimiters
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise SkillParseError("Missing or invalid YAML frontmatter")

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise SkillParseError(f"Invalid YAML: {e}") from e

    if not isinstance(frontmatter, dict):
        raise SkillParseError("Frontmatter must be a YAML dictionary")

    # Extract required fields
    name = frontmatter.get("name")
    description = frontmatter.get("description")

    if not name:
        raise SkillParseError("Missing required field: name")
    if not description:
        raise SkillParseError("Missing required field: description")

    if not isinstance(name, str) or not isinstance(description, str):
        raise SkillParseError("name and description must be strings")

    # Extract optional fields
    license_field = frontmatter.get("license")
    compatibility = frontmatter.get("compatibility")
    metadata = frontmatter.get("metadata")

    # Validate metadata is dict if present
    if metadata is not None and not isinstance(metadata, dict):
        raise SkillParseError("metadata field must be a dictionary")

    skill_metadata = SkillMetadata(
        name=name,
        description=description,
        license=license_field,
        compatibility=compatibility,
        metadata=metadata,
    )

    return skill_metadata, body
