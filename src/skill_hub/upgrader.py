"""Skill upgrade module."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from skill_hub.models import Skill, SkillMetadata
from skill_hub.utils.yaml_parser import parse_skill_file

console = Console()


class UpgradeError(Exception):
    """Error during skill upgrade."""

    pass


def detect_config_format(skill_path: Path) -> str:
    """Detect the configuration format of a skill.
    
    Args:
        skill_path: Path to the skill directory
        
    Returns:
        Config format string (claude, opencode, cursor, etc.)
    """
    # Check for tool-specific config files
    if (skill_path / ".claude").exists():
        return "claude"
    if (skill_path / ".opencode").exists():
        return "opencode"
    if (skill_path / ".cursor").exists():
        return "cursor"
    
    # Check parent directory structure
    parent = skill_path.parent
    if ".claude" in str(parent):
        return "claude"
    if ".opencode" in str(parent):
        return "opencode"
    if ".cursor" in str(parent):
        return "cursor"
    
    # Default to agents format
    return "agents"


def convert_claude_to_agent(skill: Skill, dest_path: Path) -> Skill:
    """Convert a Claude skill to agent format.
    
    Args:
        skill: Source Skill object
        dest_path: Destination path for converted skill
        
    Returns:
        Converted Skill object
    """
    console.print(f"[yellow]Converting skill '{skill.name}' from Claude to agent format...[/yellow]")
    
    # Create destination directory
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from source
    for item in skill.path.parent.iterdir():
        if item.name == "SKILL.md":
            continue
        dest = dest_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    
    # Update SKILL.md with agent metadata
    metadata = skill.metadata
    full_content = f"---\nname: {metadata.name}\ndescription: {metadata.description}"
    if metadata.license:
        full_content += f"\nlicense: {metadata.license}"
    if metadata.compatibility:
        full_content += f"\ncompatibility: {metadata.compatibility}"
    if metadata.metadata:
        # Add version if present
        if metadata.version:
            full_content += f"\nversion: {metadata.version}"
        # Add updateUrl if present
        if metadata.updateUrl:
            full_content += f"\nupdateUrl: {metadata.updateUrl}"
        # Include other metadata
        for key, value in metadata.metadata.items():
            if key not in ("version", "updateUrl"):
                full_content += f"\n{key}: {value}"
    full_content += f"\n---\n\n{skill.content.split('---', 2)[-1].split('---', 2)[-1] if '---' in skill.content else ''}"
    
    # Re-parse to get clean content
    try:
        new_metadata, body = parse_skill_file(full_content)
    except Exception:
        # Fallback: just copy the content
        body = skill.content
    
    full_content = f"---\nname: {new_metadata.name}\ndescription: {new_metadata.description}"
    if new_metadata.license:
        full_content += f"\nlicense: {new_metadata.license}"
    if new_metadata.compatibility:
        full_content += f"\ncompatibility: {new_metadata.compatibility}"
    if new_metadata.metadata:
        if new_metadata.version:
            full_content += f"\nversion: {new_metadata.version}"
        if new_metadata.updateUrl:
            full_content += f"\nupdateUrl: {new_metadata.updateUrl}"
        for key, value in new_metadata.metadata.items():
            if key not in ("version", "updateUrl"):
                full_content += f"\n{key}: {value}"
    full_content += f"\n---\n\n{body}"
    
    (dest_path / "SKILL.md").write_text(full_content, encoding="utf-8")
    
    console.print(f"[green]✓ Converted skill '{skill.name}' to agent format[/green]")
    
    return Skill(
        metadata=new_metadata,
        content=full_content,
        path=dest_path / "SKILL.md"
    )


def backup_skill(skill: Skill) -> Path:
    """Create a backup of a skill.
    
    Args:
        skill: Skill to backup
        
    Returns:
        Path to backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{skill.name}-backup-{timestamp}"
    skills_dir = Path.home() / ".agents" / "skills"
    backup_path = skills_dir / "backup" / backup_name
    
    # Copy skill to backup location
    shutil.copytree(skill.path.parent, backup_path)
    
    console.print(f"[yellow]✓ Created backup at {backup_path}[/yellow]")
    
    return backup_path


def upgrade_skill(skill_name: str, dest_dir: Optional[Path] = None) -> Skill:
    """Upgrade a skill (convert to global format).
    
    Args:
        skill_name: Name of the skill to upgrade
        dest_dir: Optional destination directory (default: ~/.agents/skills)
        
    Returns:
        Upgraded Skill object
        
    Raises:
        UpgradeError: If upgrade fails
    """
    if dest_dir is None:
        dest_dir = Path.home() / ".agents" / "skills"
    
    # Find the skill
    skills_dir = Path.home() / ".agents" / "skills"
    source_path = skills_dir / skill_name
    
    if not source_path.exists():
        raise UpgradeError(f"Skill not found: {skill_name}")
    
    # Load skill
    skill_md = source_path / "SKILL.md"
    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        metadata, body = parse_skill_file(content)
    except Exception as e:
        raise UpgradeError(f"Invalid SKILL.md format: {e}")
    
    skill = Skill(metadata=metadata, content=content, path=skill_md)
    
    # Detect source format
    source_format = detect_config_format(source_path)
    console.print(f"[yellow]Detected source format: {source_format}[/yellow]")
    
    # Create backup before upgrade
    backup_path = backup_skill(skill)
    
    try:
        # Convert based on source format
        if source_format == "claude":
            converted_skill = convert_claude_to_agent(skill, dest_dir / skill_name)
        else:
            # Already in agents format or unknown format
            console.print(f"[green]✓ Skill '{skill_name}' already in agent format[/green]")
            converted_skill = skill
        
        return converted_skill
    except Exception as e:
        # Rollback on failure
        console.print(f"[red]✗ Upgrade failed, restoring backup...[/red]")
        shutil.rmtree(dest_dir / skill_name, ignore_errors=True)
        shutil.copytree(backup_path, dest_dir / skill_name)
        raise UpgradeError(f"Upgrade failed: {e}")
