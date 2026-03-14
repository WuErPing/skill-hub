"""Command-line interface for skill-hub."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from skill_hub import __version__
from skill_hub.comparison import compare_skills, format_comparison_result
from skill_hub.discovery import DiscoveryEngine
from skill_hub.discovery.engine import discover_all_local_skills
from skill_hub.utils import expand_home

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """skill-hub: View skills from ~/.agents/skills"""
    pass


@cli.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--all", "show_all", is_flag=True, help="Show skills from all directories")
@click.option("--public", "show_public", is_flag=True, help="Show only public skills")
@click.option("--private", "show_private", is_flag=True, help="Show only private skills")
def list_skills(verbose: bool, show_all: bool, show_public: bool, show_private: bool) -> None:
    """List all skills.
    
    Examples:
        # List public skills (default)
        skill-hub list
        
        # List all skills from all directories
        skill-hub list --all
        
        # List only private skills
        skill-hub list --private
    """
    from skill_hub.discovery.engine import discover_all_skill_directories, resolve_skill_priority
    
    # Determine which directories to show
    if show_all:
        dir_types = ["public", "project"]
    elif show_private:
        dir_types = ["project"]
    elif show_public:
        dir_types = ["public"]
    else:
        # Default: show public only
        dir_types = ["public"]
    
    # Discover all skill directories
    all_dirs = discover_all_skill_directories()
    
    # Filter by directory type
    filtered_dirs = [(path, tool, dtype) for path, tool, dtype in all_dirs if dtype in dir_types]
    
    if not filtered_dirs:
        console.print(f"[yellow]No {', '.join(dir_types)} skill directories found[/yellow]")
        return
    
    # Collect skills from all filtered directories
    all_skills = []
    for skills_path, tool_name, dir_type in filtered_dirs:
        if skills_path.exists():
            engine = DiscoveryEngine(skills_path, dir_type)
            skills = engine.discover_skills()
            all_skills.extend(skills)
    
    if not all_skills:
        console.print(f"[yellow]No skills found in {', '.join(dir_types)} directories[/yellow]")
        return
    
    # If showing all, resolve priority and show duplicates warning
    if show_all:
        skills_by_name = {}
        for skill in all_skills:
            if skill.name not in skills_by_name:
                skills_by_name[skill.name] = []
            skills_by_name[skill.name].append(skill)
        
        # Check for duplicates
        duplicates = {name: skills for name, skills in skills_by_name.items() if len(skills) > 1}
        if duplicates:
            console.print("[yellow]Note: Some skills exist in multiple directories (project takes priority):[/yellow]")
            for name, skills in duplicates.items():
                sources = [s.source_directory for s in skills]
                console.print(f"  - {name}: {', '.join(sources)}")
            console.print()
        
        # Use resolved skills for display
        resolved = resolve_skill_priority(skills_by_name)
        all_skills = list(resolved.values())
    
    # Display skills
    total_count = len(all_skills)
    dir_label = "all" if show_all else ", ".join(dir_types)
    console.print(f"[bold]Skills in {dir_label} directories ({total_count}):[/bold]\n")
    
    if verbose:
        for skill in all_skills:
            console.print(f"[bold]{skill.name}[/bold]")
            console.print(f"  Description: {skill.description}")
            console.print(f"  Path: {skill.path}")
            if skill.source_directory:
                console.print(f"  Source: {skill.source_directory}")
            if skill.metadata.license:
                console.print(f"  License: {skill.metadata.license}")
            if skill.metadata.compatibility:
                console.print(f"  Compatibility: {skill.metadata.compatibility}")
            console.print()
    else:
        table = Table(show_header=True)
        table.add_column("Skill Name")
        table.add_column("Description")
        if show_all or len(dir_types) > 1:
            table.add_column("Source")
        
        for skill in all_skills:
            desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
            if show_all or len(dir_types) > 1:
                source = skill.source_directory or "unknown"
                table.add_row(skill.name, desc, source)
            else:
                table.add_row(skill.name, desc)
        
        console.print(table)


@cli.command(name="list-local")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_local_skills(verbose: bool) -> None:
    """List all skills in local project directories (e.g., .opencode/skills, .agents/skills).

    This command discovers and lists skills from all hidden directories
    matching the pattern .*/skills in the current directory.

    Examples:

        # List all local skills
        skill-hub list-local

        # List with detailed information
        skill-hub list-local --verbose
    """
    from pathlib import Path

    local_skills = discover_all_local_skills()

    if not local_skills:
        console.print("[yellow]No local skill directories found[/yellow]")
        console.print("\nLooking for directories matching: .*/skills")
        console.print("Examples: .opencode/skills, .agents/skills, .claude/skills")
        return

    total_skills = sum(len(skills) for skills in local_skills.values())
    console.print(f"[bold]Local Skills ({total_skills} total):[/bold]\n")

    for tool_name, skills in sorted(local_skills.items()):
        console.print(f"[bold cyan]{tool_name}[/bold cyan] ({len(skills)} skills):")

        if verbose:
            for skill in skills:
                console.print(f"  [bold]{skill.name}[/bold]")
                console.print(f"    Description: {skill.description}")
                console.print(f"    Path: {skill.path}")
                if skill.metadata.license:
                    console.print(f"    License: {skill.metadata.license}")
                if skill.metadata.compatibility:
                    console.print(f"    Compatibility: {skill.metadata.compatibility}")
                console.print()
        else:
            table = Table(show_header=True)
            table.add_column("Skill Name")
            table.add_column("Description")

            for skill in skills:
                desc = skill.description[:50] + "..." if len(skill.description) > 50 else skill.description
                table.add_row(f"  {skill.name}", desc)

            console.print(table)
            console.print()


@cli.command()
@click.argument("skill_name")
def view(skill_name: str) -> None:
    """View a specific skill's content."""
    skills_path = Path(expand_home("~/.agents/skills"))

    if not skills_path.exists():
        console.print(f"[yellow]Skills directory not found:[/yellow] {skills_path}")
        return

    engine = DiscoveryEngine(skills_path)
    skills = engine.discover_skills()

    # Find the skill
    skill = next((s for s in skills if s.name == skill_name), None)

    if not skill:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        console.print("\nAvailable skills:")
        for s in skills:
            console.print(f"  • {s.name}")
        return

    console.print(f"[bold]{skill.name}[/bold]")
    console.print(f"[dim]Path: {skill.path}[/dim]\n")
    console.print(skill.content)


@cli.command()
def path() -> None:
    """Show the skills directory path."""
    skills_path = Path(expand_home("~/.agents/skills"))
    console.print(skills_path)

    if skills_path.exists():
        console.print("[green]✓ Directory exists[/green]")
    else:
        console.print("[yellow]✗ Directory does not exist[/yellow]")
        console.print("\nCreate it with:")
        console.print("  mkdir -p ~/.agents/skills")


@cli.command(name="compare")
@click.option(
    "--local",
    "local_path",
    default=None,
    help="Path to local skills directory (default: auto-discover)"
)
@click.option(
    "--global",
    "global_path",
    default=None,
    help="Path to global skills directory (default: ~/.agents/skills)"
)
@click.option(
    "--summary",
    is_flag=True,
    help="Show only summary (no detailed table)"
)
@click.option(
    "--all-locals",
    is_flag=True,
    help="Compare all local skill directories (.*/skills) against global"
)
def compare_skills_cmd(local_path: str, global_path: str, summary: bool, all_locals: bool) -> None:
    """Compare local project skills with global skills.
    
    This command compares skills in your local project (e.g., .opencode/skills)
    with global skills (~/.agents/skills) and shows:
    
    - Skills only in local (local-only)
    - Skills only in global (global-only)
    - Skills with version differences (update-available)
    - Skills up to date (up-to-date)
    
    Examples:
    
        # Compare local and global skills
        skill-hub compare
        
        # Compare all local directories (.opencode/skills, .agents/skills, etc.)
        skill-hub compare --all-locals
        
        # Show only summary
        skill-hub compare --summary
        
        # Specify custom paths
        skill-hub compare --local ./skills --global ~/.agents/skills
    """
    from skill_hub.comparison import discover_and_compare_all_locals
    
    # Convert global path
    global_p = Path(global_path) if global_path else None
    
    if all_locals:
        # Compare all local skill directories
        console.print("[bold]Comparing all local skill directories with global...[/bold]\n")
        
        try:
            tool_results, aggregated = discover_and_compare_all_locals(global_path=global_p)
            
            if not tool_results:
                console.print("[yellow]No local skill directories found[/yellow]")
                console.print("Looking for: .opencode/skills, .agents/skills, etc.")
                return
            
            # Show results per tool
            for tool_name, result in sorted(tool_results.items()):
                console.print(f"\n[bold cyan]{tool_name}[/bold cyan] skills:")
                console.print(f"  Local skills: {result.local_count}")
                console.print(f"  Global skills: {result.global_count}")
                console.print(f"  Up to date: {len(result.up_to_date)}")
                console.print(f"  Needs update: {len(result.needs_update)}")
                console.print(f"  Local only: {len(result.local_only)}")
                console.print(f"  Global only: {len(result.global_only)}")
                
                if not summary:
                    format_comparison_result(result)
            
            # Show aggregated summary
            console.print(f"\n[bold green]Overall Summary:[/bold green]")
            console.print(f"  Total local sources: {len(tool_results)}")
            console.print(f"  Total unique skills (local): {aggregated.local_count}")
            console.print(f"  Total global skills: {aggregated.global_count}")
            console.print(f"  Up to date: {len(aggregated.up_to_date)}")
            console.print(f"  Needs update: {len(aggregated.needs_update)}")
            
        except Exception as e:
            console.print(f"[red]✗ Comparison failed: {e}[/red]")
            raise click.Abort()
    else:
        # Original single-directory comparison
        local_p = Path(local_path) if local_path else None
        
        console.print("[bold]Comparing local and global skills...[/bold]\n")
        
        try:
            result = compare_skills(local_path=local_p, global_path=global_p)
            
            if summary:
                console.print(f"[bold]Summary:[/bold]")
                console.print(f"  Local skills: {result.local_count}")
                console.print(f"  Global skills: {result.global_count}")
                console.print(f"  Up to date: {len(result.up_to_date)}")
                console.print(f"  Needs update: {len(result.needs_update)}")
                console.print(f"  Local only: {len(result.local_only)}")
                console.print(f"  Global only: {len(result.global_only)}")
            else:
                format_comparison_result(result)
        
        except Exception as e:
            console.print(f"[red]✗ Comparison failed: {e}[/red]")
            raise click.Abort()


# New commands for skill lifecycle management

@cli.command(name="install")
@click.argument("source")
@click.option("--as", "skill_name", default=None, help="Custom name for the installed skill")
@click.option("--to", "target", default=None, help="Target directory (e.g., ~/.agents/skills, .claude/skills)")
def install_skill(source: str, skill_name: str, target: Optional[str]) -> None:
    """Install a skill from GitHub, local path, URL, or existing skill name.
    
    By default, installs to the local project directory (./.agents/skills/).
    Use --to to specify a different location.
    
    Examples:
        # Install to project-level directory (default)
        skill-hub install user/repo/skill-name
        
        # Install to global directory
        skill-hub install user/repo/skill-name --to ~/.agents/skills
        
        # Install to Claude-specific directory
        skill-hub install user/repo/skill-name --to .claude/skills
    """
    # Import installer after CLI definition to avoid circular imports
    from skill_hub.installer import install_from_github, install_from_local, install_from_url, get_install_path
    from skill_hub.discovery import DiscoveryEngine
    
    console.print(f"[yellow]Installing skill from {source}...[/yellow]")
    
    # Determine target path
    # Default: install to project-level (./.agents/skills/)
    # If --to is specified, use that path directly
    if target is None:
        target_path = Path.cwd() / ".agents" / "skills"
        target_label = "project"
    else:
        target_path = Path(target).expanduser().resolve()
        target_label = str(target_path)
    
    # Determine installation method based on source format
    if source.startswith(("http://", "https://")):
        # URL installation
        skill = install_from_url(source, skill_name, target_path)
    elif source.startswith("/") or source.startswith("~/") or source.startswith("./"):
        # Local path installation
        skill = install_from_local(source, skill_name, target_path)
    elif "/" in source:
        # Assume GitHub repository format (user/repo/skill-name)
        skill = install_from_github(source, skill_name, target_path)
    else:
        # Just a skill name - look it up in local skills directories
        from skill_hub.discovery.engine import discover_all_skill_directories
        skill_dirs = discover_all_skill_directories()
        
        # Search for skill in all discovered directories
        skill_to_copy = None
        for skills_path, tool_name, dir_type in skill_dirs:
            if skills_path.exists():
                engine = DiscoveryEngine(skills_path, dir_type)
                local_skills = engine.discover_skills()
                found_skill = next((s for s in local_skills if s.name == source), None)
                if found_skill:
                    skill_to_copy = found_skill
                    break
        
        if skill_to_copy:
            # Copy the existing skill to install it
            from skill_hub.installer import install_from_local
            skill = install_from_local(str(skill_to_copy.path.parent), skill_name, target_path)
        else:
            raise click.ClickException(
                f"Skill '{source}' not found locally. "
                f"Use 'skill-hub list' to see available skills, or install from GitHub/URL."
            )
    
    console.print(f"[green]✓ Skill '{skill.name}' installed successfully to {target} directory![/green]")


@cli.command(name="upgrade")
@click.argument("skill_name")
def upgrade_skill(skill_name: str) -> None:
    """Upgrade a skill to global format."""
    from skill_hub.upgrader import upgrade_skill as do_upgrade
    
    try:
        skill = do_upgrade(skill_name)
        console.print(f"[green]✓ Skill '{skill.name}' upgraded successfully![/green]")
    except Exception as e:
        console.print(f"[red]✗ Upgrade failed: {e}[/red]")
        raise click.Abort()


@cli.command(name="update")
@click.argument("skill_name", required=False)
def update_skill(skill_name: str) -> None:
    """Check for and apply skill updates."""
    from skill_hub.version import update_skill as do_update, check_update

    if skill_name:
        # Update specific skill
        success = do_update(skill_name)
        if not success:
            raise click.Abort()
    else:
        # Check all skills
        skills_path = Path(expand_home("~/.agents/skills"))

        if not skills_path.exists():
            console.print(f"[yellow]Skills directory not found:[/yellow] {skills_path}")
            return

        engine = DiscoveryEngine(skills_path)
        skills = engine.discover_skills()

        if not skills:
            console.print("[yellow]No skills found in ~/.agents/skills[/yellow]")
            return

        has_updates = False
        for skill in skills:
            has_update, current_version, latest_version = check_update(
                skill.name,
                skill.path.parent
            )

            if has_update:
                has_updates = True
                console.print(f"[yellow]Update available:[/yellow] {skill.name} ({current_version} → {latest_version})")
            else:
                console.print(f"[green]Up to date:[/green] {skill.name} ({current_version})")

        if not has_updates:
            console.print("[green]All skills are up to date![/green]")


@cli.command(name="sync")
@click.argument("skill_name")
@click.option("--from", "source", required=True, type=click.Choice(["public", "private"]), help="Source directory")
@click.option("--to", "target", required=True, type=click.Choice(["public", "private"]), help="Target directory")
@click.option("--force", is_flag=True, help="Force overwrite if skill already exists")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without making changes")
def sync_skill_cmd(skill_name: str, source: str, target: str, force: bool, dry_run: bool) -> None:
    """Sync a skill between public and project-level directories.

    Examples:
        # Sync from public to project-level
        skill-hub sync my-skill --from public --to private

        # Sync from project-level to public
        skill-hub sync my-skill --from private --to public

        # Dry run - show what would happen without making changes
        skill-hub sync my-skill --from public --to private --dry-run

        # Force overwrite existing skill
        skill-hub sync my-skill --from public --to private --force
    """
    from skill_hub.installer import sync_skill
    from skill_hub.discovery.engine import discover_all_skill_directories

    # Validate source != target
    if source == target:
        raise click.ClickException("Source and target directories must be different")
    
    # Map CLI 'private' to internal 'project' and determine paths
    if source == "public":
        source_path = Path.home() / ".agents" / "skills"
        source_internal = "public"
    else:
        source_path = Path.cwd() / ".agents" / "skills"
        source_internal = "project"
    
    if target == "public":
        target_path = Path.home() / ".agents" / "skills"
        target_internal = "public"
    else:
        target_path = Path.cwd() / ".agents" / "skills"
        target_internal = "project"

    console.print(f"[yellow]Syncing skill '{skill_name}' from {source} to {target}...[/yellow]")

    # Check if skill exists in source
    from skill_hub.discovery.engine import discover_all_skill_directories
    all_dirs = discover_all_skill_directories()
    source_dirs = [(p, t, dt) for p, t, dt in all_dirs if dt == source_internal]

    skill_found = None
    for skills_path, tool_name, dir_type in source_dirs:
        if skills_path.exists():
            engine = DiscoveryEngine(skills_path, dir_type)
            skills = engine.discover_skills()
            found = next((s for s in skills if s.name == skill_name), None)
            if found:
                skill_found = found
                break

    if not skill_found:
        raise click.ClickException(f"Skill '{skill_name}' not found in {source} directories")

    # Check if skill already exists in target
    existing_in_target = None
    if target_path.exists():
        engine = DiscoveryEngine(target_path, target_internal)
        skills = engine.discover_skills()
        existing_in_target = next((s for s in skills if s.name == skill_name), None)

    # Handle overwrite protection
    if existing_in_target and not force and not dry_run:
        console.print(f"[yellow]Warning: Skill '{skill_name}' already exists in {target} directory[/yellow]")
        if not click.confirm("Do you want to overwrite it?"):
            console.print("[dim]Sync cancelled.[/dim]")
            return

    # Perform sync
    try:
        skill = sync_skill(skill_found, target_path, dry_run=dry_run)
        if dry_run:
            console.print(f"[blue]Would sync '{skill_name}' from {source} to {target}[/blue]")
        else:
            console.print(f"[green]✓ Successfully synced '{skill_name}' from {source} to {target}![/green]")
    except Exception as e:
        console.print(f"[red]✗ Sync failed: {e}[/red]")
        raise click.Abort()


@cli.command(name="version")
@click.option("--check", is_flag=True, help="Check for available updates")
def show_version(check: bool) -> None:
    """Show version information.

    Examples:

        # Show current version
        skill-hub version

        # Check for updates
        skill-hub version --check
    """
    from skill_hub.version import compare_versions, get_latest_version

    console.print(f"skill-hub version [bold]{__version__}[/bold]")

    if check:
        console.print("Checking for updates...")
        latest = get_latest_version("wuerping/skill-hub")
        if latest:
            if compare_versions(__version__, latest) < 0:
                console.print(f"[yellow]Update available: {latest}[/yellow]")
                console.print("Upgrade with: pip install --upgrade skill-hub")
            else:
                console.print("[green]You're on the latest version![/green]")
        else:
            console.print("[dim]Could not check for updates[/dim]")


@cli.command(name="self-update")
def self_update() -> None:
    """Update skill-hub to the latest version.

    This command will upgrade skill-hub to the latest version from PyPI.
    """
    import subprocess

    console.print("Updating skill-hub...")
    try:
        subprocess.check_call(["pip", "install", "--upgrade", "skill-hub"])
        console.print("[green]✓ Updated successfully![/green]")
        console.print("Restart your terminal or run 'skill-hub --version' to see the new version.")
    except subprocess.CalledProcessError:
        console.print("[red]✗ Update failed.[/red]")
        console.print("Try manually: pip install --upgrade skill-hub")
        raise click.Abort()
