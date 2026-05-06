"""Command-line interface for skill-hub."""

import subprocess

import click
from rich.console import Console

from skill_hub import __version__
from skill_hub.web.app import create_app

console = Console()


@click.group()
def cli() -> None:
    """skill-hub: manage skills from ~/.skills_repo/"""
    pass


@cli.command(name="web")
@click.option("--port", default=7860, type=int, help="Port to run the web server on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
def web_command(port: int, host: str, no_open: bool) -> None:
    """Start the skill-hub web UI."""
    import threading
    import time
    import webbrowser

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


@cli.command(name="summarize")
@click.argument("repo_name")
def summarize_repo(repo_name: str) -> None:
    """Generate a prompt to summarize a repo's README.

    Copy the output to your agent (Claude Code, OpenCode, etc.) to generate
    a structured summary. Then submit it with: skill-hub set-summary <repo> <json>

    Example:
        skill-hub summarize anthropics/skills
    """
    from skill_hub.web.repos import load_repos_config, repo_dir
    from skill_hub.web.intro import generate_prompt, read_repo_readme

    repos = load_repos_config()
    repo = next((r for r in repos if r.name == repo_name), None)
    if not repo:
        console.print(f"[red]Repo '{repo_name}' not found.[/red]")
        console.print("Run 'skill-hub web' to add repos.")
        raise click.Abort()

    target = repo_dir(repo)
    readme = read_repo_readme(target)
    if not readme:
        console.print(f"[red]README.md not found in {target}[/red]")
        raise click.Abort()

    prompt = generate_prompt(repo_name, readme)
    console.print("[green]Copy the following prompt to your agent:[/green]")
    console.print()
    console.print(prompt)
    console.print()
    console.print("[dim]After running, submit the result with:[/dim]")
    console.print(f"[blue]skill-hub set-summary {repo_name} '<json_result>'[/blue]")


@cli.command(name="set-summary")
@click.argument("repo_name")
@click.argument("summary_json")
def set_summary(repo_name: str, summary_json: str) -> None:
    """Submit a generated summary for a repo.

    The summary_json should be a JSON string with keys:
    purpose, features, value, target_users, tech_stack.

    Example:
        skill-hub set-summary anthropics/skills '{"purpose":"...",...}'
    """
    import json
    from skill_hub.web.repos import load_repos_config, repo_dir
    from skill_hub.web.intro import load_intro, save_intro
    from datetime import datetime
    from skill_hub.web.intro import _md5_of_file

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise click.Abort()

    repos = load_repos_config()
    repo = next((r for r in repos if r.name == repo_name), None)
    if not repo:
        console.print(f"[red]Repo '{repo_name}' not found.[/red]")
        raise click.Abort()

    target = repo_dir(repo)
    readme_path = target / "README.md"
    if not readme_path.exists():
        readme_path = target / "Readme.md"

    intro = load_intro(repo_name, readme_path)
    intro.summary = summary
    intro.generated_at = datetime.utcnow()
    intro.cached = True
    intro.readme_md5 = _md5_of_file(readme_path)

    save_intro(intro)
    console.print(f"[green]Summary saved for {repo_name}[/green]")
