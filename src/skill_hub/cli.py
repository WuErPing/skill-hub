"""Command-line interface for skill-hub."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from skill_hub import __version__
from skill_hub.discovery import DiscoveryEngine
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
