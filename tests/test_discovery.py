"""Tests for skill-hub discovery engine."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.discovery.engine import (
    DiscoveryEngine,
    discover_all_skill_directories,
    discover_all_local_skills,
    discover_local_skills_dirs,
    resolve_skill_priority,
)
from skill_hub.models import Skill, SkillMetadata


@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _write_skill(base: Path, name: str, desc: str = "A test skill") -> Path:
    """Helper to create a minimal SKILL.md under base/name/."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nContent.\n"
    )
    return skill_dir


class TestDiscoverLocalSkillsDirs:
    """Tests for discover_local_skills_dirs function."""

    def test_no_skill_directories(self, temp_base_dir):
        """Test when no skill directories exist."""
        result = discover_local_skills_dirs(temp_base_dir)
        assert result == []

    def test_with_skill_directories(self, temp_base_dir):
        """Test discovering skill directories."""
        opencode_dir = temp_base_dir / ".opencode" / "skills"
        opencode_dir.mkdir(parents=True)

        result = discover_local_skills_dirs(temp_base_dir)
        assert len(result) == 1
        path, tool_name = result[0]
        assert tool_name == "opencode"
        assert path == opencode_dir

    def test_multiple_skill_directories(self, temp_base_dir):
        """Test discovering multiple skill directories."""
        (temp_base_dir / ".opencode" / "skills").mkdir(parents=True)
        (temp_base_dir / ".agents" / "skills").mkdir(parents=True)

        result = discover_local_skills_dirs(temp_base_dir)
        assert len(result) == 2
        tool_names = [name for _, name in result]
        assert "opencode" in tool_names
        assert "agents" in tool_names

    def test_ignores_non_hidden_dirs(self, temp_base_dir):
        """Test that non-hidden directories are ignored."""
        (temp_base_dir / "opencode" / "skills").mkdir(parents=True)
        result = discover_local_skills_dirs(temp_base_dir)
        assert result == []

    def test_ignores_hidden_without_skills_subdir(self, temp_base_dir):
        """Test that hidden directories without a skills subdir are ignored."""
        (temp_base_dir / ".myapp").mkdir()
        result = discover_local_skills_dirs(temp_base_dir)
        assert result == []

    def test_default_base_path(self, temp_base_dir, monkeypatch):
        """Test default base_path falls back to cwd."""
        monkeypatch.chdir(temp_base_dir)
        (temp_base_dir / ".agents" / "skills").mkdir(parents=True)
        result = discover_local_skills_dirs()
        assert len(result) == 1


class TestDiscoverAllSkillDirectories:
    """Tests for discover_all_skill_directories function."""

    def test_includes_project_level_dirs(self, temp_base_dir):
        """Test discovering project-level directories."""
        (temp_base_dir / ".opencode" / "skills").mkdir(parents=True)

        result = discover_all_skill_directories(temp_base_dir)
        project_results = [(p, t, d) for p, t, d in result if d == "project"]
        assert len(project_results) == 1
        assert project_results[0][1] == "opencode"

    def test_public_dirs_always_from_home(self, temp_base_dir):
        """Test that public dirs come from home directory, not base_path."""
        result = discover_all_skill_directories(temp_base_dir)
        public_results = [(p, t, d) for p, t, d in result if d == "public"]
        for path, _, _ in public_results:
            assert str(Path.home()) in str(path)

    def test_empty_base_dir(self, temp_base_dir):
        """Test with an empty base directory (no project-level dirs)."""
        result = discover_all_skill_directories(temp_base_dir)
        project_results = [(p, t, d) for p, t, d in result if d == "project"]
        assert project_results == []


class TestDiscoverAllLocalSkills:
    """Tests for discover_all_local_skills function."""

    def test_no_local_skills(self, temp_base_dir):
        """Test when no local skills exist."""
        result = discover_all_local_skills(temp_base_dir)
        assert result == {}

    def test_with_skill_files(self, temp_base_dir):
        """Test discovering skills from files."""
        skills_dir = temp_base_dir / ".opencode" / "skills"
        _write_skill(skills_dir, "test-skill")

        result = discover_all_local_skills(temp_base_dir)
        assert "opencode" in result
        assert len(result["opencode"]) == 1

    def test_multiple_skills_in_one_dir(self, temp_base_dir):
        """Test discovering multiple skills from one directory."""
        skills_dir = temp_base_dir / ".agents" / "skills"
        _write_skill(skills_dir, "skill-a")
        _write_skill(skills_dir, "skill-b")

        result = discover_all_local_skills(temp_base_dir)
        assert "agents" in result
        assert len(result["agents"]) == 2


class TestDiscoveryEngine:
    """Tests for DiscoveryEngine class."""

    def test_discover_skills_empty_directory(self, temp_base_dir):
        """Test discovering skills from empty directory."""
        engine = DiscoveryEngine(temp_base_dir)
        skills = engine.discover_skills()
        assert skills == []

    def test_discover_skills_nonexistent_directory(self, temp_base_dir):
        """Test discovering skills from a nonexistent directory."""
        engine = DiscoveryEngine(temp_base_dir / "nonexistent")
        skills = engine.discover_skills()
        assert skills == []

    def test_discover_skills_with_skill_file(self, temp_base_dir):
        """Test discovering skills from a SKILL.md file."""
        skills_dir = temp_base_dir / "skills"
        _write_skill(skills_dir, "test-skill")

        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()
        assert len(skills) == 1
        assert skills[0].name == "test-skill"

    def test_discover_skills_skips_backup(self, temp_base_dir):
        """Test that backup directories are skipped."""
        skills_dir = temp_base_dir / "skills"
        _write_skill(skills_dir, "normal-skill")
        _write_skill(skills_dir / "backup", "backup-skill")

        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()
        skill_names = [s.name for s in skills]
        assert "normal-skill" in skill_names
        assert "backup-skill" not in skill_names

    def test_directory_type_tracking(self, temp_base_dir):
        """Test that directory_type is propagated to discovered skills."""
        skills_dir = temp_base_dir / "skills"
        _write_skill(skills_dir, "my-skill")

        engine = DiscoveryEngine(skills_dir, directory_type="project")
        skills = engine.discover_skills()
        assert len(skills) == 1
        assert skills[0].source_directory == "project"

    def test_discover_multiple_skills(self, temp_base_dir):
        """Test discovering multiple skills."""
        skills_dir = temp_base_dir / "skills"
        _write_skill(skills_dir, "alpha")
        _write_skill(skills_dir, "beta")
        _write_skill(skills_dir, "gamma")

        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()
        assert len(skills) == 3

    def test_discover_skills_with_updates(self, temp_base_dir):
        """Test discover_skills_with_updates method."""
        skills_dir = temp_base_dir / "skills"
        skill_dir = skills_dir / "versioned-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: versioned-skill\ndescription: test\n"
            "metadata:\n  version: 2.0.0\n---\n\nContent\n"
        )

        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills_with_updates()
        assert len(skills) == 1
        assert hasattr(skills[0], "_update_status")
        assert skills[0]._update_status["current_version"] == "2.0.0"


class TestResolveSkillPriority:
    """Tests for resolve_skill_priority function."""

    def test_single_skill(self, tmp_path):
        """Test resolving priority for single skill."""
        metadata = SkillMetadata(name="test-skill", description="A test skill")
        skill = Skill(metadata=metadata, content="", path=tmp_path / "test-skill")

        result = resolve_skill_priority({"test-skill": [skill]})
        assert result["test-skill"] == skill

    def test_project_over_public(self, tmp_path):
        """Test that project skills take priority over public."""
        metadata = SkillMetadata(name="test-skill", description="Public skill")
        public_skill = Skill(
            metadata=metadata,
            content="",
            path=tmp_path / "public" / "test-skill",
            source_directory="public",
        )

        project_metadata = SkillMetadata(name="test-skill", description="Project skill")
        project_skill = Skill(
            metadata=project_metadata,
            content="",
            path=tmp_path / "project" / "test-skill",
            source_directory="project",
        )

        result = resolve_skill_priority({"test-skill": [public_skill, project_skill]})
        assert result["test-skill"].source_directory == "project"

    def test_public_when_no_project(self, tmp_path):
        """Test that public skill is selected when no project exists."""
        metadata = SkillMetadata(name="test-skill", description="Public skill")
        public_skill = Skill(
            metadata=metadata,
            content="",
            path=tmp_path / "public" / "test-skill",
            source_directory="public",
        )

        result = resolve_skill_priority({"test-skill": [public_skill]})
        assert result["test-skill"].source_directory == "public"

    def test_fallback_to_first_when_no_match(self, tmp_path):
        """Test fallback to first skill when source_directory doesn't match known types."""
        metadata = SkillMetadata(name="test-skill", description="Unknown")
        skill = Skill(
            metadata=metadata,
            content="",
            path=tmp_path / "test-skill",
            source_directory="custom",
        )
        result = resolve_skill_priority({"test-skill": [skill]})
        assert result["test-skill"] == skill
