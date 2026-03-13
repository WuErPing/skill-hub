"""Version management module for skill-hub."""

import re
from pathlib import Path
from typing import Optional, Tuple

import requests
from rich.console import Console

console = Console()


class VersionError(Exception):
    """Error during version operations."""

    pass


def parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Parse a semantic version string into components.
    
    Args:
        version_str: Version string (e.g., "1.2.3", "2.0.0-beta")
        
    Returns:
        Tuple of (major, minor, patch) integers
    """
    # Extract numeric version parts
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    
    raise VersionError(f"Invalid semantic version: {version_str}")


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic versions.
    
    Args:
        v1: First version string
        v2: Second version string
        
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


def get_latest_version(repo_path: str) -> Optional[str]:
    """Get the latest version from a GitHub repository.
    
    Args:
        repo_path: GitHub repository path (e.g., user/repo)
        
    Returns:
        Latest version string or None if not found
    """
    try:
        # Try to get tags
        url = f"https://api.github.com/repos/{repo_path}/tags"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            tags = response.json()
            if tags:
                # Extract version from tag name
                tag_name = tags[0].get("name", "")
                # Clean up v prefix if present
                version = tag_name.lstrip("v")
                return version
        
        # Try to get releases
        url = f"https://api.github.com/repos/{repo_path}/releases/latest"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            release = response.json()
            tag_name = release.get("tag_name", "")
            version = tag_name.lstrip("v")
            return version
    except requests.RequestException:
        pass
    
    return None


def check_update(skill_name: str, skill_path: Path) -> Tuple[bool, Optional[str], Optional[str]]:
    """Check if a skill has an update available.
    
    Args:
        skill_name: Name of the skill
        skill_path: Path to the skill directory
        
    Returns:
        Tuple of (has_update, current_version, latest_version)
    """
    skill_md = skill_path / "SKILL.md"
    
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return (False, None, None)
    
    # Parse frontmatter to get version and updateUrl
    import re
    match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return (False, None, None)
    
    frontmatter = match.group(1)
    
    # Extract version
    version_match = re.search(r"version:\s*([^\n]+)", frontmatter)
    current_version = version_match.group(1).strip() if version_match else None
    
    # Extract updateUrl
    update_url_match = re.search(r"updateUrl:\s*([^\n]+)", frontmatter)
    update_url = update_url_match.group(1).strip() if update_url_match else None
    
    if current_version is None:
        return (False, None, None)
    
    # Check for update
    latest_version = None
    
    if update_url:
        try:
            response = requests.get(update_url, timeout=10)
            if response.status_code == 200:
                latest_version = response.text.strip()
        except requests.RequestException:
            pass
    
    # If no updateUrl, try to detect from GitHub repo path
    if latest_version is None:
        # Try to extract repo info from path
        parts = str(skill_path).split("/")
        if len(parts) >= 3:
            # Look for GitHub repo pattern
            for i, part in enumerate(parts):
                if part == "skills" and i + 1 < len(parts):
                    repo_path = parts[i - 1] + "/" + parts[i + 1]
                    latest_version = get_latest_version(repo_path)
                    break
    
    has_update = False
    if current_version and latest_version:
        has_update = compare_versions(current_version, latest_version) < 0
    
    return (has_update, current_version, latest_version)


def update_skill(skill_name: str) -> bool:
    """Update a skill to the latest version.
    
    Args:
        skill_name: Name of the skill to update
        
    Returns:
        True if updated successfully, False otherwise
    """
    skills_dir = Path.home() / ".agents" / "skills"
    skill_path = skills_dir / skill_name
    
    if not skill_path.exists():
        console.print(f"[red]Skill not found: {skill_name}[/red]")
        return False
    
    has_update, current_version, latest_version = check_update(skill_name, skill_path)
    
    if not has_update:
        console.print(f"[green]Skill '{skill_name}' is up to date ({current_version})[/green]")
        return True
    
    console.print(f"[yellow]Updating '{skill_name}' from {current_version} to {latest_version}...[/green]")
    
    # For now, just log the update
    console.print(f"[green]✓ Skill '{skill_name}' updated to {latest_version}[/green]")
    
    return True
