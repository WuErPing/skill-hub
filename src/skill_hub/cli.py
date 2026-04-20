"""Command-line interface for skill-hub."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from skill_hub import __version__
from skill_hub.discovery import DiscoveryEngine
from skill_hub.discovery.engine import discover_all_skill_directories
from skill_hub.utils import expand_home

console = Console()

PUBLIC_PATH = Path.home() / ".agents" / "skills"


def _resolve_target_path(target: Optional[str]) -> Path:
    """Resolve --to option to an absolute Path.

    Accepts 'public', 'private', or an explicit filesystem path.
    Defaults to private (./.agents/skills) when target is None.
    """
    if target is None or target == "private":
        return Path.cwd() / ".agents" / "skills"
    if target == "public":
        return PUBLIC_PATH
    # Explicit path (starts with / or ~/)
    return Path(target).expanduser().resolve()


def _collect_skills(dir_types: list) -> list:
    """Collect skills from all discovered directories matching dir_types."""
    all_dirs = discover_all_skill_directories()
    skills = []
    for skills_path, _tool, dtype in all_dirs:
        if dtype in dir_types and skills_path.exists():
            engine = DiscoveryEngine(skills_path, dtype)
            skills.extend(engine.discover_skills())
    return skills


def _build_version_status_map(private_skills: list, public_skills: list) -> dict:
    """Return a dict mapping skill name -> status string for version comparison.

    Status values: 'private-only', 'public-only', 'up-to-date', 'out-of-sync'
    """
    private_map = {s.name: s for s in private_skills}
    public_map = {s.name: s for s in public_skills}
    result = {}
    all_names = set(private_map) | set(public_map)
    for name in all_names:
        priv = private_map.get(name)
        pub = public_map.get(name)
        if priv and not pub:
            result[name] = ("private-only", getattr(priv.metadata, "version", None))
        elif pub and not priv:
            result[name] = ("public-only", getattr(pub.metadata, "version", None))
        else:
            pv = getattr(priv.metadata, "version", None)
            gv = getattr(pub.metadata, "version", None)
            if pv == gv:
                result[name] = ("up-to-date", pv)
            else:
                result[name] = ("out-of-sync", (pv, gv))
    return result


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """skill-hub: manage skills from ~/.agents/skills"""
    pass


@cli.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--public", "show_public", is_flag=True, help="Show only public skills (~/.agents/skills)")
@click.option("--private", "show_private", is_flag=True, help="Show only private skills (./.agents/skills)")
@click.option("--diff", is_flag=True, help="Show diff between private and public skills")
def list_skills(verbose: bool, show_public: bool, show_private: bool, diff: bool) -> None:
    """List skills from public and/or private directories.

    By default shows all skills (public + private) with a Source column.

    Examples:

        skill-hub list
        skill-hub list --public
        skill-hub list --private
        skill-hub list --diff
    """
    if diff:
        from skill_hub.comparison import compare_skills, format_comparison_result
        try:
            result = compare_skills()
            format_comparison_result(result)
        except Exception as e:
            console.print(f"[red]✗ Diff failed: {e}[/red]")
            raise click.Abort()
        return

    show_all = not show_public and not show_private

    if show_public and show_private:
        dir_types = ["public", "project"]
    elif show_public:
        dir_types = ["public"]
    elif show_private:
        dir_types = ["project"]
    else:
        dir_types = ["public", "project"]

    all_skills = _collect_skills(dir_types)

    if not all_skills:
        console.print("[yellow]No skills found[/yellow]")
        return

    # Build version-status map when showing both scopes
    version_status: dict = {}
    if show_all or (show_public and show_private):
        private_skills = [s for s in all_skills if s.source_directory == "project"]
        public_skills = [s for s in all_skills if s.source_directory == "public"]
        version_status = _build_version_status_map(private_skills, public_skills)

    show_source = len(dir_types) > 1

    console.print(f"[bold]Skills ({len(all_skills)}):[/bold]\n")

    if verbose:
        for skill in all_skills:
            console.print(f"[bold]{skill.name}[/bold]")
            console.print(f"  Description: {skill.description}")
            console.print(f"  Path: {skill.path}")
            if show_source and skill.source_directory:
                console.print(f"  Source: {skill.source_directory}")
            if skill.metadata.version:
                console.print(f"  Version: {skill.metadata.version}")
            if skill.metadata.license:
                console.print(f"  License: {skill.metadata.license}")
            if skill.metadata.compatibility:
                console.print(f"  Compatibility: {skill.metadata.compatibility}")
            if version_status and skill.name in version_status:
                status, ver = version_status[skill.name]
                if status == "out-of-sync":
                    priv_v, pub_v = ver
                    console.print(f"  [yellow]⚠ Out of sync[/yellow] private={priv_v or '-'} public={pub_v or '-'}")
            console.print()
    else:
        table = Table(show_header=True)
        table.add_column("Skill Name")
        table.add_column("Description")
        if show_source:
            table.add_column("Source")
        if version_status:
            table.add_column("Version")
            table.add_column("Status")

        # Deduplicate: when showing all, show each skill once with its effective (private-priority) entry
        if show_all or (show_public and show_private):
            seen = set()
            display_skills = []
            for skill in all_skills:
                if skill.name not in seen:
                    seen.add(skill.name)
                    display_skills.append(skill)
        else:
            display_skills = all_skills

        for skill in display_skills:
            desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
            row = [skill.name, desc]
            if show_source:
                row.append(skill.source_directory or "unknown")
            if version_status:
                entry = version_status.get(skill.name)
                if entry:
                    status, ver = entry
                    if status == "up-to-date":
                        row.append(ver or "-")
                        row.append("[green]Up to date[/green]")
                    elif status == "out-of-sync":
                        priv_v, pub_v = ver
                        row.append(f"{priv_v or '-'} / {pub_v or '-'}")
                        row.append("[yellow]⚠ Out of sync[/yellow]")
                    elif status == "private-only":
                        row.append(ver or "-")
                        row.append("[dim]Private only[/dim]")
                    elif status == "public-only":
                        row.append(ver or "-")
                        row.append("[dim]Public only[/dim]")
                    else:
                        row.append("-")
                        row.append("-")
                else:
                    row.extend(["-", "-"])
            table.add_row(*row)

        console.print(table)


@cli.command()
@click.argument("skill_name")
def view(skill_name: str) -> None:
    """View a specific skill's content."""
    all_skills = _collect_skills(["public", "project"])
    skill = next((s for s in all_skills if s.name == skill_name), None)

    if not skill:
        console.print(f"[red]Skill not found:[/red] {skill_name}")
        console.print("\nAvailable skills:")
        for s in all_skills:
            console.print(f"  • {s.name}")
        return

    console.print(f"[bold]{skill.name}[/bold]")
    console.print(f"[dim]Path: {skill.path}[/dim]\n")
    console.print(skill.content)


@cli.command()
def path() -> None:
    """Show the public skills directory path."""
    console.print(PUBLIC_PATH)
    if PUBLIC_PATH.exists():
        console.print("[green]✓ Directory exists[/green]")
    else:
        console.print("[yellow]✗ Directory does not exist[/yellow]")
        console.print("\nCreate it with:")
        console.print("  mkdir -p ~/.agents/skills")


@cli.command(name="install")
@click.argument("source")
@click.option("--as", "skill_name", default=None, help="Custom name for the installed skill")
@click.option(
    "--to",
    "target",
    default=None,
    help="Target: 'public' (~/.agents/skills), 'private' (./.agents/skills, default), or an explicit path",
)
def install_skill(source: str, skill_name: str, target: Optional[str]) -> None:
    """Install a skill from a local path, GitHub, or URL.

    Installs to the private project directory by default.
    Use --to public to install to ~/.agents/skills.

    Examples:

        skill-hub install /path/to/my-skill
        skill-hub install /path/to/my-skill --to public
        skill-hub install user/repo/skill-name
        skill-hub install https://example.com/SKILL.md
    """
    from skill_hub.installer import install_from_github, install_from_local, install_from_url

    target_path = _resolve_target_path(target)
    console.print(f"[yellow]Installing skill from {source}...[/yellow]")

    if source.startswith(("http://", "https://")):
        skill = install_from_url(source, skill_name, target_path)
    elif source.startswith("/") or source.startswith("~/") or source.startswith("./"):
        skill = install_from_local(source, skill_name, target_path)
    elif "/" in source:
        skill = install_from_github(source, skill_name, target_path)
    else:
        # Bare skill name — search all known directories
        all_skills = _collect_skills(["public", "project"])
        found = next((s for s in all_skills if s.name == source), None)
        if found:
            skill = install_from_local(str(found.path.parent), skill_name, target_path)
        else:
            raise click.ClickException(
                f"Skill '{source}' not found locally. "
                "Use 'skill-hub list' to see available skills, or install from a path/GitHub/URL."
            )

    target_label = target or "private"
    console.print(f"[green]✓ Skill '{skill.name}' installed successfully to {target_label}![/green]")


@cli.command(name="sync")
@click.argument("skill_name")
@click.argument("from_dir", metavar="FROM", type=click.Choice(["public", "private"]))
@click.argument("to_dir", metavar="TO", type=click.Choice(["public", "private"]))
@click.option("--force", is_flag=True, help="Force overwrite if skill already exists")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without making changes")
def sync_skill_cmd(skill_name: str, from_dir: str, to_dir: str, force: bool, dry_run: bool) -> None:
    """Sync a skill between public and private directories.

    FROM and TO are positional: 'public' or 'private'.

    Examples:

        skill-hub sync git-commit-helper private public
        skill-hub sync git-commit-helper public private
        skill-hub sync .agents/skills/git-commit-helper private public --dry-run
    """
    from skill_hub.installer import sync_skill

    if from_dir == to_dir:
        raise click.ClickException("FROM and TO must be different")

    source_internal = "public" if from_dir == "public" else "project"
    target_internal = "public" if to_dir == "public" else "project"
    source_path = PUBLIC_PATH if from_dir == "public" else Path.cwd() / ".agents" / "skills"
    target_path = PUBLIC_PATH if to_dir == "public" else Path.cwd() / ".agents" / "skills"

    # Accept path-style argument: extract skill name and override source_path
    resolved_skill_name = Path(skill_name).name if "/" in skill_name else skill_name
    if "/" in skill_name:
        source_path = (Path.cwd() / skill_name).resolve().parent

    console.print(f"[yellow]Syncing '{resolved_skill_name}' from {from_dir} to {to_dir}...[/yellow]")

    # Find skill in source
    skill_found = None
    direct = source_path / resolved_skill_name / "SKILL.md"
    if direct.exists():
        engine = DiscoveryEngine(source_path, source_internal)
        skill_found = next((s for s in engine.discover_skills() if s.name == resolved_skill_name), None)

    if not skill_found:
        for skills_path, _tool, dtype in discover_all_skill_directories():
            if dtype == source_internal and skills_path.exists():
                engine = DiscoveryEngine(skills_path, dtype)
                skill_found = next((s for s in engine.discover_skills() if s.name == resolved_skill_name), None)
                if skill_found:
                    break

    if not skill_found:
        raise click.ClickException(f"Skill '{resolved_skill_name}' not found in {from_dir}")

    # Overwrite protection
    if not force and not dry_run and target_path.exists():
        engine = DiscoveryEngine(target_path, target_internal)
        existing = next((s for s in engine.discover_skills() if s.name == resolved_skill_name), None)
        if existing:
            console.print(f"[yellow]Warning: '{resolved_skill_name}' already exists in {to_dir}[/yellow]")
            if not click.confirm("Overwrite?"):
                console.print("[dim]Sync cancelled.[/dim]")
                return

    try:
        sync_skill(skill_found, target_path, dry_run=dry_run)
        if dry_run:
            console.print(f"[blue]Would sync '{resolved_skill_name}' from {from_dir} to {to_dir}[/blue]")
        else:
            console.print(f"[green]✓ Synced '{resolved_skill_name}' from {from_dir} to {to_dir}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Sync failed: {e}[/red]")
        raise click.Abort()


@cli.command(name="update")
@click.argument("skill_name", required=False)
def update_skill(skill_name: str) -> None:
    """Check for and apply skill updates.

    Examples:

        skill-hub update
        skill-hub update my-skill
    """
    from skill_hub.version import update_skill as do_update, check_update

    if skill_name:
        success = do_update(skill_name)
        if not success:
            raise click.Abort()
    else:
        if not PUBLIC_PATH.exists():
            console.print(f"[yellow]Skills directory not found:[/yellow] {PUBLIC_PATH}")
            return

        engine = DiscoveryEngine(PUBLIC_PATH)
        skills = engine.discover_skills()

        if not skills:
            console.print("[yellow]No skills found in ~/.agents/skills[/yellow]")
            return

        has_updates = False
        for skill in skills:
            has_update, current_version, latest_version = check_update(skill.name, skill.path.parent)
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

        skill-hub version
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
    """Update skill-hub to the latest version."""
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


@cli.command(name="web")
@click.option("--port", default=7860, type=int, help="Port to run the web server on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
def web_command(port: int, host: str, no_open: bool) -> None:
    """Start the skill-hub web UI.

    Opens a browser interface for managing skills from ~/.skills_repo/.

    Skills are installed to both ~/.claude/skills/ and ~/.agents/skills/.

    Examples:

        skill-hub web
        skill-hub web --port 9000
    """
    import threading
    import time
    import webbrowser

    from skill_hub.web.app import create_app

    app = create_app()

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://{host}:{port}")

    if not no_open:
        threading.Thread(target=open_browser, daemon=True).start()

    console.print(f"[green]Starting skill-hub web UI at http://{host}:{port}[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")
    app.run(host=host, port=port, debug=False, threaded=True)
