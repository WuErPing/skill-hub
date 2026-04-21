"""Tests for skill-hub data models."""

from skill_hub.models import SkillMetadata


class TestSkillMetadata:
    """Tests for SkillMetadata class."""

    def test_basic_metadata(self):
        metadata = SkillMetadata(
            name="test-skill",
            description="A test skill",
        )
        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill"
        assert metadata.license is None
        assert metadata.compatibility is None
        assert metadata.metadata is None

    def test_full_metadata(self):
        metadata = SkillMetadata(
            name="full-skill",
            description="A complete skill",
            license="MIT",
            compatibility="claude, opencode",
            metadata={"version": "1.2.3"},
        )
        assert metadata.license == "MIT"
        assert metadata.compatibility == "claude, opencode"
        assert metadata.metadata == {"version": "1.2.3"}
