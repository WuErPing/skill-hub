"""Version management module for skill-hub."""

import re
from typing import Optional, Tuple

import requests


def parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Parse a semantic version string into components."""
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    raise ValueError(f"Invalid semantic version: {version_str}")


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic versions.

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    parts1 = parse_semver(v1)
    parts2 = parse_semver(v2)
    for a, b in zip(parts1, parts2):
        if a < b:
            return -1
        if a > b:
            return 1
    return 0


def get_latest_version(repo_path: str, timeout: float = 10) -> Optional[str]:
    """Get the latest version from a GitHub repository."""
    try:
        url = f"https://api.github.com/repos/{repo_path}/tags"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            tags = response.json()
            if tags:
                tag_name = tags[0].get("name", "")
                return tag_name.lstrip("v")

        url = f"https://api.github.com/repos/{repo_path}/releases/latest"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            release = response.json()
            tag_name = release.get("tag_name", "")
            return tag_name.lstrip("v")
    except requests.RequestException:
        pass

    return None
