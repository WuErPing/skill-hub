"""Tests for skill-hub data models."""

import tempfile
from pathlib import Path

import pytest

from skill_hub.models import Skill, SkillMetadata


@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSkillMetadata:
    """Tests for SkillMetadata class."""

    def test_metadata_with_version(self):
        """Test extracting version from metadata."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
            metadata={"version": "1.2.3"}
        )

        assert metadata.version == "1.2.3"

    def test_metadata_without_version(self):
        """Test version property when no version exists."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
            metadata=None
        )

        assert metadata.version is None

    def test_metadata_with_update_url(self):
        """Test extracting updateUrl from metadata."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
            metadata={"updateUrl": "https://example.com/update"}
        )

        assert metadata.updateUrl == "https://example.com/update"

    def test_metadata_without_update_url(self):
        """Test updateUrl property when not present."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
            metadata={}
        )

        assert metadata.updateUrl is None


class TestSkill:
    """Tests for Skill class."""

    def test_skill_properties(self, temp_base_dir):
        """Test basic skill properties."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill"
        )
        skill_path = temp_base_dir / "test-skill" / "SKILL.md"
        skill = Skill(
            metadata=metadata,
            content="# Test Content",
            path=skill_path
        )

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"

    def test_skill_source_directory(self, temp_base_dir):
        """Test skill with source directory tracking."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill"
        )
        skill_path = temp_base_dir / "test-skill" / "SKILL.md"
        skill = Skill(
            metadata=metadata,
            content="# Test Content",
            path=skill_path,
            source_directory="project"
        )

        assert skill.source_directory == "project"

    def test_skill_content(self, temp_base_dir):
        """Test skill content."""
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill"
        )
        content = "# Test Skill\n\nThis is the content."
        skill_path = temp_base_dir / "test-skill" / "SKILL.md"
        skill = Skill(
            metadata=metadata,
            content=content,
            path=skill_path
        )

        assert skill.content == content
