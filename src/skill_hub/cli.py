"""Command-line interface for skill-hub."""

from pathlib import Path

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
def list_skills(verbose: bool) -> None:
    """List all skills in ~/.agents/skills."""
    skills_path = Path(expand_home("~/.agents/skills"))

    if not skills_path.exists():
        console.print(f"[yellow]Skills directory not found:[/yellow] {skills_path}")
        console.print("\nCreate it with: mkdir -p ~/.agents/skills")
        return

    engine = DiscoveryEngine(skills_path)
    skills = engine.discover_skills()

    if not skills:
        console.print("[yellow]No skills found in ~/.agents/skills[/yellow]")
        return

    console.print(f"[bold]Skills in ~/.agents/skills ({len(skills)}):[/bold]\n")

    if verbose:
        for skill in skills:
            console.print(f"[bold]{skill.name}[/bold]")
            console.print(f"  Description: {skill.description}")
            console.print(f"  Path: {skill.path}")
            if skill.metadata.license:
                console.print(f"  License: {skill.metadata.license}")
            if skill.metadata.compatibility:
                console.print(f"  Compatibility: {skill.metadata.compatibility}")
            console.print()
    else:
        table = Table(show_header=True)
        table.add_column("Skill Name")
        table.add_column("Description")

        for skill in skills:
            desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
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
def install_skill(source: str, skill_name: str) -> None:
    """Install a skill from GitHub, local path, or URL."""
    # Import installer after CLI definition to avoid circular imports
    from skill_hub.installer import install_from_github, install_from_local, install_from_url
    
    console.print(f"[yellow]Installing skill from {source}...[/yellow]")
    
    # Determine installation method based on source format
    if source.startswith(("http://", "https://")):
        # URL installation
        skill = install_from_url(source, skill_name)
    elif source.startswith("/") or source.startswith("~/") or source.startswith("./"):
        # Local path installation
        skill = install_from_local(source, skill_name)
    else:
        # Assume GitHub repository format (user/repo/skill-name)
        skill = install_from_github(source, skill_name)
    
    console.print(f"[green]✓ Skill '{skill.name}' installed successfully![/green]")


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
