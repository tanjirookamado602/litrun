"""
litrun ui: Launch embedded Web UI dashboard and interactive device console
"""

import webbrowser
import click
from rich.console import Console
from rich.panel import Panel
from litrun.server import start_server

console = Console()


@click.command(name="ui")
@click.argument("model_id", default="qwen2.5-0.5b")
@click.option("--host", default="0.0.0.0", help="Network host interface to bind (default: 0.0.0.0)")
@click.option("--port", default=8080, type=int, help="Port to listen on (default: 8080)")
@click.option("--open/--no-open", "open_browser", default=True, help="Automatically open browser tab (default: enabled)")
def ui_cmd(model_id: str, host: str, port: int, open_browser: bool):
    """Launch the litrun visual Web UI device dashboard & AI playground."""
    target_url = f"http://localhost:{port}" if host in ["0.0.0.0", "127.0.0.1"] else f"http://{host}:{port}"

    console.print(
        Panel(
            f"[bold green]⚡ litrun Web UI Device Console[/bold green]\n"
            f"[cyan]Dashboard URL:[/cyan] [bold underline]{target_url}[/bold underline]\n"
            f"[dim]Features: Telemetry Gauges • Multimodal Chat • 40-Pin GPIO Matrix • Benchmarking[/dim]",
            title="[bold]litrun Web Console[/bold]",
            border_style="green",
        )
    )

    if open_browser:
        try:
            webbrowser.open_new_tab(target_url)
        except Exception:
            pass

    start_server(host=host, port=port, model_id=model_id, ui=True)

