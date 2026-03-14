"""Skill comparison module for comparing local and global skills."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from skill_hub.discovery import DiscoveryEngine
from skill_hub.discovery.engine import discover_local_skills_dirs


@dataclass
class SkillComparison:
    """Comparison result for a single skill."""

    name: str
    local_version: Optional[str] = None
    global_version: Optional[str] = None
    status: str = "unknown"  # missing, local-only, global-only, up-to-date, update-available
    local_source: Optional[str] = None  # Tool name (e.g., 'opencode', 'agents')

    @property
    def needs_update(self) -> bool:
        """Check if skill needs update."""
        return self.status == "update-available"

    @property
    def sort_key(self) -> tuple:
        """Return sort key for ordering: Local Only first, then shared, then Global Only."""
        status_order = {
            "local-only": 0,
            "update-available": 1,
            "up-to-date": 2,
            "global-only": 3,
        }
        return (status_order.get(self.status, 4), self.name.lower())


@dataclass
class ComparisonResult:
    """Complete comparison result."""
    
    local_path: Path
    global_path: Path
    skills: Dict[str, SkillComparison] = field(default_factory=dict)
    
    @property
    def missing(self) -> List[SkillComparison]:
        """Skills in global but not local."""
        return [s for s in self.skills.values() if s.status == "missing"]
    
    @property
    def local_only(self) -> List[SkillComparison]:
        """Skills only in local."""
        return [s for s in self.skills.values() if s.status == "local-only"]
    
    @property
    def global_only(self) -> List[SkillComparison]:
        """Skills only in global."""
        return [s for s in self.skills.values() if s.status == "global-only"]
    
    @property
    def up_to_date(self) -> List[SkillComparison]:
        """Skills with same version."""
        return [s for s in self.skills.values() if s.status == "up-to-date"]
    
    @property
    def needs_update(self) -> List[SkillComparison]:
        """Skills that need update."""
        return [s for s in self.skills.values() if s.status == "update-available"]
    
    @property
    def total(self) -> int:
        """Total skills compared."""
        return len(self.skills)
    
    @property
    def local_count(self) -> int:
        """Count of local skills."""
        return len([s for s in self.skills.values() if s.status != "global-only"])
    
    @property
    def global_count(self) -> int:
        """Count of global skills."""
        return len([s for s in self.skills.values() if s.status != "local-only"])


def parse_skill_version(skill_path: Path) -> Optional[str]:
    """Parse version from a skill's SKILL.md file.
    
    Args:
        skill_path: Path to the skill directory
        
    Returns:
        Version string or None if not found
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None
    
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
        
        import re
        # Look for version in frontmatter
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            
            # Try metadata.version first
            meta_match = re.search(r"metadata:\s*\n((?:\s+.*\n)*)", frontmatter)
            if meta_match:
                metadata_block = meta_match.group(1)
                version_match = re.search(r"version:\s*([^\n]+)", metadata_block)
                if version_match:
                    return version_match.group(1).strip()
            
            # Try direct version field
            version_match = re.search(r"version:\s*([^\n]+)", frontmatter)
            if version_match:
                return version_match.group(1).strip()
    except Exception:
        pass
    
    return None


def discover_local_skills() -> Path:
    """Discover local project skills directory.
    
    Returns:
        Path to local skills directory
    """
    # Check .opencode/skills first (project-local)
    opencode_skills = Path(".opencode/skills")
    if opencode_skills.exists():
        return opencode_skills
    
    # Check .agents/skills in project
    project_agents = Path(".agents/skills")
    if project_agents.exists():
        return project_agents
    
    # Default to opencode
    return opencode_skills


def discover_global_skills() -> Path:
    """Discover global skills directory.
    
    Returns:
        Path to global skills directory (~/.agents/skills)
    """
    return Path.home() / ".agents" / "skills"


def compare_skills(
    local_path: Optional[Path] = None,
    global_path: Optional[Path] = None
) -> ComparisonResult:
    """Compare local and global skills.
    
    When local_path is not specified, discovers and aggregates skills from ALL
    local skill directories (.opencode/skills, .agents/skills, etc.).
    
    Args:
        local_path: Path to local skills directory (default: auto-discover all)
        global_path: Path to global skills directory (default: ~/.agents/skills)
        
    Returns:
        ComparisonResult with all comparison data
    """
    if global_path is None:
        global_path = discover_global_skills()
    
    # Discover global skills
    global_engine = DiscoveryEngine(global_path)
    global_skills = global_engine.discover_skills()
    global_skill_map = {s.name: s for s in global_skills}
    
    # Determine local skill sources
    if local_path is None:
        # Discover all local skill directories
        local_dirs = discover_local_skills_dirs(Path.cwd())
        if not local_dirs:
            # Fallback to legacy behavior if no dirs found
            local_path = discover_local_skills()
            local_dirs = [(local_path, "local")]
    else:
        local_dirs = [(local_path, "local")]
    
    # Aggregate skills from all local sources with their source (tool name)
    all_local_skills: Dict[str, Tuple[Path, str]] = {}

    for skills_dir, tool_name in local_dirs:
        if not skills_dir.exists():
            continue

        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()

        for skill in skills:
            if skill.name not in all_local_skills:
                all_local_skills[skill.name] = (skill.path.parent, tool_name)

    # Build comparison
    all_skill_names = set(all_local_skills.keys()) | set(global_skill_map.keys())
    skills_comparison: Dict[str, SkillComparison] = {}

    for name in all_skill_names:
        comparison = SkillComparison(name=name)

        if name in all_local_skills:
            local_path, tool_name = all_local_skills[name]
            comparison.local_version = parse_skill_version(local_path)
            comparison.local_source = tool_name

            global_skill = global_skill_map.get(name)
            if global_skill:
                comparison.global_version = parse_skill_version(global_skill.path.parent)
                if comparison.local_version == comparison.global_version:
                    comparison.status = "up-to-date"
                else:
                    comparison.status = "update-available"
            else:
                comparison.status = "local-only"
        else:
            global_skill = global_skill_map.get(name)
            if global_skill:
                comparison.global_version = parse_skill_version(global_skill.path.parent)
            comparison.status = "global-only"
        
        skills_comparison[name] = comparison
    
    return ComparisonResult(
        local_path=local_dirs[0][0] if local_dirs else Path.cwd(),
        global_path=global_path,
        skills=skills_comparison
    )


def discover_and_compare_all_locals(
    base_path: Optional[Path] = None,
    global_path: Optional[Path] = None
) -> Tuple[Dict[str, ComparisonResult], ComparisonResult]:
    """Discover all local skill directories and compare each with global.
    
    This function finds all .*/skills directories and compares skills from
    each one against the global skills directory.
    
    Args:
        base_path: Base directory to search for local skills (default: current dir)
        global_path: Path to global skills directory (default: ~/.agents/skills)
        
    Returns:
        Tuple of (tool_results, aggregated_result)
        - tool_results: Dict mapping tool_name to ComparisonResult for each local source
        - aggregated_result: ComparisonResult aggregating all local sources vs global
    """
    if base_path is None:
        base_path = Path.cwd()
    
    if global_path is None:
        global_path = discover_global_skills()
    
    # Discover global skills once
    global_engine = DiscoveryEngine(global_path)
    global_skills = global_engine.discover_skills()
    global_skill_map = {s.name: s for s in global_skills}
    
    # Find all local skill directories
    local_dirs = discover_local_skills_dirs(base_path)
    
    # Compare each tool's skills
    tool_results: Dict[str, ComparisonResult] = {}
    all_local_skills: Dict[str, Tuple[Path, str]] = {}  # name -> (path, tool_name)
    
    for skills_dir, tool_name in local_dirs:
        if not skills_dir.exists():
            continue
            
        # Discover skills for this tool
        engine = DiscoveryEngine(skills_dir)
        skills = engine.discover_skills()
        
        # Build comparison
        skill_map = {s.name: s for s in skills}
        all_names = set(skill_map.keys()) | set(global_skill_map.keys())
        comparisons: Dict[str, SkillComparison] = {}
        
        for name in all_names:
            local_skill = skill_map.get(name)
            global_skill = global_skill_map.get(name)
            
            comparison = SkillComparison(name=name)
            
            if local_skill and not global_skill:
                comparison.status = "local-only"
                comparison.local_version = parse_skill_version(local_skill.path.parent)
                comparison.local_source = tool_name
                all_local_skills[name] = (local_skill.path.parent, tool_name)
            elif global_skill and not local_skill:
                comparison.status = "global-only"
                comparison.global_version = parse_skill_version(global_skill.path.parent)
            elif local_skill and global_skill:
                comparison.local_version = parse_skill_version(local_skill.path.parent)
                comparison.global_version = parse_skill_version(global_skill.path.parent)
                comparison.local_source = tool_name
                if comparison.local_version == comparison.global_version:
                    comparison.status = "up-to-date"
                else:
                    comparison.status = "update-available"
                all_local_skills[name] = (local_skill.path.parent, tool_name)
            
            comparisons[name] = comparison
        
        tool_results[tool_name] = ComparisonResult(
            local_path=skills_dir,
            global_path=global_path,
            skills=comparisons
        )
    
    # Build aggregated comparison across all local sources
    all_names = set(all_local_skills.keys()) | set(global_skill_map.keys())
    aggregated_comparisons: Dict[str, SkillComparison] = {}
    
    for name in all_names:
        comparison = SkillComparison(name=name)
        
        if name in all_local_skills:
            local_path, tool_name = all_local_skills[name]
            comparison.local_version = parse_skill_version(local_path)
            comparison.local_source = tool_name
            
            global_skill = global_skill_map.get(name)
            if global_skill:
                comparison.global_version = parse_skill_version(global_skill.path.parent)
                if comparison.local_version == comparison.global_version:
                    comparison.status = "up-to-date"
                else:
                    comparison.status = "update-available"
            else:
                comparison.status = "local-only"
        else:
            global_skill = global_skill_map.get(name)
            if global_skill:
                comparison.global_version = parse_skill_version(global_skill.path.parent)
            comparison.status = "global-only"
        
        aggregated_comparisons[name] = comparison
    
    aggregated_result = ComparisonResult(
        local_path=base_path,
        global_path=global_path,
        skills=aggregated_comparisons
    )
    
    return tool_results, aggregated_result


def format_comparison_result(result: ComparisonResult) -> str:
    """Format comparison result as a table.
    
    Args:
        result: ComparisonResult to format
        
    Returns:
        Formatted string table
    """
    from rich.table import Table
    from rich.console import Console
    
    console = Console()
    
    # Create table with Source column
    table = Table(title="Skill Comparison")
    table.add_column("Skill Name", style="cyan")
    table.add_column("Source", style="dim")
    table.add_column("Local Version", style="green")
    table.add_column("Global Version", style="blue")
    table.add_column("Status", style="magenta")
    
    # Sort skills: Local Only first, then shared (up-to-date/update-available), then Global Only
    sorted_skills = sorted(result.skills.values(), key=lambda s: s.sort_key)
    
    # Add rows for each skill
    for comparison in sorted_skills:
        local_ver = comparison.local_version or "-"
        global_ver = comparison.global_version or "-"
        source = comparison.local_source or "-"
        
        # Color status based on type
        if comparison.status == "local-only":
            status = "Local Only"
            status_style = "yellow"
        elif comparison.status == "global-only":
            status = "Global Only"
            status_style = "yellow"
        elif comparison.status == "up-to-date":
            status = "Up to Date"
            status_style = "green"
        elif comparison.status == "update-available":
            status = f"Update Available ({global_ver})"
            status_style = "red"
        else:
            status = comparison.status
            status_style = "white"
        
        table.add_row(
            comparison.name,
            source,
            local_ver,
            global_ver,
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    # Print summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Local skills: {result.local_count}")
    console.print(f"  Global skills: {result.global_count}")
    console.print(f"  Up to date: {len(result.up_to_date)}")
    console.print(f"  Needs update: {len(result.needs_update)}")
    console.print(f"  Local only: {len(result.local_only)}")
    console.print(f"  Global only: {len(result.global_only)}")
    
    # Print table
    console.print("\n")
    console.print(table)
    
    return ""
