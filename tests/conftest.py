"""Test fixtures and configuration for skill-hub."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_skills_dir():
    """Create a temporary skills directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_skill_metadata():
    """Sample skill metadata for testing."""
    return {
        "name": "test-skill",
        "description": "A test skill for unit tests",
        "license": "MIT",
        "compatibility": "claude, opencode",
        "version": "1.0.0",
    }


@pytest.fixture
def sample_skill_content(sample_skill_metadata):
    """Sample skill content with YAML frontmatter."""
    metadata_str = "\n".join(f"{k}: {v}" for k, v in sample_skill_metadata.items())
    return f"""---
{metadata_str}
---

# Test Skill

This is the content of the test skill.
"""
