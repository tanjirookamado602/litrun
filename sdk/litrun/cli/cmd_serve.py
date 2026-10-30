"""
litrun serve: Start OpenAI-compatible HTTP REST server & Web UI console
"""

import click
from rich.console import Console
from litrun.server import start_server

console = Console()


@click.command(name="serve")
@click.argument("model_id", default="qwen2.5-0.5b")
@click.option("--host", default="0.0.0.0", help="Network host interface to bind (default: 0.0.0.0)")
@click.option("--port", default=8080, type=int, help="Port to listen on (default: 8080)")
@click.option("--ui/--no-ui", "ui", default=True, help="Enable embedded Web UI dashboard (default: enabled)")
def serve_cmd(model_id: str, host: str, port: int, ui: bool):
    """Starts an OpenAI-compatible REST server (POST /v1/chat/completions) with embedded Web UI console."""
    start_server(host=host, port=port, model_id=model_id, ui=ui)
