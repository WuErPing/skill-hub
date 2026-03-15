"""Tests for skill-hub installer module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.installer import (
    InstallationError,
    get_install_path,
    install_from_github,
    install_from_local,
    install_from_url,
    sync_skill,
)
from skill_hub.models import Skill, SkillMetadata


@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _make_source_skill(base: Path, name: str, desc: str = "A test skill") -> Path:
    """Create a source skill directory with a SKILL.md file."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nContent here.\n"
    )
    return skill_dir


class TestGetInstallPath:
    """Tests for get_install_path function."""

    def test_public_path(self):
        result = get_install_path("my-skill", target="public")
        assert result == Path.home() / ".agents" / "skills" / "my-skill"

    def test_project_path(self):
        result = get_install_path("my-skill", target="project")
        assert result == Path.cwd() / ".agents" / "skills" / "my-skill"

    def test_default_is_public(self):
        result = get_install_path("my-skill")
        assert result == Path.home() / ".agents" / "skills" / "my-skill"


class TestInstallFromLocal:
    """Tests for install_from_local function."""

    def test_install_from_existing_directory(self, tmp_path):
        """Test installing from an existing skill directory."""
        source_dir = _make_source_skill(tmp_path / "source", "test-skill")
        target_dir = tmp_path / "target"

        result = install_from_local(str(source_dir), None, target_dir)

        assert result is not None
        assert result.name == "test-skill"
        installed_path = target_dir / "test-skill" / "SKILL.md"
        assert installed_path.exists()

    def test_install_with_custom_name_uses_directory(self, tmp_path):
        """Test that custom name is used for the installation directory."""
        source_dir = _make_source_skill(tmp_path / "source", "original-name")
        target_dir = tmp_path / "target"

        result = install_from_local(str(source_dir), "custom-name", target_dir)

        assert result is not None
        # The metadata name comes from the SKILL.md file, not the custom name
        assert result.name == "original-name"
        # But the file is installed under the custom directory name
        assert (target_dir / "custom-name" / "SKILL.md").exists()

    def test_install_from_nonexistent_directory(self, tmp_path):
        """Test installing from a non-existent directory."""
        target_dir = tmp_path / "target"

        with pytest.raises(InstallationError, match="not found"):
            install_from_local("/nonexistent/path", None, target_dir)

    def test_install_from_file_not_directory(self, tmp_path):
        """Test installing from a file instead of a directory."""
        source_file = tmp_path / "not_a_dir.txt"
        source_file.write_text("hello")
        target_dir = tmp_path / "target"

        with pytest.raises(InstallationError, match="not a directory"):
            install_from_local(str(source_file), None, target_dir)

    def test_install_without_skill_md(self, tmp_path):
        """Test installing from directory without SKILL.md."""
        source_dir = tmp_path / "source" / "incomplete-skill"
        source_dir.mkdir(parents=True)
        target_dir = tmp_path / "target"

        with pytest.raises(InstallationError, match="SKILL.md not found"):
            install_from_local(str(source_dir), None, target_dir)

    def test_install_copies_extra_files(self, tmp_path):
        """Test that extra files are copied along with SKILL.md."""
        source_dir = _make_source_skill(tmp_path / "source", "full-skill")
        (source_dir / "README.md").write_text("# Readme")
        (source_dir / "config.yaml").write_text("key: value")
        target_dir = tmp_path / "target"

        install_from_local(str(source_dir), None, target_dir)

        assert (target_dir / "full-skill" / "SKILL.md").exists()
        assert (target_dir / "full-skill" / "README.md").exists()
        assert (target_dir / "full-skill" / "config.yaml").exists()

    def test_install_default_target(self, tmp_path, monkeypatch):
        """Test that default target is project-level .agents/skills."""
        source_dir = _make_source_skill(tmp_path / "source", "default-target")
        monkeypatch.chdir(tmp_path)

        result = install_from_local(str(source_dir), None, None)

        expected_path = Path.cwd() / ".agents" / "skills" / "default-target" / "SKILL.md"
        assert result.path == expected_path


class TestInstallFromUrl:
    """Tests for install_from_url function."""

    def test_install_from_url(self, tmp_path):
        """Test installing from a URL."""
        skill_content = "---\nname: url-skill\ndescription: Skill from URL\n---\n\n# URL Skill\n"
        target_dir = tmp_path / "target"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.text = skill_content

            result = install_from_url("https://example.com/SKILL.md", None, target_dir)

        assert result is not None
        assert result.name == "url-skill"
        assert (target_dir / "url-skill" / "SKILL.md").exists()

    def test_install_from_url_with_custom_name(self, tmp_path):
        """Test installing from URL with custom name."""
        skill_content = "---\nname: original-name\ndescription: Skill from URL\n---\n\n# Original Skill\n"
        target_dir = tmp_path / "target"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.text = skill_content

            result = install_from_url("https://example.com/SKILL.md", "custom-name", target_dir)

        assert result is not None
        # Metadata name stays as parsed from file
        assert result.name == "original-name"
        # But installed under custom directory
        assert (target_dir / "custom-name" / "SKILL.md").exists()

    def test_install_from_url_network_error(self, tmp_path):
        """Test installing from URL with network error."""
        import requests

        target_dir = tmp_path / "target"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection refused")

            with pytest.raises(InstallationError, match="Failed to download"):
                install_from_url("https://example.com/SKILL.md", None, target_dir)

    def test_install_from_url_invalid_content(self, tmp_path):
        """Test installing from URL with invalid SKILL.md content."""
        target_dir = tmp_path / "target"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.text = "This is not valid SKILL.md content"

            with pytest.raises(InstallationError, match="Invalid SKILL.md"):
                install_from_url("https://example.com/SKILL.md", None, target_dir)


class TestInstallFromGithub:
    """Tests for install_from_github function."""

    def test_install_github_invalid_format(self, tmp_path):
        """Test installing with invalid GitHub format."""
        target_dir = tmp_path / "target"

        with pytest.raises(InstallationError, match="Invalid GitHub repository"):
            install_from_github("invalid", None, target_dir)

    def test_install_github_repo_not_found(self, tmp_path):
        """Test installing from GitHub when repo/skill not found."""
        target_dir = tmp_path / "target"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 404

            with pytest.raises(InstallationError, match="Could not find SKILL.md"):
                install_from_github("user/repo/skill-name", None, target_dir)

    def test_install_github_success(self, tmp_path):
        """Test successful GitHub installation."""
        target_dir = tmp_path / "target"
        skill_content = "---\nname: gh-skill\ndescription: GitHub skill\n---\n\nContent\n"

        with patch("skill_hub.installer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = skill_content

            result = install_from_github("user/repo/gh-skill", None, target_dir)

        assert result.name == "gh-skill"
        assert (target_dir / "gh-skill" / "SKILL.md").exists()


class TestSyncSkill:
    """Tests for sync_skill function."""

    def test_sync_creates_copy(self, tmp_path):
        """Test that sync creates a copy of the skill."""
        source_dir = _make_source_skill(tmp_path / "source", "sync-test", "Skill to sync")
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        metadata = SkillMetadata(name="sync-test", description="Skill to sync")
        source_skill = Skill(
            metadata=metadata,
            content=(source_dir / "SKILL.md").read_text(),
            path=source_dir / "SKILL.md",
            source_directory="public",
        )

        result = sync_skill(source_skill, target_dir)

        assert result is not None
        assert result.name == "sync-test"
        assert (target_dir / "sync-test" / "SKILL.md").exists()

    def test_sync_dry_run(self, tmp_path):
        """Test sync with dry-run flag."""
        source_dir = _make_source_skill(tmp_path / "source", "dry-run-test", "Dry run test")
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        metadata = SkillMetadata(name="dry-run-test", description="Dry run test")
        source_skill = Skill(
            metadata=metadata,
            content=(source_dir / "SKILL.md").read_text(),
            path=source_dir / "SKILL.md",
            source_directory="public",
        )

        result = sync_skill(source_skill, target_dir, dry_run=True)

        assert result is not None
        assert not (target_dir / "dry-run-test" / "SKILL.md").exists()

    def test_sync_preserves_content(self, tmp_path):
        """Test that sync preserves skill content."""
        source_dir = _make_source_skill(tmp_path / "source", "content-test")
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        original_content = (source_dir / "SKILL.md").read_text()
        metadata = SkillMetadata(name="content-test", description="A test skill")
        source_skill = Skill(
            metadata=metadata,
            content=original_content,
            path=source_dir / "SKILL.md",
            source_directory="public",
        )

        sync_skill(source_skill, target_dir)

        synced_content = (target_dir / "content-test" / "SKILL.md").read_text()
        assert synced_content == original_content
