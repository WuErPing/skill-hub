"""Tests for install directory configuration management."""

import json
from pathlib import Path

import pytest

from skill_hub.web.config import (
    InstallDir,
    get_install_dirs,
    add_install_dir,
    remove_install_dir,
    CONFIG_FILE,
)


@pytest.fixture
def temp_config(tmp_path):
    """Override config file location for tests."""
    import skill_hub.web.config as config_module
    original = config_module.CONFIG_FILE
    config_module.CONFIG_FILE = tmp_path / "config.json"
    yield tmp_path
    config_module.CONFIG_FILE = original


def test_default_dirs_on_first_load(temp_config):
    """When config.json doesn't exist, default dirs are auto-created."""
    dirs = get_install_dirs()
    assert len(dirs) == 2
    assert dirs[0].label == "claude"
    assert dirs[0].is_default is True
    assert dirs[1].label == "agents"
    assert dirs[1].is_default is True


def test_add_custom_dir(temp_config):
    """Adding a custom dir persists to config."""
    add_install_dir("~/.cursor/skills")
    dirs = get_install_dirs()
    labels = [d.label for d in dirs]
    assert "cursor" in labels
    # Verify persisted
    import skill_hub.web.config as config_module
    with open(config_module.CONFIG_FILE) as f:
        data = json.load(f)
    assert any(d["label"] == "cursor" for d in data["installDirs"])


def test_add_duplicate_dir_ignored(temp_config):
    """Adding an existing dir returns existing without error."""
    existing = add_install_dir("~/.claude/skills")  # already default
    dirs = get_install_dirs()
    assert len(dirs) == 2
    assert existing.label == "claude"


def test_remove_custom_dir(temp_config):
    """Removing a custom dir works."""
    add_install_dir("~/.cursor/skills")
    remove_install_dir("cursor")
    dirs = get_install_dirs()
    labels = [d.label for d in dirs]
    assert "cursor" not in labels


def test_cannot_remove_default_dir(temp_config):
    """Removing a default dir raises error."""
    with pytest.raises(ValueError, match="Cannot remove default"):
        remove_install_dir("claude")


def test_abbreviation_generation(temp_config):
    """Abbreviations avoid conflicts using first-N-letters algorithm."""
    add_install_dir("~/.cursor/skills")   # "cursor" -> "Cu" (C taken by claude)
    add_install_dir("~/.custom/skills")   # "custom" -> "Cus" (C and Cu taken)
    dirs = get_install_dirs()
    cursor_dir = next(d for d in dirs if d.label == "cursor")
    custom_dir = next(d for d in dirs if d.label == "custom")
    assert cursor_dir.abbreviation == "Cu"
    assert custom_dir.abbreviation == "Cus"
