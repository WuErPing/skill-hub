"""Skill installation module."""

import shutil
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console

from skill_hub.models import Skill, SkillMetadata
from skill_hub.utils.yaml_parser import parse_skill_file

console = Console()


class InstallationError(Exception):
    """Error during skill installation."""

    pass


def install_from_github(repo_path: str, skill_name: Optional[str] = None) -> Skill:
    """Install a skill from a GitHub repository.
    
    Args:
        repo_path: GitHub repository path (e.g., user/repo/skill-name)
        skill_name: Optional custom name for the installed skill
        
    Returns:
        Installed Skill object
        
    Raises:
        InstallationError: If installation fails
    """
    # Parse repo path to extract components
    parts = repo_path.split("/")
    if len(parts) < 2:
        raise InstallationError(f"Invalid GitHub repository format: {repo_path}")
    
    # Extract skill name from path or use provided name
    if skill_name is None:
        skill_name = parts[-1] if len(parts) > 2 else repo_path.split("/")[-1]
    
    # Construct raw content URL for SKILL.md
    # For now, assume standard GitHub structure
    owner = parts[0]
    repo = parts[1] if len(parts) > 2 else parts[1]
    
    # Try to download SKILL.md from multiple possible locations
    possible_paths = [
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/SKILL.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/master/SKILL.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/skill-name/SKILL.md",
    ]
    
    skill_content = None
    for url in possible_paths:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                skill_content = response.text
                break
        except requests.RequestException:
            continue
    
    if skill_content is None:
        raise InstallationError(f"Could not find SKILL.md in repository {repo_path}")
    
    # Parse and validate the skill
    try:
        metadata, body = parse_skill_file(skill_content)
    except Exception as e:
        raise InstallationError(f"Invalid SKILL.md format: {e}")
    
    # Determine installation path
    skills_dir = Path.home() / ".agents" / "skills"
    install_path = skills_dir / skill_name
    
    # Create directory and save SKILL.md
    install_path.mkdir(parents=True, exist_ok=True)
    
    # Write full content (frontmatter + body)
    full_content = f"---\nname: {metadata.name}\ndescription: {metadata.description}"
    if metadata.license:
        full_content += f"\nlicense: {metadata.license}"
    if metadata.compatibility:
        full_content += f"\ncompatibility: {metadata.compatibility}"
    if metadata.metadata:
        full_content += f"\n{metadata.metadata}"
    full_content += f"\n---\n\n{body}"
    
    (install_path / "SKILL.md").write_text(full_content, encoding="utf-8")
    
    console.print(f"[green]✓ Successfully installed skill '{skill_name}'[/green]")
    
    return Skill(metadata=metadata, content=full_content, path=install_path / "SKILL.md")


def install_from_local(source_path: str, skill_name: Optional[str] = None) -> Skill:
    """Install a skill from a local directory path.
    
    Args:
        source_path: Local path to the skill directory
        skill_name: Optional custom name for the installed skill
        
    Returns:
        Installed Skill object
        
    Raises:
        InstallationError: If installation fails
    """
    source = Path(source_path).expanduser().resolve()
    
    if not source.exists():
        raise InstallationError(f"Skill directory not found: {source}")
    
    if not source.is_dir():
        raise InstallationError(f"Source is not a directory: {source}")
    
    # Find SKILL.md in source
    skill_md = source / "SKILL.md"
    if not skill_md.exists():
        raise InstallationError(f"SKILL.md not found in {source}")
    
    # Parse and validate
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
        metadata, body = parse_skill_file(content)
    except Exception as e:
        raise InstallationError(f"Invalid SKILL.md format: {e}")
    
    # Determine installation path
    skills_dir = Path.home() / ".agents" / "skills"
    target_name = skill_name or metadata.name
    install_path = skills_dir / target_name
    
    # Copy directory contents
    console.print(f"[yellow]Installing skill '{target_name}'...[/yellow]")
    
    # Copy all files except SKILL.md (we'll rewrite it)
    for item in source.iterdir():
        if item.name == "SKILL.md":
            continue
        dest = install_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    
    # Write SKILL.md
    full_content = f"---\nname: {metadata.name}\ndescription: {metadata.description}"
    if metadata.license:
        full_content += f"\nlicense: {metadata.license}"
    if metadata.compatibility:
        full_content += f"\ncompatibility: {metadata.compatibility}"
    if metadata.metadata:
        full_content += f"\n{metadata.metadata}"
    full_content += f"\n---\n\n{body}"
    
    install_path.mkdir(parents=True, exist_ok=True)
    (install_path / "SKILL.md").write_text(full_content, encoding="utf-8")
    
    console.print(f"[green]✓ Successfully installed skill '{target_name}'[/green]")
    
    return Skill(metadata=metadata, content=full_content, path=install_path / "SKILL.md")


def install_from_url(url: str, skill_name: Optional[str] = None) -> Skill:
    """Install a skill from a direct URL to SKILL.md.
    
    Args:
        url: Direct URL to the SKILL.md file
        skill_name: Optional custom name for the installed skill
        
    Returns:
        Installed Skill object
        
    Raises:
        InstallationError: If installation fails
    """
    console.print(f"[yellow]Downloading skill from {url}...[/yellow]")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        skill_content = response.text
    except requests.RequestException as e:
        raise InstallationError(f"Failed to download skill from URL: {e}")
    
    # Parse and validate
    try:
        metadata, body = parse_skill_file(skill_content)
    except Exception as e:
        raise InstallationError(f"Invalid SKILL.md format: {e}")
    
    # Determine installation path
    skills_dir = Path.home() / ".agents" / "skills"
    target_name = skill_name or metadata.name
    install_path = skills_dir / target_name
    
    # Create directory and save SKILL.md
    install_path.mkdir(parents=True, exist_ok=True)
    
    full_content = f"---\nname: {metadata.name}\ndescription: {metadata.description}"
    if metadata.license:
        full_content += f"\nlicense: {metadata.license}"
    if metadata.compatibility:
        full_content += f"\ncompatibility: {metadata.compatibility}"
    if metadata.metadata:
        full_content += f"\n{metadata.metadata}"
    full_content += f"\n---\n\n{body}"
    
    (install_path / "SKILL.md").write_text(full_content, encoding="utf-8")
    
    console.print(f"[green]✓ Successfully installed skill '{target_name}'[/green]")
    
    return Skill(metadata=metadata, content=full_content, path=install_path / "SKILL.md")
