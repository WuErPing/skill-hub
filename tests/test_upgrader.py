"""Tests for skill-hub upgrader module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.upgrader import (
    UpgradeError,
    backup_skill,
    convert_claude_to_agent,
    detect_config_format,
    upgrade_skill,
)
from skill_hub.models import Skill, SkillMetadata


def _make_skill(base: Path, name: str, content: str = None) -> Skill:
    """Helper to create a Skill object backed by a real file."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    if content is None:
        content = f"---\nname: {name}\ndescription: A test skill\n---\n\n# {name}\n\nContent.\n"
    (skill_dir / "SKILL.md").write_text(content)
    metadata = SkillMetadata(name=name, description="A test skill")
    return Skill(metadata=metadata, content=content, path=skill_dir / "SKILL.md")


class TestDetectConfigFormat:
    """Tests for detect_config_format function."""

    def test_claude_config_file(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        assert detect_config_format(tmp_path) == "claude"

    def test_opencode_config_file(self, tmp_path):
        (tmp_path / ".opencode").mkdir()
        assert detect_config_format(tmp_path) == "opencode"

    def test_cursor_config_file(self, tmp_path):
        (tmp_path / ".cursor").mkdir()
        assert detect_config_format(tmp_path) == "cursor"

    def test_claude_parent_path(self, tmp_path):
        skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        assert detect_config_format(skill_dir) == "claude"

    def test_opencode_parent_path(self, tmp_path):
        skill_dir = tmp_path / ".opencode" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        assert detect_config_format(skill_dir) == "opencode"

    def test_default_agents(self, tmp_path):
        assert detect_config_format(tmp_path) == "agents"


class TestBackupSkill:
    """Tests for backup_skill function."""

    def test_creates_backup(self, tmp_path):
        with patch("skill_hub.upgrader.Path.home", return_value=tmp_path):
            skills_dir = tmp_path / ".agents" / "skills"
            skill = _make_skill(skills_dir, "backup-test")

            backup_path = backup_skill(skill)

            assert backup_path.exists()
            assert "backup-test-backup-" in backup_path.name
            assert (backup_path / "SKILL.md").exists()


class TestUpgradeSkill:
    """Tests for upgrade_skill function."""

    def test_skill_not_found(self, tmp_path):
        with patch("skill_hub.upgrader.Path.cwd", return_value=tmp_path), \
             patch("skill_hub.upgrader.Path.home", return_value=tmp_path):
            (tmp_path / ".agents" / "skills").mkdir(parents=True)
            with pytest.raises(UpgradeError, match="Skill not found"):
                upgrade_skill("nonexistent", dest_dir=tmp_path / "dest")

    def test_upgrade_from_local(self, tmp_path):
        local_skills = tmp_path / ".agents" / "skills"
        skill = _make_skill(local_skills, "local-skill")
        dest_dir = tmp_path / "dest"

        with patch("skill_hub.upgrader.Path.cwd", return_value=tmp_path), \
             patch("skill_hub.upgrader.Path.home", return_value=tmp_path):
            result = upgrade_skill("local-skill", dest_dir=dest_dir)

        assert result is not None
        assert result.name == "local-skill"

    def test_upgrade_agents_format_noop(self, tmp_path):
        """Skills already in agents format should be returned as-is."""
        local_skills = tmp_path / ".agents" / "skills"
        skill = _make_skill(local_skills, "agents-skill")
        dest_dir = tmp_path / "dest"

        with patch("skill_hub.upgrader.Path.cwd", return_value=tmp_path), \
             patch("skill_hub.upgrader.Path.home", return_value=tmp_path):
            result = upgrade_skill("agents-skill", dest_dir=dest_dir)

        assert result.name == "agents-skill"


class TestConvertClaudeToAgent:
    """Tests for convert_claude_to_agent function."""

    def test_basic_conversion(self, tmp_path):
        source_dir = tmp_path / ".claude" / "skills"
        skill = _make_skill(source_dir, "claude-skill")
        dest_path = tmp_path / "dest" / "claude-skill"

        result = convert_claude_to_agent(skill, dest_path)

        assert result is not None
        assert (dest_path / "SKILL.md").exists()
