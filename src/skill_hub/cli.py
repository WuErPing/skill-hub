"""Command-line interface for skill-hub."""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from skill_hub import __version__
from skill_hub.adapters import AdapterRegistry
from skill_hub.discovery import DiscoveryEngine
from skill_hub.models import Config, RepositoryConfig
from skill_hub.remote import RepositoryManager, RepositorySkillScanner
from skill_hub.sync import SyncEngine
from skill_hub.utils import ConfigManager
from skill_hub.web import create_app  # Flask app (legacy web UI)

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
    
    # Load configuration from file
    config_manager = ConfigManager()
    ctx.obj["config_manager"] = config_manager
    # Use silent=True for most commands to avoid noise, commands will check config_manager.exists() if needed
    ctx.obj["config"] = config_manager.load(silent=True)


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host for web UI")
@click.option("--port", default=8501, show_default=True, type=int, help="Port for web UI")
@click.option(
    "--backend",
    type=click.Choice(["fastapi", "streamlit", "flask"]),
    default="fastapi",
    show_default=True,
    help="Web backend to use",
)
@click.pass_context
def web(ctx: click.Context, host: str, port: int, backend: str) -> None:
    """Start the skill-hub web interface (FastAPI/Streamlit/Flask)."""
    if backend == "flask":
        app = create_app()
        console.print(
            f"[bold]Starting Flask web UI at[/bold] http://{host}:{port}\n" "Press CTRL+C to stop."
        )
        app.run(host=host, port=port, debug=ctx.obj["verbose"])
        return

    if backend == "streamlit":
        console.print(
            f"[bold]Starting Streamlit web UI at[/bold] http://{host}:{port}\n" "Press CTRL+C to stop."
        )
        app_path = Path(__file__).with_name("web") / "streamlit_app.py"
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.address",
            host,
            "--server.port",
            str(port),
        ]
        subprocess.run(cmd)
        return

    # Default: FastAPI-based UI
    console.print(
        f"[bold]Starting FastAPI web UI at[/bold] http://{host}:{port}\n" "Press CTRL+C to stop."
    )
    from skill_hub.web.fastapi_app import create_app as create_fastapi_app
    import uvicorn

    app = create_fastapi_app()
    uvicorn.run(app, host=host, port=port, log_level="info" if ctx.obj["verbose"] else "warning")


@cli.command()
@click.option("--with-anthropic", is_flag=True, help="Add Anthropic skills repository")
@click.option("--repo", "-r", multiple=True, help="Add custom repository URL")
@click.pass_context
def init(ctx: click.Context, with_anthropic: bool, repo: tuple) -> None:
    """Initialize skill-hub configuration."""
    config = ctx.obj["config"]
    config_manager = ctx.obj["config_manager"]
    repo_manager = RepositoryManager()

    console.print("[bold]Initializing skill-hub configuration...[/bold]\n")

    # Check if already configured
    if config.repositories:
        console.print(f"[yellow]Configuration already exists with {len(config.repositories)} repositories[/yellow]")
        if not click.confirm("Do you want to add more repositories?", default=True):
            console.print("\nRun 'skill-hub repo list' to view configured repositories")
            return
        console.print()

    added_count = 0

    # Add Anthropic skills if requested
    if with_anthropic:
        anthropic_url = "https://github.com/anthropics/skills"
        if not any(r.url == anthropic_url for r in config.repositories):
            config.repositories.append(RepositoryConfig(url=anthropic_url))
            console.print(f"[green]✓[/green] Added: {anthropic_url}")
            added_count += 1
        else:
            console.print(f"[dim]Already configured: {anthropic_url}[/dim]")

    # Add custom repositories
    for repo_url in repo:
        if not repo_manager.validate_url(repo_url):
            console.print(f"[red]✗ Invalid URL:[/red] {repo_url}")
            continue

        if any(r.url == repo_url for r in config.repositories):
            console.print(f"[dim]Already configured: {repo_url}[/dim]")
            continue

        config.repositories.append(RepositoryConfig(url=repo_url))
        console.print(f"[green]✓[/green] Added: {repo_url}")
        added_count += 1

    # Interactive mode if no flags provided
    if not with_anthropic and not repo:
        console.print("[bold]Quick Setup:[/bold]\n")
        
        # Ask about Anthropic skills
        if click.confirm("Add Anthropic's community skills repository?", default=True):
            anthropic_url = "https://github.com/anthropics/skills"
            if not any(r.url == anthropic_url for r in config.repositories):
                config.repositories.append(RepositoryConfig(url=anthropic_url))
                console.print(f"  [green]✓[/green] Added: {anthropic_url}")
                added_count += 1

        console.print()
        
        # Ask about custom repositories
        if click.confirm("Add custom repository?", default=False):
            while True:
                repo_url = click.prompt("  Repository URL", type=str)
                
                if not repo_manager.validate_url(repo_url):
                    console.print(f"    [red]✗ Invalid URL format[/red]")
                    continue

                if any(r.url == repo_url for r in config.repositories):
                    console.print(f"    [yellow]Already configured[/yellow]")
                else:
                    config.repositories.append(RepositoryConfig(url=repo_url))
                    console.print(f"    [green]✓[/green] Added")
                    added_count += 1

                if not click.confirm("  Add another?", default=False):
                    break
            console.print()

    # Save configuration
    if added_count > 0:
        if config_manager.save(config):
            console.print(f"\n[bold green]✓[/bold green] Configuration saved to {config_manager.config_path}")
            console.print(f"  {added_count} repository(ies) configured\n")
            
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Run: [cyan]skill-hub pull[/cyan] to fetch skills")
            console.print("  2. Run: [cyan]skill-hub sync[/cyan] to distribute to agents")
        else:
            console.print("\n[red]Failed to save configuration[/red]")
    else:
        console.print("\n[yellow]No repositories added[/yellow]")
        console.print("\nAdd repositories with: skill-hub repo add <url>")


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


@cli.group(name="repo")
@click.pass_context
def repo(ctx: click.Context) -> None:
    """Manage remote skill repositories."""
    pass


@repo.command(name="add")
@click.argument("url")
@click.option("--branch", default="main", help="Git branch (default: main)")
@click.option("--path", default="", help="Subdirectory path in repository")
@click.pass_context
def repo_add(ctx: click.Context, url: str, branch: str, path: str) -> None:
    """Add a remote repository."""
    config = ctx.obj["config"]
    config_manager = ctx.obj["config_manager"]
    repo_manager = RepositoryManager()

    # Validate URL
    if not repo_manager.validate_url(url):
        console.print(f"[red]Invalid repository URL:[/red] {url}")
        return

    # Check if already exists
    for repo in config.repositories:
        if repo.url == url:
            console.print(f"[yellow]Repository already configured:[/yellow] {url}")
            return

    # Add to config
    repo_config = RepositoryConfig(url=url, branch=branch, path=path)
    config.repositories.append(repo_config)
    
    # Save configuration
    if not config_manager.save(config):
        console.print("[red]Failed to save configuration[/red]")
        return

    console.print(f"[green]✓[/green] Added repository: {url}")
    console.print(f"  Branch: {branch}")
    if path:
        console.print(f"  Path: {path}")
    console.print("\n[bold]Run 'skill-hub pull' to fetch skills[/bold]")


@repo.command(name="list")
@click.pass_context
def repo_list(ctx: click.Context) -> None:
    """List configured repositories."""
    config = ctx.obj["config"]
    config_manager = ctx.obj["config_manager"]
    repo_manager = RepositoryManager()

    if not config.repositories:
        if not config_manager.exists():
            console.print("[yellow]No configuration found[/yellow]\n")
            console.print("Get started with: [cyan]skill-hub init[/cyan]")
        else:
            console.print("[yellow]No repositories configured[/yellow]\n")
            console.print("Add a repository with: [cyan]skill-hub repo add <url>[/cyan]")
            console.print("Or run: [cyan]skill-hub init[/cyan] for interactive setup")
        return

    console.print(f"[bold]Configured repositories ({len(config.repositories)}):[/bold]\n")

    table = Table(show_header=True)
    table.add_column("URL")
    table.add_column("Branch")
    table.add_column("Enabled")
    table.add_column("Status")

    for repo in config.repositories:
        enabled = "✓" if repo.enabled else "✗"
        metadata = repo_manager.load_metadata(repo.url)

        if metadata and metadata.last_sync_at:
            status = f"Synced {metadata.sync_count} times"
        else:
            status = "Not synced yet"

        table.add_row(repo.url, repo.branch, enabled, status)

    console.print(table)


@repo.command(name="remove")
@click.argument("url")
@click.pass_context
def repo_remove(ctx: click.Context, url: str) -> None:
    """Remove a repository."""
    config = ctx.obj["config"]
    config_manager = ctx.obj["config_manager"]

    # Find and remove
    for i, repo in enumerate(config.repositories):
        if repo.url == url:
            config.repositories.pop(i)
            
            # Save configuration
            if not config_manager.save(config):
                console.print("[red]Failed to save configuration[/red]")
                return
                
            console.print(f"[green]✓[/green] Removed repository: {url}")
            return

    console.print(f"[yellow]Repository not found:[/yellow] {url}")


@cli.command()
@click.argument("url", required=False)
@click.pass_context
def pull(ctx: click.Context, url: Optional[str]) -> None:
    """Pull skills from remote repositories."""
    config = ctx.obj["config"]
    config_manager = ctx.obj["config_manager"]
    repo_manager = RepositoryManager()
    scanner = RepositorySkillScanner()
    sync_engine = SyncEngine(config)

    # Check if configuration exists
    if not config_manager.exists() and not config.repositories:
        console.print("[yellow]No configuration found[/yellow]\n")
        console.print("Initialize skill-hub with: [cyan]skill-hub init[/cyan]")
        console.print("\nExample:")
        console.print("  skill-hub init --with-anthropic")
        return

    # Determine which repositories to pull
    if url:
        repos = [r for r in config.repositories if r.url == url]
        if not repos:
            console.print(f"[red]Repository not configured:[/red] {url}")
            return
    else:
        repos = [r for r in config.repositories if r.enabled]

    if not repos:
        console.print("[yellow]No enabled repositories to pull from[/yellow]")
        console.print("\nAdd a repository with: skill-hub repo add <url>")
        return

    console.print("[bold]Pulling skills from remote repositories...[/bold]\n")

    total_skills = 0
    for repo_config in repos:
        console.print(f"📦 {repo_config.url}")

        # Clone or update repository
        if not repo_manager.clone_or_update(repo_config):
            console.print(f"  [red]✗ Failed to sync repository[/red]")
            continue

        # Get current commit hash
        commit_hash = repo_manager.get_commit_hash(repo_config.url)

        # Scan for skills
        repo_dir = repo_manager.get_repository_path(repo_config.url)
        scanned_skills = scanner.scan_repository(repo_dir, repo_config)

        if not scanned_skills:
            console.print(f"  [yellow]No skills found[/yellow]")
            continue

        # Convert to Skill objects
        skills = scanner.create_skill_objects(scanned_skills, repo_config.url)

        # Import skills to hub
        for skill in skills:
            try:
                sync_engine._sync_skill_to_hub(skill)
                total_skills += 1
            except Exception as e:
                console.print(f"  [red]✗ Failed to import '{skill.name}': {e}[/red]")

        # Save metadata
        from datetime import datetime
        from skill_hub.models import RepositoryMetadata

        metadata = RepositoryMetadata(
            url=repo_config.url,
            branch=repo_config.branch,
            commit_hash=commit_hash,
            last_sync_at=datetime.now().isoformat(),
            skills_imported=[s.name for s in skills],
            sync_count=(repo_manager.load_metadata(repo_config.url).sync_count + 1
                        if repo_manager.load_metadata(repo_config.url)
                        else 1),
        )
        repo_manager.save_metadata(metadata)

        console.print(f"  [green]✓ Imported {len(skills)} skills[/green]")

    console.print(f"\n[bold green]✓[/bold green] Pull completed: {total_skills} skills imported")


def main() -> None:
    """Main entry point."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
