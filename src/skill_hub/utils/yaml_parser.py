"""YAML frontmatter parser for SKILL.md files."""

import re
from typing import Optional, Tuple

import yaml

from skill_hub.models import SkillMetadata
from skill_hub.utils import validate_description, validate_skill_name


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

    # Validate name and description
    if not validate_skill_name(name):
        raise SkillParseError(
            f"Invalid skill name '{name}': must be lowercase alphanumeric "
            "with single hyphens, 1-64 chars"
        )

    if not validate_description(description):
        raise SkillParseError(
            f"Invalid description: must be 1-1024 characters, got {len(description)}"
        )

    # Extract optional fields
    license_field = frontmatter.get("license")
    compatibility = frontmatter.get("compatibility")
    metadata = frontmatter.get("metadata")

    # Validate metadata is dict if present
    if metadata is not None and not isinstance(metadata, dict):
        raise SkillParseError("metadata field must be a dictionary")

    # Convert metadata values to strings if present
    if metadata:
        metadata = {k: str(v) for k, v in metadata.items()}

    skill_metadata = SkillMetadata(
        name=name,
        description=description,
        license=license_field,
        compatibility=compatibility,
        metadata=metadata,
    )

    return skill_metadata, body


def parse_skill_file_from_path(path) -> Optional[Tuple[SkillMetadata, str]]:
    """
    Parse SKILL.md file from filesystem path.

    Args:
        path: Path to SKILL.md file

    Returns:
        Tuple of (SkillMetadata, content) or None if parsing fails

    Note:
        Returns None instead of raising to allow graceful handling
        during batch discovery operations.
    """
    try:
        content = path.read_text(encoding="utf-8")
        return parse_skill_file(content)
    except (OSError, SkillParseError):
        return None
