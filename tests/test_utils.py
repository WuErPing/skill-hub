"""Tests for skill-hub utilities."""

from pathlib import Path

import pytest

from skill_hub.utils.path_utils import expand_home
from skill_hub.utils.yaml_parser import SkillParseError, parse_skill_file


class TestExpandHome:
    """Tests for expand_home function."""

    def test_expand_tilde(self):
        result = expand_home("~/some/path")
        assert "~" not in str(result)
        assert str(result).startswith(str(Path.home()))

    def test_absolute_path_unchanged(self):
        result = expand_home("/usr/local/bin")
        assert str(result).endswith("usr/local/bin")

    def test_returns_resolved_path(self):
        result = expand_home("~/foo/../bar")
        assert ".." not in str(result)

    def test_returns_path_object(self):
        result = expand_home("~/test")
        assert isinstance(result, Path)


class TestParseSkillFile:
    """Tests for parse_skill_file function."""

    def test_parse_with_frontmatter(self):
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

Content here.
"""
        metadata, body = parse_skill_file(content)
        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill"
        assert "# Test Skill" in body

    def test_parse_without_frontmatter_raises_error(self):
        with pytest.raises(SkillParseError, match="Missing or invalid"):
            parse_skill_file("# Test Skill\n\nContent here.")

    def test_parse_empty_content_raises_error(self):
        with pytest.raises(SkillParseError):
            parse_skill_file("")

    def test_parse_missing_name_raises_error(self):
        content = "---\ndescription: No name field\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="name"):
            parse_skill_file(content)

    def test_parse_missing_description_raises_error(self):
        content = "---\nname: test-skill\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="description"):
            parse_skill_file(content)

    def test_parse_with_optional_fields(self):
        content = """---
name: full-skill
description: A complete skill
license: MIT
compatibility: claude, opencode
---

# Full Skill
"""
        metadata, body = parse_skill_file(content)
        assert metadata.license == "MIT"
        assert metadata.compatibility == "claude, opencode"

    def test_parse_with_metadata_dict(self):
        content = """---
name: versioned-skill
description: Has metadata
metadata:
  version: 1.2.3
---

# Versioned Skill
"""
        metadata, body = parse_skill_file(content)
        assert metadata.metadata == {"version": "1.2.3"}
