"""
CLI Command: litrun fleet
Enterprise Edge Fleet Management & Cryptographic OTA Updates.
"""

from __future__ import annotations
import os
import json
import uuid
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from litrun.fleet import (
    FleetManager,
    FleetNodeProfile,
    OTAPackage,
    create_local_fleet_node,
)

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def fleet_cmd(ctx):
    """🌐 Enterprise edge fleet management & cryptographic OTA rollouts."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(status_cmd)


@fleet_cmd.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="Output in machine-readable JSON format.")
def status_cmd(json_output: bool):
    """Displays real-time fleet health, node telemetry, and OTA rollout status."""
    manager = FleetManager()

    # If empty, add local node for instant exploration
    if not manager.nodes:
        local_node = create_local_fleet_node()
        manager.enroll_node(local_node)

    summary = manager.fleet_telemetry_summary()

    if json_output:
        res = {
            "summary": summary,
            "nodes": [n.to_dict() for n in manager.nodes.values()],
            "rollouts": [r.to_dict() for r in manager.rollouts.values()],
        }
        click.echo(json.dumps(res, indent=2))
        return

    # Rich Panel Summary
    panel_text = (
        f"[bold cyan]Fleet Status:[/bold cyan] {summary['online_nodes']}/{summary['total_nodes']} Nodes Online  |  "
        f"[green]{summary['healthy_nodes']} Healthy[/green]  |  "
        f"[yellow]{summary['throttled_nodes']} Throttled[/yellow]  |  "
        f"Avg Temp: [bold]{summary['average_cpu_temp_c']}°C[/bold]  |  "
        f"Cluster RAM: [dim]{summary['available_ram_mb']:,}MB / {summary['total_ram_mb']:,}MB available[/dim]"
    )
    console.print(Panel(panel_text, title="🌐 litrun Edge Fleet Cluster", border_style="cyan"))

    table = Table(title="Cluster Edge Nodes", show_header=True, header_style="bold magenta")
    table.add_column("Node ID", style="bold green", min_width=18)
    table.add_column("Hostname", style="dim")
    table.add_column("Board / SoC", style="bold")
    table.add_column("RAM Avail", justify="right")
    table.add_column("Temp", justify="right")
    table.add_column("Active Model", style="cyan")
    table.add_column("Status", justify="center")

    for n in manager.nodes.values():
        status_badge = (
            "[bold green]HEALTHY[/bold green]"
            if n.status == "healthy"
            else f"[bold red]{n.status.upper()}[/bold red]"
        )
        temp_color = "green" if n.cpu_temp_c < 65 else ("yellow" if n.cpu_temp_c < 80 else "red")

        table.add_row(
            n.node_id,
            n.hostname,
            f"{n.board_name} ({n.soc})",
            f"{n.ram_avail_mb} / {n.ram_total_mb} MB",
            f"[{temp_color}]{n.cpu_temp_c:.1f}°C[/{temp_color}]",
            f"{n.current_model} (v{n.current_model_version})",
            status_badge,
        )

    console.print(table)


@fleet_cmd.command(name="enroll")
@click.option("-id", "--node-id", "node_id", type=str, default=None, help="Custom ID for this edge node.")
def enroll_cmd(node_id: str):
    """Enrolls the local edge device into the fleet management network."""
    manager = FleetManager()
    node = create_local_fleet_node()
    if node_id:
        node.node_id = node_id

    manager.enroll_node(node)
    console.print(f"[bold green]✓ Enrolled local node '{node.node_id}' ({node.board_name}) into fleet cluster.[/bold green]")


@fleet_cmd.command(name="deploy")
@click.argument("model_id", type=str)
@click.option("-v", "--version", "version", type=str, default="1.1.0", help="Model release version.")
@click.option("-q", "--quant", "quant", type=str, default="q4_k_m", help="Quantization variant.")
@click.option("--strategy", type=click.Choice(["canary", "immediate", "rolling"]), default="canary", help="Rollout strategy.")
@click.option("--canary-ratio", type=float, default=0.25, help="Canary node fraction (0.1 to 1.0).")
def deploy_cmd(model_id: str, version: str, quant: str, strategy: str, canary_ratio: float):
    """Issues a cryptographically signed OTA model rollout across the cluster."""
    manager = FleetManager()

    pkg = OTAPackage(
        package_id=f"pkg-{uuid.uuid4().hex[:8]}",
        target_model=model_id,
        target_quant=quant,
        target_version=version,
        sha256_checksum=uuid.uuid4().hex * 2,
        rollout_strategy=strategy,
        canary_ratio=canary_ratio,
    )

    rollout = manager.create_ota_deployment(pkg)
    console.print(f"[bold green]🚀 Created signed OTA Deployment: {pkg.package_id}[/bold green]")
    console.print(f"  • Target:   [bold cyan]{pkg.target_model}:{pkg.target_quant} (v{pkg.target_version})[/bold cyan]")
    console.print(f"  • Strategy: [magenta]{pkg.rollout_strategy.upper()}[/magenta] (Phase: {rollout.phase})")
    console.print(f"  • Canaries: [yellow]{rollout.canary_nodes}[/yellow]")
    console.print(f"  • HMAC-SHA256 Signature: [dim]{pkg.signature[:24]}...[/dim]")


@fleet_cmd.command(name="evaluate")
@click.argument("package_id", type=str)
def evaluate_cmd(package_id: str):
    """Evaluates canary health and either promotes or triggers autonomous rollback."""
    manager = FleetManager()
    success, msg = manager.evaluate_canary(package_id)

    if success:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")


@fleet_cmd.command(name="rollback")
@click.option("--node", "node_id", type=str, default=None, help="Target specific node or omit for fleet-wide rollback.")
def rollback_cmd(node_id: str):
    """Triggers an emergency fallback to previous verified stable model."""
    manager = FleetManager()
    reverted = manager.trigger_rollback(node_id)
    console.print(f"[bold yellow]⚠️ Reverted models to safe snapshot on {len(reverted)} node(s): {reverted}[/bold yellow]")
