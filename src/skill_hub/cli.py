"""Command-line interface for skill-hub."""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from skill_hub import __version__
from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config
from skill_hub.sync import SyncEngine

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """skill-hub: Unified skill management for AI coding agents."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = Config()


@cli.command()
@click.option("--pull", is_flag=True, help="Only pull skills from agents to hub")
@click.option("--push", is_flag=True, help="Only push skills from hub to agents")
@click.pass_context
def sync(ctx: click.Context, pull: bool, push: bool) -> None:
    """Synchronize skills between hub and agents."""
    config = ctx.obj["config"]
    sync_engine = SyncEngine(config)

    console.print("[bold]Starting skill synchronization...[/bold]")

    if pull:
        result = sync_engine.pull_from_agents()
    elif push:
        result = sync_engine.push_to_agents()
    else:
        result = sync_engine.sync()

    # Display results
    console.print(f"\n[bold green]✓[/bold green] Sync completed: {result.operation}")
    console.print(f"  • Skills synced: {result.skills_synced}")
    console.print(f"  • Skills skipped: {result.skills_skipped}")

    if result.conflicts_detected > 0:
        console.print(
            f"  [yellow]• Conflicts detected: {result.conflicts_detected}[/yellow]"
        )

    if result.errors:
        console.print(f"\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  • {error}")


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def discover(ctx: click.Context, output_json: bool) -> None:
    """Discover skills from all agent configurations."""
    config = ctx.obj["config"]
    adapter_registry = AdapterRegistry(config)
    discovery = DiscoveryEngine()

    console.print("[bold]Discovering skills...[/bold]")

    # Collect search paths
    search_paths = []
    for adapter in adapter_registry.get_enabled_adapters():
        for path in adapter.get_all_search_paths():
            search_paths.append((path, adapter.name))

    # Discover skills
    registry = discovery.discover_skills(search_paths)

    if output_json:
        print(json.dumps(registry.export_json(), indent=2))
    else:
        skills = registry.list_skills()
        console.print(f"\n[bold green]Found {len(skills)} skills:[/bold green]")

        table = Table(show_header=True)
        table.add_column("Skill Name")
        table.add_column("Description")
        table.add_column("Sources")

        for skill_name in skills:
            skill = registry.get_skill(skill_name)
            if skill:
                sources = ", ".join(set(src.agent for src in skill.sources))
                table.add_row(skill_name, skill.metadata.description[:60], sources)

        console.print(table)

        if registry.has_duplicates():
            console.print(
                f"\n[yellow]⚠ {len(registry.duplicates)} skills have conflicts[/yellow]"
            )


@cli.command(name="list")
@click.pass_context
def list_skills(ctx: click.Context) -> None:
    """List all skills in the hub."""
    config = ctx.obj["config"]
    sync_engine = SyncEngine(config)

    skills = sync_engine.list_hub_skills()

    if not skills:
        console.print("[yellow]No skills found in hub[/yellow]")
        return

    console.print(f"[bold]Skills in hub ({len(skills)}):[/bold]\n")
    for skill in skills:
        console.print(f"  • {skill}")


@cli.command()
@click.option("--check", is_flag=True, help="Run health checks")
@click.pass_context
def agents(ctx: click.Context, check: bool) -> None:
    """List available agent adapters."""
    config = ctx.obj["config"]
    adapter_registry = AdapterRegistry(config)

    if check:
        console.print("[bold]Running health checks...[/bold]\n")
        results = adapter_registry.health_check_all()

        table = Table(show_header=True)
        table.add_column("Agent")
        table.add_column("Enabled")
        table.add_column("Global Path")
        table.add_column("Status")

        for agent_name, health in results.items():
            enabled = "✓" if health["enabled"] else "✗"
            status = []
            if health["global_path_exists"]:
                status.append("exists")
            if health["global_path_writable"]:
                status.append("writable")

            status_str = ", ".join(status) if status else "not available"

            table.add_row(
                agent_name, enabled, health["global_path"], status_str
            )

        console.print(table)
    else:
        adapters = adapter_registry.list_adapters()
        console.print(f"[bold]Available adapters ({len(adapters)}):[/bold]\n")
        for adapter_name in adapters:
            adapter = adapter_registry.get_adapter(adapter_name)
            if adapter:
                status = "enabled" if adapter.is_enabled() else "disabled"
                console.print(f"  • {adapter_name} ({status})")


def main() -> None:
    """Main entry point."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
