"""
CLI Command: litrun create
Compiles and manages custom edge LLM agents using declarative Modelfiles.
"""

from __future__ import annotations
import os
import json
import click
from rich.console import Console
from rich.table import Table
from litrun.modelfile import (
    ModelfileParser,
    save_custom_model,
    get_custom_model,
    list_custom_models,
    delete_custom_model,
    export_custom_model_pack,
    import_custom_model_pack,
)

console = Console()


@click.group(invoke_without_command=True)
@click.option("-f", "--file", "modelfile_path", type=click.Path(exists=False), help="Path to Modelfile to build.")
@click.option("-t", "--tag", "tag", type=str, help="Tag/name for the custom model (e.g. 'rover-01:latest').")
@click.option("--list", "list_flag", is_flag=True, help="List all locally compiled custom models.")
@click.pass_context
def create_cmd(ctx, modelfile_path, tag, list_flag):
    """🛠️ Compile & package custom edge AI agents via declarative Modelfiles."""
    if ctx.invoked_subcommand is not None:
        return

    if list_flag:
        ctx.invoke(list_models_cmd)
        return

    if modelfile_path and tag:
        _build_from_file(modelfile_path, tag)
    elif modelfile_path and not tag:
        console.print("[red]Error: Must specify model tag using -t/--tag (e.g., -t my-agent:latest)[/red]")
    elif not modelfile_path and tag:
        console.print("[red]Error: Must specify Modelfile path using -f/--file (e.g., -f Modelfile)[/red]")
    else:
        console.print(ctx.get_help())


def _build_from_file(modelfile_path: str, tag: str):
    console.print(f"[bold cyan]🛠️ Compiling Modelfile from '{modelfile_path}' as '{tag}'...[/bold cyan]")
    try:
        parsed = ModelfileParser.parse_file(modelfile_path)
    except Exception as e:
        console.print(f"[bold red]Failed to parse Modelfile: {e}[/bold red]")
        return

    console.print(f"  • Base Model:   [bold green]{parsed.base_model}[/bold green]")
    if parsed.system_prompt:
        preview = parsed.system_prompt.replace("\n", " ")[:60]
        console.print(f"  • System Prompt: [dim]\"{preview}...\"[/dim]")
    if parsed.parameters:
        console.print(f"  • Parameters:    [dim]{parsed.parameters}[/dim]")
    if parsed.adapter_path:
        console.print(f"  • LoRA Adapter:  [bold yellow]{parsed.adapter_path}[/bold yellow]")

    try:
        manifest = save_custom_model(tag, parsed)
        console.print(f"[bold green]✓ Successfully built custom model '{tag}'[/bold green]")
        console.print(f"[dim]Run with: litrun run {tag}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Failed to save custom model: {e}[/bold red]")


@create_cmd.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="Output in machine-readable JSON format.")
def list_models_cmd(json_output: bool):
    """Lists all compiled custom models on this device."""
    models = list_custom_models()

    if json_output:
        data = [m.to_dict() for m in models]
        click.echo(json.dumps(data, indent=2))
        return

    if not models:
        console.print("[yellow]No custom models found. Create one with: litrun create -f Modelfile -t my-model:latest[/yellow]")
        return

    table = Table(title="🛠️ Custom Edge Models (litrun create)", show_header=True, header_style="bold cyan")
    table.add_column("Tag", style="bold green", min_width=20)
    table.add_column("Base Model", style="bold")
    table.add_column("Parameters", style="dim")
    table.add_column("LoRA Adapter", style="yellow")
    table.add_column("Created", style="dim")

    import datetime
    for m in models:
        created_str = datetime.datetime.fromtimestamp(m.created_at).strftime("%Y-%m-%d %H:%M")
        params_str = ", ".join(f"{k}={v}" for k, v in list(m.parameters.items())[:3])
        table.add_row(
            m.tag,
            m.base_model,
            params_str or "-",
            m.adapter_filename or "-",
            created_str,
        )

    console.print(table)


@create_cmd.command(name="inspect")
@click.argument("tag", type=str)
def inspect_model_cmd(tag: str):
    """Displays detailed manifest metadata for a custom model."""
    manifest = get_custom_model(tag)
    if not manifest:
        console.print(f"[bold red]Custom model '{tag}' not found.[/bold red]")
        return

    console.print(f"[bold cyan]🔍 Custom Model Manifest: {manifest.tag}[/bold cyan]")
    console.print(f"  • Base Model:       [bold green]{manifest.base_model}[/bold green]")
    console.print(f"  • System Prompt:    {manifest.system_prompt or '(none)'}")
    console.print(f"  • Parameters:       {json.dumps(manifest.parameters)}")
    console.print(f"  • LoRA Adapter:     {manifest.adapter_filename or '(none)'}")
    console.print(f"  • License:          {manifest.license or 'Unspecified'}")


@create_cmd.command(name="export")
@click.argument("tag", type=str)
@click.option("-o", "--output", "output_path", type=click.Path(), required=True, help="Destination .litpack archive path.")
def export_model_cmd(tag: str, output_path: str):
    """Exports a custom model to a portable .litpack bundle."""
    try:
        pack_path = export_custom_model_pack(tag, output_path)
        console.print(f"[bold green]✓ Exported '{tag}' package to '{pack_path}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Export failed: {e}[/bold red]")


@create_cmd.command(name="import")
@click.argument("pack_path", type=click.Path(exists=True))
@click.option("-t", "--tag", "tag", type=str, default=None, help="Override destination tag.")
def import_model_cmd(pack_path: str, tag: str):
    """Imports a .litpack bundle into local custom model registry."""
    try:
        manifest = import_custom_model_pack(pack_path, tag=tag)
        console.print(f"[bold green]✓ Imported custom model as '{manifest.tag}'[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Import failed: {e}[/bold red]")


@create_cmd.command(name="rm")
@click.argument("tag", type=str)
def rm_model_cmd(tag: str):
    """Deletes a custom model from local repository."""
    if delete_custom_model(tag):
        console.print(f"[bold green]✓ Deleted custom model '{tag}'[/bold green]")
    else:
        console.print(f"[bold red]Custom model '{tag}' not found.[/bold red]")
