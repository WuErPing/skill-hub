"""Command-line interface for skill-hub."""

import click

from skill_hub.web.app import create_app


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

    from rich.console import Console

    console = Console()
    app = create_app()

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://{host}:{port}")

    if not no_open:
        threading.Thread(target=open_browser, daemon=True).start()

    console.print(f"[green]Starting skill-hub web UI at http://{host}:{port}[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")
    app.run(host=host, port=port, debug=False, threaded=True)
