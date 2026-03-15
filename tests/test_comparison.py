"""Tests for skill-hub comparison module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.comparison import (
    ComparisonResult,
    SkillComparison,
    compare_skills,
    discover_and_compare_all_locals,
    discover_global_skills,
    discover_local_skills,
    format_comparison_result,
    parse_skill_version,
)


@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _create_skill(base_dir: Path, name: str, version: str = None) -> None:
    """Helper to create a skill directory with SKILL.md."""
    skill_dir = base_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"---\nname: {name}\ndescription: A test skill\n"
    if version:
        content += f"metadata:\n  version: {version}\n"
    content += "---\n\n# Test Skill\n"
    (skill_dir / "SKILL.md").write_text(content)


class TestSkillComparison:
    """Tests for SkillComparison dataclass."""

    def test_needs_update_true(self):
        sc = SkillComparison(name="s", status="update-available")
        assert sc.needs_update is True

    def test_needs_update_false(self):
        sc = SkillComparison(name="s", status="up-to-date")
        assert sc.needs_update is False

    def test_sort_key_ordering(self):
        local = SkillComparison(name="a", status="local-only")
        update = SkillComparison(name="b", status="update-available")
        uptodate = SkillComparison(name="c", status="up-to-date")
        glob = SkillComparison(name="d", status="global-only")
        assert sorted([glob, uptodate, update, local], key=lambda s: s.sort_key) == [
            local, update, uptodate, glob,
        ]

    def test_default_values(self):
        sc = SkillComparison(name="x")
        assert sc.local_version is None
        assert sc.global_version is None
        assert sc.status == "unknown"
        assert sc.local_source is None


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_property_filters(self, tmp_path):
        skills = {
            "a": SkillComparison(name="a", status="local-only"),
            "b": SkillComparison(name="b", status="global-only"),
            "c": SkillComparison(name="c", status="up-to-date"),
            "d": SkillComparison(name="d", status="update-available"),
            "e": SkillComparison(name="e", status="missing"),
        }
        result = ComparisonResult(local_path=tmp_path, global_path=tmp_path, skills=skills)
        assert len(result.local_only) == 1
        assert len(result.global_only) == 1
        assert len(result.up_to_date) == 1
        assert len(result.needs_update) == 1
        assert len(result.missing) == 1
        assert result.total == 5
        # local_count = all except global-only
        assert result.local_count == 4
        # global_count = all except local-only
        assert result.global_count == 4


class TestParseSkillVersion:
    """Tests for parse_skill_version function."""

    def test_parse_version_from_metadata(self, tmp_path):
        _create_skill(tmp_path, "s1", version="1.2.3")
        assert parse_skill_version(tmp_path / "s1") == "1.2.3"

    def test_parse_version_no_version(self, tmp_path):
        _create_skill(tmp_path, "s2")
        assert parse_skill_version(tmp_path / "s2") is None

    def test_parse_version_missing_dir(self, tmp_path):
        assert parse_skill_version(tmp_path / "nonexistent") is None

    def test_parse_direct_version_field(self, tmp_path):
        skill_dir = tmp_path / "s3"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: s3\ndescription: test\nversion: 0.5.0\n---\n\nContent\n"
        )
        assert parse_skill_version(skill_dir) == "0.5.0"


class TestDiscoverLocalSkills:
    """Tests for discover_local_skills function."""

    def test_returns_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".opencode" / "skills").mkdir(parents=True)
        result = discover_local_skills()
        assert result == Path(".opencode/skills")

    def test_fallback_agents(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".agents" / "skills").mkdir(parents=True)
        result = discover_local_skills()
        assert result == Path(".agents/skills")

    def test_default_opencode(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = discover_local_skills()
        assert result == Path(".opencode/skills")


class TestDiscoverGlobalSkills:
    """Tests for discover_global_skills function."""

    def test_returns_home_agents(self):
        result = discover_global_skills()
        assert result == Path.home() / ".agents" / "skills"


class TestCompareSkills:
    """Tests for compare_skills function."""

    def test_compare_identical_skills(self, tmp_path):
        """Test comparing identical skills."""
        local_dir = tmp_path / "local" / "skills"
        global_dir = tmp_path / "global" / "skills"
        local_dir.mkdir(parents=True)
        global_dir.mkdir(parents=True)

        _create_skill(local_dir, "test-skill", version="1.0.0")
        _create_skill(global_dir, "test-skill", version="1.0.0")

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert len(result.up_to_date) == 1
        assert len(result.needs_update) == 0

    def test_compare_needs_update(self, tmp_path):
        """Test comparing skills where global is newer."""
        local_dir = tmp_path / "local" / "skills"
        global_dir = tmp_path / "global" / "skills"
        local_dir.mkdir(parents=True)
        global_dir.mkdir(parents=True)

        _create_skill(local_dir, "test-skill", version="1.0.0")
        _create_skill(global_dir, "test-skill", version="2.0.0")

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert len(result.needs_update) == 1
        assert len(result.up_to_date) == 0

    def test_compare_local_only(self, tmp_path):
        """Test comparing skills only in local directory."""
        local_dir = tmp_path / "local" / "skills"
        global_dir = tmp_path / "global" / "skills"
        local_dir.mkdir(parents=True)
        global_dir.mkdir(parents=True)

        _create_skill(local_dir, "local-skill")

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert len(result.local_only) == 1
        assert len(result.global_only) == 0

    def test_compare_global_only(self, tmp_path):
        """Test comparing skills only in global directory."""
        local_dir = tmp_path / "local" / "skills"
        global_dir = tmp_path / "global" / "skills"
        local_dir.mkdir(parents=True)
        global_dir.mkdir(parents=True)

        _create_skill(global_dir, "global-skill")

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert len(result.global_only) == 1
        assert len(result.local_only) == 0

    def test_compare_mixed(self, tmp_path):
        """Test comparing with a mix of local-only, global-only, and shared skills."""
        local_dir = tmp_path / "local"
        global_dir = tmp_path / "global"
        local_dir.mkdir(parents=True)
        global_dir.mkdir(parents=True)

        _create_skill(local_dir, "shared", version="1.0.0")
        _create_skill(global_dir, "shared", version="1.0.0")
        _create_skill(local_dir, "local-only")
        _create_skill(global_dir, "global-only")

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert len(result.up_to_date) == 1
        assert len(result.local_only) == 1
        assert len(result.global_only) == 1
        assert result.total == 3

    def test_compare_empty_directories(self, tmp_path):
        """Test comparing two empty directories."""
        local_dir = tmp_path / "local"
        global_dir = tmp_path / "global"
        local_dir.mkdir()
        global_dir.mkdir()

        result = compare_skills(local_path=local_dir, global_path=global_dir)

        assert result.total == 0


class TestDiscoverAndCompareAllLocals:
    """Tests for discover_and_compare_all_locals function."""

    def test_no_local_directories(self, tmp_path):
        """Test comparing when no local directories exist."""
        global_dir = tmp_path / "global"
        global_dir.mkdir()

        tool_results, aggregated = discover_and_compare_all_locals(
            base_path=tmp_path, global_path=global_dir
        )

        assert tool_results == {}
        assert aggregated.local_count == 0

    def test_with_local_directories(self, tmp_path):
        """Test comparing with local directories."""
        local_dir = tmp_path / ".opencode" / "skills"
        local_dir.mkdir(parents=True)
        _create_skill(local_dir, "test-skill")

        global_dir = tmp_path / "global"
        global_dir.mkdir()

        tool_results, aggregated = discover_and_compare_all_locals(
            base_path=tmp_path, global_path=global_dir
        )

        assert "opencode" in tool_results
        assert aggregated.local_count >= 1

    def test_multiple_local_directories(self, tmp_path):
        """Test comparing with multiple local directories."""
        oc_dir = tmp_path / ".opencode" / "skills"
        oc_dir.mkdir(parents=True)
        _create_skill(oc_dir, "oc-skill")

        ag_dir = tmp_path / ".agents" / "skills"
        ag_dir.mkdir(parents=True)
        _create_skill(ag_dir, "ag-skill")

        global_dir = tmp_path / "global"
        global_dir.mkdir()

        tool_results, aggregated = discover_and_compare_all_locals(
            base_path=tmp_path, global_path=global_dir
        )

        assert "opencode" in tool_results
        assert "agents" in tool_results
        assert aggregated.local_count == 2


class TestFormatComparisonResult:
    """Tests for format_comparison_result function."""

    def test_format_returns_string(self, tmp_path):
        skills = {
            "a": SkillComparison(name="a", status="up-to-date", local_version="1.0", global_version="1.0"),
            "b": SkillComparison(name="b", status="local-only", local_version="1.0"),
        }
        result = ComparisonResult(local_path=tmp_path, global_path=tmp_path, skills=skills)
        output = format_comparison_result(result)
        assert isinstance(output, str)
