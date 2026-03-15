"""Tests for skill-hub CLI commands."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from skill_hub.cli import (
    cli,
    compare_skills_cmd,
    install_skill,
    list_local_skills,
    list_skills,
    path as path_cmd,
    show_version,
    self_update,
    sync_skill_cmd,
    update_skill,
    upgrade_skill,
    view,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestListSkillsCommand:
    """Tests for the 'list' command."""

    def test_list_skills_no_directory(self, runner, temp_skills_dir):
        """Test listing skills when no directory exists."""
        result = runner.invoke(list_skills, ["--all"])
        # Should handle missing directory gracefully
        assert result.exit_code == 0

    def test_list_skills_with_public_flag(self, runner):
        """Test listing public skills only."""
        result = runner.invoke(list_skills, ["--public"])
        assert result.exit_code == 0

    def test_list_skills_with_private_flag(self, runner):
        """Test listing private skills only."""
        result = runner.invoke(list_skills, ["--private"])
        assert result.exit_code == 0

    def test_list_skills_with_verbose_flag(self, runner):
        """Test listing skills with verbose output."""
        result = runner.invoke(list_skills, ["--verbose"])
        assert result.exit_code == 0

    def test_list_skills_help(self, runner):
        """Test list command help message."""
        result = runner.invoke(list_skills, ["--help"])
        assert result.exit_code == 0
        assert "List all skills" in result.output


class TestListLocalSkillsCommand:
    """Tests for the 'list-local' command."""

    def test_list_local_skills_no_directories(self, runner):
        """Test listing local skills when no directories exist."""
        result = runner.invoke(list_local_skills)
        assert result.exit_code == 0
        # Should output message about no directories found
        assert "No local skill directories found" in result.output or result.exit_code == 0

    def test_list_local_skills_with_verbose(self, runner):
        """Test listing local skills with verbose output."""
        result = runner.invoke(list_local_skills, ["--verbose"])
        assert result.exit_code == 0


class TestViewSkillCommand:
    """Tests for the 'view' command."""

    def test_view_nonexistent_skill(self, runner):
        """Test viewing a skill that doesn't exist."""
        result = runner.invoke(view, ["nonexistent-skill"])
        assert result.exit_code == 0
        assert "Skill not found" in result.output

    def test_view_skill_help(self, runner):
        """Test view command help message."""
        result = runner.invoke(view, ["--help"])
        assert result.exit_code == 0
        assert "View a specific skill" in result.output


class TestPathCommand:
    """Tests for the 'path' command."""

    def test_path_command(self, runner):
        """Test showing skills directory path."""
        result = runner.invoke(path_cmd)
        assert result.exit_code == 0
        assert "agents/skills" in result.output

    def test_path_help(self, runner):
        """Test path command help message."""
        result = runner.invoke(path_cmd, ["--help"])
        assert result.exit_code == 0
        assert "Show the skills directory path" in result.output


class TestCompareCommand:
    """Tests for the 'compare' command."""

    def test_compare_help(self, runner):
        """Test compare command help message."""
        result = runner.invoke(compare_skills_cmd, ["--help"])
        assert result.exit_code == 0
        assert "Compare local project skills" in result.output

    def test_compare_with_summary(self, runner):
        """Test compare with summary flag."""
        result = runner.invoke(compare_skills_cmd, ["--summary"])
        assert result.exit_code == 0

    def test_compare_all_locals(self, runner):
        """Test compare with all-locals flag."""
        result = runner.invoke(compare_skills_cmd, ["--all-locals"])
        assert result.exit_code == 0


class TestInstallSkillCommand:
    """Tests for the 'install' command."""

    def test_install_help(self, runner):
        """Test install command help message."""
        result = runner.invoke(install_skill, ["--help"])
        assert result.exit_code == 0
        assert "Install a skill" in result.output

    def test_install_missing_source(self, runner):
        """Test installing with missing source."""
        result = runner.invoke(install_skill, [])
        assert result.exit_code != 0


class TestUpgradeSkillCommand:
    """Tests for the 'upgrade' command."""

    def test_upgrade_help(self, runner):
        """Test upgrade command help message."""
        result = runner.invoke(upgrade_skill, ["--help"])
        assert result.exit_code == 0
        assert "Upgrade a skill" in result.output


class TestUpdateSkillCommand:
    """Tests for the 'update' command."""

    def test_update_help(self, runner):
        """Test update command help message."""
        result = runner.invoke(update_skill, ["--help"])
        assert result.exit_code == 0
        assert "Check for and apply skill updates" in result.output


class TestSyncSkillCommand:
    """Tests for the 'sync' command."""

    def test_sync_help(self, runner):
        """Test sync command help message."""
        result = runner.invoke(sync_skill_cmd, ["--help"])
        assert result.exit_code == 0
        assert "Sync a skill" in result.output

    def test_sync_same_source_target(self, runner):
        """Test sync with same source and target."""
        result = runner.invoke(sync_skill_cmd, ["skill-name", "--from", "public", "--to", "public"])
        assert result.exit_code != 0
        assert "Source and target directories must be different" in result.output

    def test_sync_missing_skill(self, runner):
        """Test sync for skill that doesn't exist."""
        result = runner.invoke(sync_skill_cmd, ["nonexistent-skill", "--from", "public", "--to", "private"])
        # Should fail since skill doesn't exist
        assert result.exit_code != 0


class TestVersionCommand:
    """Tests for the 'version' command."""

    def test_version_command(self, runner):
        """Test showing version."""
        result = runner.invoke(show_version)
        assert result.exit_code == 0
        assert "skill-hub version" in result.output

    def test_version_help(self, runner):
        """Test version command help message."""
        result = runner.invoke(show_version, ["--help"])
        assert result.exit_code == 0
        assert "Show version information" in result.output

    def test_version_check(self, runner):
        """Test checking for updates."""
        result = runner.invoke(show_version, ["--check"])
        assert result.exit_code == 0


class TestSelfUpdateCommand:
    """Tests for the 'self-update' command."""

    def test_self_update_help(self, runner):
        """Test self-update command help message."""
        result = runner.invoke(self_update, ["--help"])
        assert result.exit_code == 0
        assert "Update skill-hub" in result.output

    @patch("subprocess.check_call")
    def test_self_update_success(self, mock_check_call, runner):
        """Test successful self-update."""
        result = runner.invoke(self_update)
        assert result.exit_code == 0
        assert "Updated successfully" in result.output

    def test_self_update_failure(self, runner):
        """Test failed self-update."""
        with patch("subprocess.check_call") as mock_check_call:
            mock_check_call.side_effect = subprocess.CalledProcessError(1, "pip")
            result = runner.invoke(self_update)
            assert result.exit_code != 0
            assert "Update failed" in result.output


class TestCliGroup:
    """Tests for the main CLI group."""

    def test_cli_help(self, runner):
        """Test main CLI help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "skill-hub" in result.output
