"""
litrun CLI: Swarm & Edge Mesh Cluster Command
Manage decentralized SBC clusters, discover peer nodes, and route tasks.
"""

from __future__ import annotations
import json
import sys
import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from litrun.swarm import SwarmMesh, SwarmNode, SwarmRouter, SwarmBeacon

console = Console()


@click.group(name="swarm")
def swarm_cmd():
    """🌐 Decentralized edge SBC mesh clustering and task dispatching."""
    pass


@swarm_cmd.command(name="status")
@click.option("--json", "output_json", is_flag=True, default=False, help="Output machine-readable JSON")
def swarm_status(output_json: bool):
    """Show active mesh nodes and hardware capabilities."""
    mesh = SwarmMesh()
    nodes = mesh.get_all_nodes()

    if output_json:
        click.echo(json.dumps([n.to_dict() for n in nodes], indent=2))
        return

    table = Table(title="🌐 litrun Edge Swarm Mesh Status", border_style="blue")
    table.add_column("Node ID", style="cyan", no_wrap=True)
    table.add_column("Hostname", style="green")
    table.add_column("Endpoint", style="yellow")
    table.add_column("SoC / Board", style="magenta")
    table.add_column("RAM (Avail/Total)", style="bold")
    table.add_column("Thermal", style="red")
    table.add_column("Accelerator", style="green")

    for n in nodes:
        npu_str = f"RKNN ({n.npu_tops}T)" if n.has_npu else ("CUDA" if n.has_gpu else "CPU")
        ram_str = f"{n.ram_avail_mb} / {n.ram_total_mb} MB"
        thermal_str = "Cool (0)" if str(n.thermal_state) in ("0", "nominal") else f"Throttled ({n.thermal_state})"
        table.add_row(
            n.node_id,
            n.hostname,
            f"{n.ip}:{n.port}",
            n.soc or n.board_name,
            ram_str,
            thermal_str,
            npu_str,
        )

    console.print(table)
    console.print(f"[dim]Total Active Nodes: {len(nodes)} (Local: {mesh.local_node.node_id})[/dim]\n")


@swarm_cmd.command(name="beacon")
@click.option("--port", default=50505, type=int, help="UDP discovery port (default: 50505)")
def swarm_beacon(port: int):
    """Start background UDP discovery beacon."""
    mesh = SwarmMesh()
    beacon = SwarmBeacon(mesh, port=port)
    console.print(
        Panel(
            f"[bold cyan]📡 litrun Swarm Beacon Active[/bold cyan]\n"
            f"[dim]Port:[/dim] UDP {port}\n"
            f"[dim]Node ID:[/dim] {mesh.local_node.node_id} ({mesh.local_node.hostname})\n"
            f"[dim]Endpoint:[/dim] http://{mesh.local_node.ip}:{mesh.local_node.port}\n"
            f"Broadcasting and listening for SBC cluster heartbeats. Press Ctrl+C to stop.",
            title="P2P Mesh Discovery",
            border_style="cyan",
        )
    )
    beacon.start()
    try:
        while True:
            time.sleep(2.0)
            nodes = mesh.get_all_nodes()
            sys.stdout.write(f"\r   Peers in Mesh: {len(nodes)} | Last sync: {time.strftime('%H:%M:%S')}")
            sys.stdout.flush()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping Swarm Beacon.[/yellow]")
    finally:
        beacon.stop()


@swarm_cmd.command(name="dispatch")
@click.option("-p", "--prompt", default="Summarize system telemetry health.", help="Prompt to dispatch")
@click.option("-m", "--model", default="smollm2-135m", help="Target model identifier")
@click.option("-t", "--type", "task_type", type=click.Choice(["reasoning", "vision", "audio"]), default="reasoning", help="Task type")
def swarm_dispatch(prompt: str, model: str, task_type: str):
    """Intelligently route a prompt to the optimal node in the cluster."""
    mesh = SwarmMesh()
    router = SwarmRouter(mesh)

    console.print(f"\n[bold green]🚀 Dispatching to Edge Swarm...[/bold green]")
    console.print(f"[cyan]Task Type:[/cyan] {task_type} | [cyan]Target Model:[/cyan] {model}")
    console.print(f"[cyan]Prompt:[/cyan] \"{prompt}\"")

    result = router.dispatch(prompt=prompt, task_type=task_type, model_id=model)

    target = result["dispatched_to"]
    console.print(
        Panel(
            f"[bold]Target Node:[/bold] {target['hostname']} ({target['node_id']})\n"
            f"[bold]Routing Decision:[/bold] {result['routing_reason']}\n"
            f"[bold]Execution Mode:[/bold] {'Remote Node over HTTP' if result['is_remote'] else 'Local Node'}\n"
            f"[bold]Speed:[/bold] {result['tokens_per_sec']} tok/s | [bold]TTFT:[/bold] {result['ttft_ms']} ms",
            title="Cluster Routing Result",
            border_style="green",
        )
    )
    console.print(Panel(result["response"], title="Response Output", border_style="dim"))
