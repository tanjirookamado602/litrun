"""
litrun CLI: LoRA On-Device Adaptation Command
Initialize, train, inspect, and evaluate low-rank adapters for edge models.
"""

from __future__ import annotations
import json
import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from litrun.lora import LoRAAdapter, LoRAConfig

console = Console()


@click.group(name="lora")
def lora_cmd():
    """🧬 On-device Low-Rank Adaptation (LoRA) edge fine-tuning."""
    pass


@lora_cmd.command(name="init")
@click.option("-n", "--name", default="edge_lora", help="Adapter name")
@click.option("-o", "--output", help="Output path (default: <name>.litlora)")
@click.option("-m", "--model", default="smollm2-135m", help="Base model identifier")
@click.option("-r", "--rank", default=4, type=int, help="Rank r (default: 4)")
@click.option("-a", "--alpha", default=8.0, type=float, help="Scaling alpha (default: 8.0)")
def lora_init(name: str, output: str, model: str, rank: int, alpha: float):
    """Create a new initialized LoRA adapter."""
    output_path = output or f"{name}.litlora"
    adapter = LoRAAdapter.create(name=name, base_model=model, rank=rank, alpha=alpha)
    adapter.save(output_path)
    summary = adapter.get_summary()

    console.print(
        Panel(
            f"[bold green]✨ Initialized Edge LoRA Adapter: {output_path}[/bold green]\n"
            f"[cyan]Base Model:[/cyan]           {summary['base_model']}\n"
            f"[cyan]Rank (r):[/cyan]             {summary['rank']}\n"
            f"[cyan]Alpha:[/cyan]                {summary['alpha']}\n"
            f"[cyan]Target Modules:[/cyan]       {', '.join(summary['target_modules'])}\n"
            f"[cyan]Trainable Parameters:[/cyan] {summary['trainable_parameters']:,}\n"
            f"[cyan]Memory Footprint:[/cyan]     {summary['memory_footprint_kb']} KB",
            title="LoRA Initialization",
            border_style="green",
        )
    )


@lora_cmd.command(name="info")
@click.option("-a", "--adapter", "adapter_path", required=True, help="Path to .litlora file")
@click.option("--json", "output_json", is_flag=True, default=False, help="Output machine-readable JSON")
def lora_info(adapter_path: str, output_json: bool):
    """Display adapter configuration and memory footprint."""
    if not os.path.isfile(adapter_path):
        console.print(f"[bold red]❌ Error:[/bold red] File not found: {adapter_path}")
        raise click.Abort()

    adapter = LoRAAdapter.load(adapter_path)
    summary = adapter.get_summary()

    if output_json:
        click.echo(json.dumps(summary, indent=2))
        return

    table = Table(title=f"🔍 LoRA Adapter: {os.path.basename(adapter_path)}", border_style="magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    table.add_row("Adapter Name", summary["name"])
    table.add_row("Base Model", summary["base_model"])
    table.add_row("Rank (r)", str(summary["rank"]))
    table.add_row("Alpha", str(summary["alpha"]))
    table.add_row("Target Modules", ", ".join(summary["target_modules"]))
    table.add_row("Trainable Parameters", f"{summary['trainable_parameters']:,}")
    table.add_row("Memory Footprint", f"{summary['memory_footprint_kb']} KB")

    console.print(table)


@lora_cmd.command(name="train")
@click.option("-a", "--adapter", "adapter_path", required=True, help="Path to .litlora file")
@click.option("-d", "--data", "data_path", help="Path to training JSONL file")
@click.option("--epochs", default=3, type=int, help="Training epochs (default: 3)")
@click.option("--lr", default=0.005, type=float, help="Learning rate (default: 0.005)")
def lora_train(adapter_path: str, data_path: str, epochs: int, lr: float):
    """Train adapter on prompt/response dataset on-device."""
    if not os.path.isfile(adapter_path):
        console.print(f"[bold red]❌ Error:[/bold red] File not found: {adapter_path}")
        raise click.Abort()

    adapter = LoRAAdapter.load(adapter_path)
    examples = []

    if data_path and os.path.isfile(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    prompt = entry.get("prompt") or entry.get("input", "")
                    target = entry.get("target") or entry.get("output", "")
                    if prompt and target:
                        examples.append((prompt, target))
    else:
        examples = [
            ("Turn on living room light", "action: set_gpio(pin=17, value=1)"),
            ("Shut down engine cooling fan", "action: set_gpio(pin=22, value=0)"),
            ("Report temperature sensor reading", "action: read_telemetry(sensor='temp')"),
            ("Lock edge security perimeter", "action: trigger_relay(zone='security', state='locked')"),
        ]
        console.print("[dim]ℹ️ No dataset file provided; using synthetic edge robotics demonstration dataset.[/dim]")

    console.print(
        Panel(
            f"[bold]Training Adapter:[/bold] {adapter.config.adapter_name}\n"
            f"[bold]Examples:[/bold] {len(examples)} | [bold]Epochs:[/bold] {epochs} | [bold]LR:[/bold] {lr}",
            title="⚡ On-Device Edge Training",
            border_style="yellow",
        )
    )

    result = adapter.train_on_examples(examples, epochs=epochs, lr=lr)
    adapter.save(adapter_path)

    console.print(f"[bold green]✓ Training Complete![/bold green]")
    console.print(f"  • Final Loss: [cyan]{result['final_loss']}[/cyan]")
    console.print(f"  • Training Time: [cyan]{result['training_time_sec']}s[/cyan]")
    console.print(f"  • Weights Saved: [green]{adapter_path}[/green]\n")
