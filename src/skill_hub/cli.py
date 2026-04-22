"""Command-line interface for skill-hub."""

import subprocess
from pathlib import Path

import click
from rich.console import Console

from skill_hub import __version__
from skill_hub.web.app import create_app

console = Console()


def _check_update_on_startup() -> bool:
    """Check for updates and prompt user. Returns True if server should start."""
    from skill_hub.version import compare_versions, get_latest_version

    try:
        latest = get_latest_version("wuerping/skill-hub", timeout=5)
    except Exception:
        return True

    if not latest or compare_versions(__version__, latest) >= 0:
        return True

    skip_file = Path.home() / ".skills_repo" / "skip_update"
    if skip_file.exists():
        skipped = skip_file.read_text().strip()
        if skipped == latest:
            return True

    console.print("")
    console.print(
        f"[yellow]Update available: skill-hub {latest}[/yellow] "
        f"[dim](current: {__version__})[/dim]"
    )
    console.print("[dim]You can upgrade to get the latest features and bug fixes.[/dim]")
    console.print("")

    choice = click.prompt(
        "What would you like to do?",
        type=click.Choice(["update", "skip", "later"], case_sensitive=False),
        default="later",
        show_choices=True,
        show_default=True,
    )

    if choice.lower() == "update":
        console.print("Updating skill-hub...")
        try:
            subprocess.check_call(["pip", "install", "--upgrade", "skill-hub"])
            console.print("[green]✓ Updated successfully![/green]")
            console.print(
                "[dim]Please restart 'skill-hub web' to use the new version.[/dim]"
            )
            return False
        except subprocess.CalledProcessError:
            console.print("[red]✗ Update failed.[/red]")
            console.print("Try manually: pip install --upgrade skill-hub")
            return True
    elif choice.lower() == "skip":
        skip_file.parent.mkdir(parents=True, exist_ok=True)
        skip_file.write_text(latest)
        console.print(
            f"[dim]Skipped {latest}. You won't be prompted again for this version.[/dim]"
        )
        return True
    else:  # later
        return True


@click.group()
def cli() -> None:
    """skill-hub: manage skills from ~/.skills_repo/"""
    pass


@cli.command(name="web")
@click.option("--port", default=7860, type=int, help="Port to run the web server on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
@click.option(
    "--no-check-update", is_flag=True, help="Skip update check on startup"
)
def web_command(port: int, host: str, no_open: bool, no_check_update: bool) -> None:
    """Start the skill-hub web UI."""
    import threading
    import time
    import webbrowser

    if not no_check_update:
        if not _check_update_on_startup():
            return

    app = create_app()

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://{host}:{port}")

    if not no_open:
        threading.Thread(target=open_browser, daemon=True).start()

    console.print(f"[green]Starting skill-hub web UI at http://{host}:{port}[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")
    app.run(host=host, port=port, debug=False, threaded=True)


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
    console.print("Updating skill-hub...")
    try:
        subprocess.check_call(["pip", "install", "--upgrade", "skill-hub"])
        console.print("[green]✓ Updated successfully![/green]")
        console.print("Restart your terminal or run 'skill-hub --version' to see the new version.")
    except subprocess.CalledProcessError:
        console.print("[red]✗ Update failed.[/red]")
        console.print("Try manually: pip install --upgrade skill-hub")
        raise click.Abort()
