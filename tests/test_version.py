"""Tests for skill-hub version module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from skill_hub.version import (
    VersionError,
    check_update,
    compare_versions,
    get_latest_version,
    parse_semver,
    update_skill,
)


class TestParseSemver:
    """Tests for parse_semver function."""

    def test_basic_version(self):
        assert parse_semver("1.2.3") == (1, 2, 3)

    def test_version_with_v_prefix(self):
        assert parse_semver("v1.2.3") == (1, 2, 3)

    def test_version_zero(self):
        assert parse_semver("0.0.0") == (0, 0, 0)

    def test_large_numbers(self):
        assert parse_semver("100.200.300") == (100, 200, 300)

    def test_version_with_prerelease(self):
        assert parse_semver("1.2.3-beta") == (1, 2, 3)

    def test_invalid_version_raises(self):
        with pytest.raises(VersionError, match="Invalid semantic version"):
            parse_semver("not-a-version")

    def test_partial_version_raises(self):
        with pytest.raises(VersionError):
            parse_semver("1.2")


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_equal_versions(self):
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_v1_less_than_v2_major(self):
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_v1_less_than_v2_minor(self):
        assert compare_versions("1.0.0", "1.1.0") == -1

    def test_v1_less_than_v2_patch(self):
        assert compare_versions("1.0.0", "1.0.1") == -1

    def test_v1_greater_than_v2(self):
        assert compare_versions("2.0.0", "1.0.0") == 1

    def test_with_v_prefix(self):
        assert compare_versions("v1.0.0", "v1.0.0") == 0

    def test_mixed_prefix(self):
        assert compare_versions("v1.0.0", "1.0.0") == 0


class TestGetLatestVersion:
    """Tests for get_latest_version function."""

    def test_returns_version_from_tags(self):
        with patch("skill_hub.version.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [{"name": "v1.5.0"}]

            result = get_latest_version("user/repo")

        assert result == "1.5.0"

    def test_strips_v_prefix(self):
        with patch("skill_hub.version.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [{"name": "v2.0.0"}]

            result = get_latest_version("user/repo")

        assert result == "2.0.0"

    def test_returns_none_on_error(self):
        import requests

        with patch("skill_hub.version.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("timeout")

            result = get_latest_version("user/repo")

        assert result is None

    def test_returns_none_when_no_tags(self):
        with patch("skill_hub.version.requests.get") as mock_get:
            resp = mock_get.return_value
            resp.status_code = 200
            resp.json.return_value = []
            # Second call for releases also returns no tags
            mock_get.return_value.status_code = 404

            result = get_latest_version("user/repo")

        # Either None or empty, depends on implementation flow
        # The function tries tags first, then releases
        assert result is None or result == ""


class TestCheckUpdate:
    """Tests for check_update function."""

    def test_no_skill_md(self, tmp_path):
        has_update, current, latest = check_update("missing", tmp_path / "missing")
        assert has_update is False
        assert current is None
        assert latest is None

    def test_no_version_in_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "no-version"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: no-version\ndescription: test\n---\n\nContent\n")

        has_update, current, latest = check_update("no-version", skill_dir)
        assert has_update is False
        assert current is None

    def test_no_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "bad"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter here")

        has_update, current, latest = check_update("bad", skill_dir)
        assert has_update is False

    def test_with_version_and_update_url(self, tmp_path):
        skill_dir = tmp_path / "versioned"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: versioned\ndescription: test\nversion: 1.0.0\n"
            "updateUrl: https://example.com/version\n---\n\nContent\n"
        )

        with patch("skill_hub.version.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "2.0.0"

            has_update, current, latest = check_update("versioned", skill_dir)

        assert has_update is True
        assert current == "1.0.0"
        assert latest == "2.0.0"

    def test_version_up_to_date(self, tmp_path):
        skill_dir = tmp_path / "uptodate"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: uptodate\ndescription: test\nversion: 2.0.0\n"
            "updateUrl: https://example.com/version\n---\n\nContent\n"
        )

        with patch("skill_hub.version.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "2.0.0"

            has_update, current, latest = check_update("uptodate", skill_dir)

        assert has_update is False
        assert current == "2.0.0"


class TestUpdateSkill:
    """Tests for update_skill function."""

    def test_skill_not_found(self, tmp_path):
        with patch("skill_hub.version.Path.home", return_value=tmp_path):
            (tmp_path / ".agents" / "skills").mkdir(parents=True)
            result = update_skill("nonexistent")
        assert result is False

    def test_skill_up_to_date(self, tmp_path):
        with patch("skill_hub.version.Path.home", return_value=tmp_path):
            skill_dir = tmp_path / ".agents" / "skills" / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: test\nversion: 1.0.0\n---\n\nContent\n"
            )

            with patch("skill_hub.version.check_update", return_value=(False, "1.0.0", None)):
                result = update_skill("test-skill")

        assert result is True
