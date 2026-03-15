"""Tests for skill-hub utilities."""

from pathlib import Path

import pytest

from skill_hub.utils.path_utils import expand_home
from skill_hub.utils.yaml_parser import SkillParseError, parse_skill_file, parse_skill_file_from_path


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
        """Test parsing skill file with YAML frontmatter."""
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
        """Test parsing skill file without frontmatter raises error."""
        with pytest.raises(SkillParseError, match="Missing or invalid"):
            parse_skill_file("# Test Skill\n\nContent here.")

    def test_parse_empty_content_raises_error(self):
        """Test parsing empty content raises error."""
        with pytest.raises(SkillParseError):
            parse_skill_file("")

    def test_parse_malformed_frontmatter_raises_error(self):
        """Test parsing with malformed frontmatter raises error."""
        content = "---\nname: test-skill\ndescription: Missing closing ---\n# Test Skill\n"
        with pytest.raises(SkillParseError):
            parse_skill_file(content)

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
  updateUrl: https://example.com/update
---

# Versioned Skill
"""
        metadata, body = parse_skill_file(content)
        assert metadata.metadata == {"version": "1.2.3", "updateUrl": "https://example.com/update"}
        assert metadata.version == "1.2.3"
        assert metadata.updateUrl == "https://example.com/update"

    def test_parse_invalid_yaml_raises_error(self):
        content = "---\n: : : invalid yaml\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="Invalid YAML"):
            parse_skill_file(content)

    def test_parse_non_dict_frontmatter_raises_error(self):
        content = "---\n- list item\n- another\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="dictionary"):
            parse_skill_file(content)

    def test_parse_non_string_name_raises_error(self):
        content = "---\nname: 123\ndescription: test\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="strings"):
            parse_skill_file(content)

    def test_parse_metadata_non_dict_raises_error(self):
        content = "---\nname: test\ndescription: test\nmetadata: not-a-dict\n---\n\nContent\n"
        with pytest.raises(SkillParseError, match="metadata.*dictionary"):
            parse_skill_file(content)

    def test_parse_body_is_stripped(self):
        content = "---\nname: test\ndescription: test\n---\n\nBody content\n"
        _, body = parse_skill_file(content)
        assert "Body content" in body


class TestParseSkillFileFromPath:
    """Tests for parse_skill_file_from_path function."""

    def test_parse_from_existing_file(self, tmp_path):
        """Test parsing from an existing file."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n")

        result = parse_skill_file_from_path(skill_file)

        assert result is not None
        metadata, body = result
        assert metadata.name == "test-skill"

    def test_parse_from_nonexistent_file(self, tmp_path):
        """Test parsing from a non-existent file."""
        result = parse_skill_file_from_path(tmp_path / "nonexistent.md")
        assert result is None

    def test_parse_from_invalid_file(self, tmp_path):
        """Test parsing from a file with invalid content returns None."""
        skill_file = tmp_path / "BAD.md"
        skill_file.write_text("No frontmatter here")

        result = parse_skill_file_from_path(skill_file)
        assert result is None
