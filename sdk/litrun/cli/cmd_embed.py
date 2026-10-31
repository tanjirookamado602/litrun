"""
litrun embed: Offline Vector Embedding & Local Knowledge Ingestion CLI
"""

import os
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from litrun.rag import EdgeVectorStore

console = Console()


@click.command(name="embed")
@click.argument("target", required=False, default=None)
@click.option("--text", "raw_text", default=None, help="Raw text string to embed into the vector store")
@click.option("--source", "source_name", default=None, help="Custom document source name identifier")
@click.option("--list", "list_mode", is_flag=True, help="List all indexed sources in the vector store")
@click.option("--clear", "clear_mode", is_flag=True, help="Clear all stored vector embeddings")
@click.option("-q", "--query", "query_text", default=None, help="Search the knowledge store for relevant chunks")
@click.option("-k", "--top-k", "top_k", default=3, type=int, help="Number of context matches to retrieve")
def embed_cmd(
    target: str,
    raw_text: str,
    source_name: str,
    list_mode: bool,
    clear_mode: bool,
    query_text: str,
    top_k: int,
):
    """Ingests local documents into an offline SQLite vector database for RAG."""
    store = EdgeVectorStore()

    if clear_mode:
        store.clear()
        console.print("[bold yellow]✓ Cleared all vector embeddings from local knowledge store.[/bold yellow]")
        return

    if list_mode:
        sources = store.list_sources()
        if not sources:
            console.print("[dim]Vector store is empty. Ingest files using 'litrun embed <file>'[/dim]")
            return

        table = Table(title="Indexed Local Knowledge Base", show_header=True, header_style="bold magenta")
        table.add_column("Source Document", style="bold white", width=36)
        table.add_column("Chunks", style="cyan", width=10)
        table.add_column("Vector Database", style="dim")

        for s in sources:
            table.add_row(s["source"], str(s["chunks"]), store.db_path)
        console.print(table)
        return

    if query_text:
        results = store.search(query_text, top_k=top_k)
        if not results:
            console.print(f"[yellow]No matching context found for query:[/yellow] '{query_text}'")
            return

        console.print(Panel(f"[bold cyan]Query:[/bold cyan] {query_text}", title="RAG Vector Search"))
        for i, r in enumerate(results):
            console.print(
                f"[bold green]Match #{i+1}[/bold green] "
                f"([cyan]Source: {r['source']}[/cyan] | [dim]Similarity: {r['similarity']}[/dim])\n"
                f"{r['text'][:250]}...\n"
            )
        return

    # Ingest file or text
    if target:
        if not os.path.exists(target):
            console.print(f"[bold red]✗ File not found:[/bold red] {target}")
            sys.exit(1)

        src = source_name or os.path.basename(target)
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            console.print(f"[bold red]✗ Failed to read file:[/bold red] {e}")
            sys.exit(1)

        num_chunks = store.add_document(src, content)
        console.print(
            f"[bold green]✓ Ingested document:[/bold green] [bold white]{src}[/bold white] "
            f"({num_chunks} vector chunks indexed in [dim]{store.db_path}[/dim])"
        )
        return

    if raw_text:
        src = source_name or "raw_input"
        num_chunks = store.add_document(src, raw_text)
        console.print(
            f"[bold green]✓ Ingested raw text:[/bold green] [bold white]{src}[/bold white] "
            f"({num_chunks} vector chunks indexed)"
        )
        return

    console.print("[yellow]Usage: litrun embed <file> or litrun embed --query <text>[/yellow]")
    console.print("Run [bold cyan]litrun embed --help[/bold cyan] for all options.")
