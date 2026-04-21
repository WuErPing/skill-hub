"""Integration tests for multi-layer skill directories feature.

These tests cover the end-to-end functionality of:
- Directory discovery with public and private directories
- Install to public/private directories
- Sync command between directories
- Priority resolution
- Dry-run mode
- Overwrite protection
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from skill_hub.cli import install_skill, list_skills, sync_skill_cmd
from skill_hub.discovery.engine import (
    DiscoveryEngine,
    discover_all_skill_directories,
    resolve_skill_priority,
)
from skill_hub.installer import get_install_path, install_from_local, sync_skill
from skill_hub.models import Skill, SkillMetadata


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _create_skill(base: Path, name: str, desc: str = "A test skill") -> Path:
    """Helper to create a minimal SKILL.md under base/name/."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nContent.\n"
    )
    return skill_dir


class TestDirectoryDiscovery:
    """Task 6.1: Test directory discovery with public and private directories."""

    def test_discover_both_public_and_project_dirs(self, temp_project_dir, monkeypatch):
        """Test discovering both public and project-level directories."""
        # Create project-level directory
        project_skills = temp_project_dir / ".agents" / "skills"
        project_skills.mkdir(parents=True)
        _create_skill(project_skills, "project-skill")

        # Mock home directory for public discovery
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)
            _create_skill(public_skills, "public-skill")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Discover all directories
            dirs = discover_all_skill_directories(temp_project_dir)

            # Should find both public and project directories
            types = [d[2] for d in dirs]
            assert "public" in types
            assert "project" in types

    def test_discover_multiple_tools(self, temp_project_dir):
        """Test discovering skills directories for multiple tools."""
        # Create multiple tool directories
        (temp_project_dir / ".agents" / "skills").mkdir(parents=True)
        (temp_project_dir / ".claude" / "skills").mkdir(parents=True)
        (temp_project_dir / ".opencode" / "skills").mkdir(parents=True)

        dirs = discover_all_skill_directories(temp_project_dir)

        tool_names = [d[1] for d in dirs]
        assert "agents" in tool_names
        assert "claude" in tool_names
        assert "opencode" in tool_names

    def test_skills_from_both_directories(self, temp_project_dir, monkeypatch):
        """Test that skills are discovered from both public and project dirs."""
        # Create project-level skill
        project_skills = temp_project_dir / ".agents" / "skills"
        project_skills.mkdir(parents=True)
        _create_skill(project_skills, "project-only")

        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)
            _create_skill(public_skills, "public-only")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Create discovery engines for both
            project_engine = DiscoveryEngine(project_skills, directory_type="project")
            public_engine = DiscoveryEngine(public_skills, directory_type="public")

            project_skills_list = project_engine.discover_skills()
            public_skills_list = public_engine.discover_skills()

            assert len(project_skills_list) == 1
            assert project_skills_list[0].name == "project-only"

            assert len(public_skills_list) == 1
            assert public_skills_list[0].name == "public-only"


class TestInstallToPublic:
    """Task 6.2: Test install to public directory (backward compatibility)."""

    def test_install_to_public_directory(self, temp_project_dir, monkeypatch):
        """Test installing a skill to the public directory."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Create source skill
            source_dir = temp_project_dir / "source-skill"
            source_dir.mkdir()
            (source_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: Test\n---\n\nContent."
            )

            # Install to public
            result = install_from_local(str(source_dir), None, public_skills)

            assert result is not None
            assert result.name == "test-skill"
            assert (public_skills / "test-skill" / "SKILL.md").exists()

    def test_default_install_is_public(self, temp_project_dir, monkeypatch):
        """Test that default install target is public directory."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            monkeypatch.setattr(Path, "home", lambda: home_path)

            # Get default install path
            install_path = get_install_path("my-skill")

            assert install_path == public_skills / "my-skill"

    def test_install_public_backward_compatible(self, runner, temp_project_dir, monkeypatch):
        """Test that install command works without --to flag (backward compatible)."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Create source skill
            source_dir = temp_project_dir / "source-skill"
            source_dir.mkdir()
            (source_dir / "SKILL.md").write_text(
                "---\nname: backward-compat\ndescription: Test\n---\n\nContent."
            )

            with patch("skill_hub.installer.install_from_local") as mock_install:
                mock_install.return_value = Skill(
                    metadata=SkillMetadata(name="backward-compat", description="Test"),
                    content="",
                    path=public_skills / "backward-compat" / "SKILL.md",
                )

                result = runner.invoke(install_skill, [str(source_dir)])

                assert result.exit_code == 0
                # Should default to public
                called_target = mock_install.call_args[0][2]
                assert str(called_target).endswith(".agents/skills")


class TestInstallToPrivate:
    """Task 6.3: Test install to private directory."""

    def test_install_to_private_directory(self, temp_project_dir, monkeypatch):
        """Test installing a skill to the private (project) directory."""
        monkeypatch.chdir(temp_project_dir)

        private_skills = temp_project_dir / ".agents" / "skills"
        private_skills.mkdir(parents=True)

        # Create source skill
        source_dir = temp_project_dir / "source-skill"
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text(
            "---\nname: private-skill\ndescription: Test\n---\n\nContent."
        )

        # Install to private
        result = install_from_local(str(source_dir), None, private_skills)

        assert result is not None
        assert result.name == "private-skill"
        assert (private_skills / "private-skill" / "SKILL.md").exists()

    def test_get_install_path_private(self, temp_project_dir, monkeypatch):
        """Test get_install_path returns correct private path."""
        monkeypatch.chdir(temp_project_dir)

        result = get_install_path("my-skill", target="project")

        # Path uses cwd, so compare resolved paths
        expected = Path.cwd() / ".agents" / "skills" / "my-skill"
        assert result.resolve() == expected.resolve()

    def test_cli_install_to_private(self, runner, temp_project_dir, monkeypatch):
        """Test CLI install command with --to private."""
        monkeypatch.chdir(temp_project_dir)

        # Create source skill
        source_dir = temp_project_dir / "source-skill"
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text(
            "---\nname: cli-private\ndescription: Test\n---\n\nContent."
        )

        with patch("skill_hub.installer.install_from_local") as mock_install:
            mock_install.return_value = Skill(
                metadata=SkillMetadata(name="cli-private", description="Test"),
                content="",
                path=temp_project_dir / ".agents" / "skills" / "cli-private" / "SKILL.md",
            )

            result = runner.invoke(install_skill, [str(source_dir), "--to", "private"])

            assert result.exit_code == 0
            called_target = mock_install.call_args[0][2]
            assert ".agents/skills" in str(called_target)


class TestSyncCommand:
    """Task 6.4: Test sync command (public to private, private to public)."""

    def test_sync_public_to_private(self, temp_project_dir, monkeypatch):
        """Test syncing a skill from public to private directory."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create skill in public
            _create_skill(public_skills, "syncable-skill", "Public version")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Create source skill object
            metadata = SkillMetadata(name="syncable-skill", description="Public version")
            source_skill = Skill(
                metadata=metadata,
                content=(public_skills / "syncable-skill" / "SKILL.md").read_text(),
                path=public_skills / "syncable-skill" / "SKILL.md",
                source_directory="public",
            )

            # Sync to private
            result = sync_skill(source_skill, private_skills)

            assert result is not None
            assert (private_skills / "syncable-skill" / "SKILL.md").exists()

    def test_sync_private_to_public(self, temp_project_dir, monkeypatch):
        """Test syncing a skill from private to public directory."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create skill in private
            _create_skill(private_skills, "private-sync", "Private version")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Create source skill object
            metadata = SkillMetadata(name="private-sync", description="Private version")
            source_skill = Skill(
                metadata=metadata,
                content=(private_skills / "private-sync" / "SKILL.md").read_text(),
                path=private_skills / "private-sync" / "SKILL.md",
                source_directory="project",
            )

            # Sync to public
            result = sync_skill(source_skill, public_skills)

            assert result is not None
            assert (public_skills / "private-sync" / "SKILL.md").exists()

    def test_cli_sync_command(self, runner, temp_project_dir, monkeypatch):
        """Test CLI sync command between directories."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create skill in public
            _create_skill(public_skills, "cli-sync-skill")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Mock the discovery to return our test directories
            def mock_discover():
                return [
                    (public_skills, "agents", "public"),
                    (private_skills, "agents", "project"),
                ]

            with patch("skill_hub.cli.discover_all_skill_directories", mock_discover):
                with patch("skill_hub.installer.sync_skill") as mock_sync:
                    mock_sync.return_value = Skill(
                        metadata=SkillMetadata(name="cli-sync-skill", description="Test"),
                        content="",
                        path=private_skills / "cli-sync-skill" / "SKILL.md",
                    )

                    result = runner.invoke(sync_skill_cmd, ["cli-sync-skill", "public", "private"])

                    assert result.exit_code == 0


class TestPriorityResolution:
    """Task 6.5: Test priority resolution when same skill exists in multiple directories."""

    def test_project_takes_priority_over_public(self, temp_project_dir, monkeypatch):
        """Test that project-level skills take priority over public skills."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create same skill in both directories
            _create_skill(public_skills, "priority-test", "Public version")
            _create_skill(private_skills, "priority-test", "Project version")

            # Create skill objects
            public_metadata = SkillMetadata(name="priority-test", description="Public version")
            public_skill = Skill(
                metadata=public_metadata,
                content="",
                path=public_skills / "priority-test" / "SKILL.md",
                source_directory="public",
            )

            project_metadata = SkillMetadata(name="priority-test", description="Project version")
            project_skill = Skill(
                metadata=project_metadata,
                content="",
                path=private_skills / "priority-test" / "SKILL.md",
                source_directory="project",
            )

            # Resolve priority
            skills_by_name = {"priority-test": [public_skill, project_skill]}
            resolved = resolve_skill_priority(skills_by_name)

            # Project should win
            assert resolved["priority-test"].source_directory == "project"

    def test_public_used_when_no_project(self, temp_project_dir, monkeypatch):
        """Test that public skill is used when no project version exists."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            # Create skill only in public
            _create_skill(public_skills, "public-only-priority")

            public_metadata = SkillMetadata(name="public-only-priority", description="Test")
            public_skill = Skill(
                metadata=public_metadata,
                content="",
                path=public_skills / "public-only-priority" / "SKILL.md",
                source_directory="public",
            )

            skills_by_name = {"public-only-priority": [public_skill]}
            resolved = resolve_skill_priority(skills_by_name)

            assert resolved["public-only-priority"].source_directory == "public"

    def test_priority_with_multiple_duplicates(self, temp_project_dir, monkeypatch):
        """Test priority resolution with multiple duplicate skills."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create multiple skills with duplicates
            for name in ["skill-a", "skill-b", "skill-c"]:
                _create_skill(public_skills, name, f"Public {name}")
                _create_skill(private_skills, name, f"Project {name}")

            # Create skill objects
            skills_by_name = {}
            for name in ["skill-a", "skill-b", "skill-c"]:
                public_skill = Skill(
                    metadata=SkillMetadata(name=name, description=f"Public {name}"),
                    content="",
                    path=public_skills / name / "SKILL.md",
                    source_directory="public",
                )
                project_skill = Skill(
                    metadata=SkillMetadata(name=name, description=f"Project {name}"),
                    content="",
                    path=private_skills / name / "SKILL.md",
                    source_directory="project",
                )
                skills_by_name[name] = [public_skill, project_skill]

            resolved = resolve_skill_priority(skills_by_name)

            # All should resolve to project
            for name in ["skill-a", "skill-b", "skill-c"]:
                assert resolved[name].source_directory == "project"


class TestDryRunMode:
    """Task 6.6: Test dry-run mode for sync."""

    def test_dry_run_does_not_create_files(self, temp_project_dir, monkeypatch):
        """Test that dry-run mode does not actually create files."""
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        _create_skill(source_dir, "dry-run-test")

        target_dir = temp_project_dir / "target"
        target_dir.mkdir()

        metadata = SkillMetadata(name="dry-run-test", description="Test")
        source_skill = Skill(
            metadata=metadata,
            content=(source_dir / "dry-run-test" / "SKILL.md").read_text(),
            path=source_dir / "dry-run-test" / "SKILL.md",
            source_directory="public",
        )

        # Sync with dry-run
        result = sync_skill(source_skill, target_dir, dry_run=True)

        assert result is not None
        # File should NOT exist
        assert not (target_dir / "dry-run-test" / "SKILL.md").exists()

    def test_dry_run_returns_skill_info(self, temp_project_dir):
        """Test that dry-run returns skill information without copying."""
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        _create_skill(source_dir, "info-test")

        target_dir = temp_project_dir / "target"
        target_dir.mkdir()

        metadata = SkillMetadata(name="info-test", description="Test")
        source_skill = Skill(
            metadata=metadata,
            content=(source_dir / "info-test" / "SKILL.md").read_text(),
            path=source_dir / "info-test" / "SKILL.md",
            source_directory="public",
        )

        result = sync_skill(source_skill, target_dir, dry_run=True)

        assert result.name == "info-test"
        assert result.metadata.description == "Test"

    def test_cli_dry_run_flag(self, runner, temp_project_dir, monkeypatch):
        """Test CLI sync command with --dry-run flag."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            _create_skill(public_skills, "cli-dry-run")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Mock the discovery to return our test directories
            def mock_discover():
                return [
                    (public_skills, "agents", "public"),
                    (private_skills, "agents", "project"),
                ]

            with patch("skill_hub.cli.discover_all_skill_directories", mock_discover):
                with patch("skill_hub.installer.sync_skill") as mock_sync:
                    mock_sync.return_value = Skill(
                        metadata=SkillMetadata(name="cli-dry-run", description="Test"),
                        content="",
                        path=private_skills / "cli-dry-run" / "SKILL.md",
                    )

                    result = runner.invoke(
                        sync_skill_cmd, ["cli-dry-run", "public", "private", "--dry-run"]
                    )

                    assert result.exit_code == 0
                    # Verify dry_run=True was passed
                    call_kwargs = mock_sync.call_args[1]
                    assert call_kwargs.get("dry_run") is True


class TestOverwriteProtection:
    """Task 6.7: Test overwrite protection."""

    def test_sync_overwrites_existing_skill(self, temp_project_dir):
        """Test that sync overwrites existing skill by default."""
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        _create_skill(source_dir, "existing-skill", "New version")

        target_dir = temp_project_dir / "target"
        target_dir.mkdir()
        # Pre-create the skill in target
        _create_skill(target_dir, "existing-skill", "Old version")

        metadata = SkillMetadata(name="existing-skill", description="New version")
        source_skill = Skill(
            metadata=metadata,
            content=(source_dir / "existing-skill" / "SKILL.md").read_text(),
            path=source_dir / "existing-skill" / "SKILL.md",
            source_directory="public",
        )

        # Sync should overwrite by default
        result = sync_skill(source_skill, target_dir)

        assert result is not None
        # Verify content was updated
        updated_content = (target_dir / "existing-skill" / "SKILL.md").read_text()
        assert "New version" in updated_content

    def test_install_overwrites_existing_skill(self, temp_project_dir, monkeypatch):
        """Test that install overwrites existing skill by default."""
        monkeypatch.chdir(temp_project_dir)

        target_dir = temp_project_dir / ".agents" / "skills"
        target_dir.mkdir(parents=True)

        # Pre-create existing skill
        _create_skill(target_dir, "overwrite-test", "Old version")

        # Create new source skill
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text(
            "---\nname: overwrite-test\ndescription: New version\n---\n\nNew content."
        )

        # Install should overwrite by default
        result = install_from_local(str(source_dir), None, target_dir)

        assert result is not None
        # Verify content was updated
        updated_content = (target_dir / "overwrite-test" / "SKILL.md").read_text()
        assert "New version" in updated_content

    def test_cli_sync_with_force_flag(self, runner, temp_project_dir, monkeypatch):
        """Test CLI sync command with --force flag (handled at CLI layer)."""
        with tempfile.TemporaryDirectory() as home_tmp:
            home_path = Path(home_tmp)
            public_skills = home_path / ".agents" / "skills"
            public_skills.mkdir(parents=True)

            private_skills = temp_project_dir / ".agents" / "skills"
            private_skills.mkdir(parents=True)

            # Create skill in both locations
            _create_skill(public_skills, "force-sync-skill", "Public version")
            _create_skill(private_skills, "force-sync-skill", "Private version")

            monkeypatch.setattr(Path, "home", lambda: home_path)
            monkeypatch.chdir(temp_project_dir)

            # Mock the discovery to return our test directories
            def mock_discover():
                return [
                    (public_skills, "agents", "public"),
                    (private_skills, "agents", "project"),
                ]

            with patch("skill_hub.cli.discover_all_skill_directories", mock_discover):
                with patch("skill_hub.installer.sync_skill") as mock_sync:
                    mock_sync.return_value = Skill(
                        metadata=SkillMetadata(name="force-sync-skill", description="Test"),
                        content="",
                        path=private_skills / "force-sync-skill" / "SKILL.md",
                    )

                    # Use --force to skip confirmation
                    result = runner.invoke(
                        sync_skill_cmd, ["force-sync-skill", "public", "private", "--force"]
                    )

                    assert result.exit_code == 0
                    # Verify sync_skill was called
                    mock_sync.assert_called_once()
