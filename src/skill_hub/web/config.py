"""Install directory configuration management."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from skill_hub.utils.path_utils import expand_home

SKILLS_REPO_ROOT = expand_home("~/.skills_repo")
CONFIG_FILE = SKILLS_REPO_ROOT / "config.json"

_DEFAULT_DIRS = [
    {"path": "~/.claude/skills", "label": "claude", "isDefault": True},
    {"path": "~/.agents/skills", "label": "agents", "isDefault": True},
]


@dataclass
class InstallDir:
    path: str
    label: str
    is_default: bool = False
    abbreviation: str = ""

    def __post_init__(self):
        if not self.abbreviation:
            # When loading from dict, abbreviation is already set
            # When creating new, we need to pass existing dirs
            pass  # Abbreviation will be set by caller

    @property
    def resolved_path(self) -> Path:
        return expand_home(self.path)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "label": self.label,
            "isDefault": self.is_default,
            "abbreviation": self.abbreviation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "InstallDir":
        return cls(
            path=d["path"],
            label=d["label"],
            is_default=d.get("isDefault", False),
            abbreviation=d.get("abbreviation", ""),
        )


def _generate_abbreviation(label: str, existing_dirs: list[InstallDir] = None) -> str:
    """Generate a unique abbreviation for a label.
    
    Algorithm:
    1. Take first letter
    2. If conflicts with existing dirs, take first two letters
    3. If still conflicts, take first three, etc.
    4. If label is exhausted, add numeric suffix
    """
    existing = {d.abbreviation for d in (existing_dirs or [])}
    
    for length in range(1, len(label) + 1):
        abbr = label[:length].capitalize()
        if abbr not in existing:
            return abbr
    
    # Fallback: add numeric suffix
    suffix = 1
    base = label.capitalize()
    while f"{base}{suffix}" in existing:
        suffix += 1
    return f"{base}{suffix}"


def get_install_dirs() -> list[InstallDir]:
    """Load install directories from config.json.
    
    If config doesn't exist, create it with defaults.
    """
    if not CONFIG_FILE.exists():
        dirs = [InstallDir.from_dict(d) for d in _DEFAULT_DIRS]
        # Set abbreviations for default dirs
        for d in dirs:
            if not d.abbreviation:
                d.abbreviation = _generate_abbreviation(d.label, dirs)
        _save_config(dirs)
        return dirs
    
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        dirs = [InstallDir.from_dict(d) for d in data.get("installDirs", [])]
        # Ensure abbreviations are set (for backwards compatibility)
        for d in dirs:
            if not d.abbreviation:
                d.abbreviation = _generate_abbreviation(d.label, dirs)
        return dirs
    except (json.JSONDecodeError, KeyError):
        dirs = [InstallDir.from_dict(d) for d in _DEFAULT_DIRS]
        for d in dirs:
            if not d.abbreviation:
                d.abbreviation = _generate_abbreviation(d.label, dirs)
        _save_config(dirs)
        return dirs


def _save_config(dirs: list[InstallDir]) -> None:
    """Persist install directories to config.json."""
    SKILLS_REPO_ROOT.mkdir(parents=True, exist_ok=True)
    data = {"installDirs": [d.to_dict() for d in dirs]}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_install_dir(path: str) -> InstallDir:
    """Add a new install directory. 
    
    Args:
        path: Directory path (supports ~ expansion)
        
    Returns:
        The created InstallDir
        
    Raises:
        ValueError: If path already exists in config
    """
    dirs = get_install_dirs()
    resolved = expand_home(path)
    
    for d in dirs:
        if d.resolved_path == resolved:
            # Already exists, return existing
            return d
    
    # Derive label from directory name
    label = resolved.name if resolved.name != "skills" else resolved.parent.name
    # Remove leading dot (e.g., .cursor -> cursor)
    label = label.lstrip(".")
    if not label:
        label = "dir"
    
    # Ensure unique label
    existing_labels = {d.label for d in dirs}
    base_label = label
    suffix = 1
    while label in existing_labels:
        label = f"{base_label}{suffix}"
        suffix += 1
    
    new_dir = InstallDir(path=path, label=label, is_default=False)
    new_dir.abbreviation = _generate_abbreviation(label, dirs)
    dirs.append(new_dir)
    _save_config(dirs)
    return new_dir


def remove_install_dir(label: str) -> None:
    """Remove an install directory by label.
    
    Args:
        label: Directory label to remove
        
    Raises:
        ValueError: If directory is default or not found
    """
    dirs = get_install_dirs()
    target = next((d for d in dirs if d.label == label), None)
    
    if target is None:
        raise ValueError(f"Directory not found: {label}")
    if target.is_default:
        raise ValueError(f"Cannot remove default directory: {label}")
    
    dirs = [d for d in dirs if d.label != label]
    _save_config(dirs)
