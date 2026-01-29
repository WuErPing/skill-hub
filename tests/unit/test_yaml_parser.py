"""Tests for YAML parser."""

import pytest

from skill_hub.utils import SkillParseError, parse_skill_file


class TestSkillParser:
    """Tests for skill file parsing."""

    def test_parse_valid_skill(self) -> None:
        """Test parsing valid skill file."""
        content = """---
name: test-skill
description: A test skill
license: MIT
---

## What I do
Test content
"""
        metadata, body = parse_skill_file(content)
        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill"
        assert metadata.license == "MIT"
        assert "Test content" in body

    def test_parse_minimal_skill(self) -> None:
        """Test parsing skill with only required fields."""
        content = """---
name: minimal
description: Minimal skill
---

Content here
"""
        metadata, body = parse_skill_file(content)
        assert metadata.name == "minimal"
        assert metadata.description == "Minimal skill"
        assert metadata.license is None

    def test_missing_frontmatter(self) -> None:
        """Test error when frontmatter is missing."""
        content = "No frontmatter here"
        with pytest.raises(SkillParseError):
            parse_skill_file(content)

    def test_missing_name(self) -> None:
        """Test error when name field is missing."""
        content = """---
description: Missing name
---
Content
"""
        with pytest.raises(SkillParseError):
            parse_skill_file(content)

    def test_invalid_name(self) -> None:
        """Test error when name is invalid."""
        content = """---
name: Invalid_Name
description: Test
---
Content
"""
        with pytest.raises(SkillParseError):
            parse_skill_file(content)
