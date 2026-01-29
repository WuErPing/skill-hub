"""Tests for utility functions."""

import pytest

from skill_hub.utils import (
    compute_checksum,
    validate_description,
    validate_skill_name,
)


class TestSkillNameValidation:
    """Tests for skill name validation."""

    def test_valid_names(self) -> None:
        """Test valid skill names."""
        assert validate_skill_name("git-release")
        assert validate_skill_name("python-formatter")
        assert validate_skill_name("test")
        assert validate_skill_name("a1-b2-c3")

    def test_invalid_names(self) -> None:
        """Test invalid skill names."""
        assert not validate_skill_name("Git-Release")  # uppercase
        assert not validate_skill_name("git_release")  # underscore
        assert not validate_skill_name("-git-release")  # starts with hyphen
        assert not validate_skill_name("git-release-")  # ends with hyphen
        assert not validate_skill_name("git--release")  # consecutive hyphens
        assert not validate_skill_name("")  # empty
        assert not validate_skill_name("a" * 65)  # too long


class TestDescriptionValidation:
    """Tests for description validation."""

    def test_valid_descriptions(self) -> None:
        """Test valid descriptions."""
        assert validate_description("A")
        assert validate_description("Valid description")
        assert validate_description("x" * 1024)

    def test_invalid_descriptions(self) -> None:
        """Test invalid descriptions."""
        assert not validate_description("")  # empty
        assert not validate_description("x" * 1025)  # too long


class TestChecksum:
    """Tests for checksum computation."""

    def test_checksum_consistency(self) -> None:
        """Test checksum is consistent."""
        content = "test content"
        checksum1 = compute_checksum(content)
        checksum2 = compute_checksum(content)
        assert checksum1 == checksum2

    def test_checksum_uniqueness(self) -> None:
        """Test different content produces different checksums."""
        checksum1 = compute_checksum("content1")
        checksum2 = compute_checksum("content2")
        assert checksum1 != checksum2
