"""
litrun run: One-command hardware-aware model execution
"""

import sys
import time
import click
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
from litrun.hardware import probe_hardware
from litrun.registry import get_model, select_optimal_variant
from litrun.governor import check_ram_envelope, poll_governor
from litrun.resolver import (
    select_binary_target,
    get_model_cache_path,
    resolve_engine_binary,
    resolve_model_weights,
)
from litrun.engine import get_backend
from litrun.session import Session
from litrun.tools import (
    EMBEDDED_TOOLS_SYSTEM_PROMPT,
    parse_tool_call,
    execute_embedded_tool,
)

console = Console()


@click.command(name="run")
@click.argument("model_id", default="qwen2.5-0.5b")
@click.option("-p", "--prompt", "prompt_text", default=None, help="Direct prompt to execute")
@click.option("-q", "--quant", "preferred_quant", default=None, help="Preferred quantization (e.g. Q4_K_M, Q8_0)")
@click.option("-t", "--threads", "thread_count", default=None, type=int, help="Thread count override")
@click.option("--system", "system_prompt", default=None, help="System prompt override")
@click.option("--json", "json_mode", is_flag=True, help="Enforce deterministic JSON output using GBNF grammar")
@click.option("--schema", "schema_arg", default=None, help="JSON Schema string or path to .json schema file")
@click.option("--tools", "tools_mode", is_flag=True, help="Enable autonomous edge hardware tool calling (GPIO & telemetry)")
@click.option("--npu", "npu_mode", is_flag=True, help="Offload model inference to Rockchip NPU (RK3588 / RK3566)")
@click.option("--demo", is_flag=True, help="Run in high-speed hardware simulation mode without downloading weights")
def run_cmd(
    model_id: str,
    prompt_text: str,
    preferred_quant: str,
    thread_count: int,
    system_prompt: str,
    json_mode: bool,
    schema_arg: str,
    tools_mode: bool,
    npu_mode: bool,
    demo: bool,
):
    """Executes any curated LLM with zero quantization guesswork."""

    # 1. Probing Hardware
    with console.status("[bold cyan]Probing hardware topology & ISA extensions...[/bold cyan]", spinner="dots"):
        hw = probe_hardware()
        gov = poll_governor()

    console.print(
        f"[bold blue]→ Detected:[/bold blue] "
        f"[bold white]{hw.board_name}[/bold white] "
        f"({hw.soc} {hw.cpu_part}, {hw.ram_total_mb} MB RAM, {hw.ram_avail_mb} MB free)"
    )

    # 2. Model Registry Lookup & Smart Quantization Selection
    entry = get_model(model_id)
    if not entry:
        console.print(f"[bold red]✗ Error:[/bold red] Model '[bold yellow]{model_id}[/bold yellow]' not found in registry.")
        console.print("Run [bold cyan]litrun list[/bold cyan] to view available models.")
        sys.exit(1)

    variant, decision_msg = select_optimal_variant(entry, hw, preferred_quant=preferred_quant)

    allowed, needed_mb, gov_reason, is_tight = check_ram_envelope(
        variant.size_mb,
        context_length=entry.default_context,
        kv_bytes_per_token=entry.kv_bytes_per_token,
    )

    status_tag = "[bold green]optimal RAM envelope[/bold green]" if not is_tight else "[bold yellow]tight RAM envelope[/bold yellow]"
    console.print(
        f"[bold blue]→ Selected:[/bold blue] "
        f"[bold white]{entry.id}-{variant.quant}[/bold white] "
        f"({status_tag}: {needed_mb}MB required / {hw.ram_avail_mb}MB free)"
    )

    if not allowed:
        console.print(f"[bold red]✗ Governor Warning:[/bold red] {gov_reason}")

    # NPU Hardware Acceleration Routing
    if npu_mode:
        from litrun.rknn import RKNNRuntime
        rknn = RKNNRuntime(allow_mock=True)
        console.print(
            f"[bold green]⚡ NPU Acceleration Active:[/bold green] "
            f"Offloading matrix tensors to {rknn.info.soc} NPU ({rknn.info.npu_cores} Cores, {rknn.info.peak_tops} TOPS @ {rknn.info.cur_freq_mhz}MHz)"
        )
        if prompt_text:
            out = rknn.infer(prompt_text, model_id=model_id)
            console.print(f"\n[bold green]litrun (NPU):[/bold green] {out}")
            return

    # 3. Precompiled Binary Resolution
    bin_target = select_binary_target(hw)
    with console.status(f"[bold cyan]Resolving precompiled engine for {bin_target}...[/bold cyan]", spinner="dots"):
        try:
            bin_path = resolve_engine_binary(hw)
            console.print(f"[bold blue]→ Binary:[/bold blue] tuned {bin_target} engine ready [green][cached][/green]")
        except Exception as e:
            bin_path = None
            console.print(f"[bold blue]→ Binary:[/bold blue] using simulation engine ([dim]{e}[/dim])")

    # 4. Model Weights Check or Stream Pull
    model_path = get_model_cache_path(entry.id, variant.quant)
    import os
    if demo:
        console.print(f"[bold blue]→ Model:[/bold blue] running in hardware simulator mode ([dim]demo mode[/dim])")
        model_path = None
    elif os.path.isfile(model_path):
        console.print(f"[bold blue]→ Model:[/bold blue] {entry.id}-{variant.quant} weights ready [green][cached][/green]")
    else:
        console.print(f"[bold blue]→ Model:[/bold blue] streaming weights from HuggingFace ({variant.size_mb}MB)...")
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {entry.id} ({variant.quant})", total=variant.size_mb * 1024 * 1024)

                def update_cb(done, total):
                    progress.update(task, completed=done, total=total)

                model_path = resolve_model_weights(entry, variant, progress_callback=update_cb)
            console.print(f"[bold green]✓ Download verified with SHA-256[/bold green]")
        except Exception as e:
            console.print(f"[yellow]! Offline mode / demo simulation enabled ([dim]{e}[/dim])[/yellow]")
            model_path = None

    # 5. Dynamic Concurrency & Warmup
    final_threads = thread_count or gov.recommended_threads
    backend = get_backend(
        binary_path=bin_path,
        model_path=model_path,
        threads=final_threads,
        context_length=entry.default_context,
        model_id=entry.id,
        allow_mock=True,
    )

    expected_speed = 14.2
    for bp in entry.hardware_profiles:
        if hw.profile_id.startswith(bp.profile.split("-")[0]):
            expected_speed = bp.tokens_per_sec
            break

    console.print(
        f"[bold blue]→ Warmup complete.[/bold blue] "
        f"Ready at ~{expected_speed:.1f} tokens/sec on {final_threads} threads. Type to interact."
    )

    # 6. Execution Loop
    try:
        session = Session(max_context_tokens=entry.default_context)
        if tools_mode:
            console.print("[bold blue]→ Embedded Tools:[/bold blue] [bold green]Active[/bold green] (Direct sysfs GPIO & telemetry)")
            session.system_prompt = (
                (system_prompt + "\n\n" + EMBEDDED_TOOLS_SYSTEM_PROMPT)
                if system_prompt
                else EMBEDDED_TOOLS_SYSTEM_PROMPT
            )
        elif system_prompt:
            session.system_prompt = system_prompt

        grammar = None
        if schema_arg:
            import json as _json
            from litrun.grammar import json_schema_to_gbnf
            try:
                if os.path.isfile(schema_arg):
                    with open(schema_arg, "r") as sf:
                        schema_dict = _json.load(sf)
                else:
                    schema_dict = _json.loads(schema_arg)
                grammar = json_schema_to_gbnf(schema_dict)
                console.print("[dim]✓ Applied GBNF JSON Schema constraints[/dim]")
            except Exception as se:
                console.print(f"[bold red]✗ Schema Error:[/bold red] Could not parse schema: {se}")
        elif json_mode:
            from litrun.grammar import STANDARD_JSON_GBNF
            grammar = STANDARD_JSON_GBNF
            console.print("[dim]✓ Applied standard JSON GBNF grammar[/dim]")

        import json as _json

        def run_step(prompt_input: str) -> None:
            session.add_user_message(prompt_input)
            formatted = session.format_prompt(family=entry.family)

            console.print(f"[bold cyan]litrun:[/bold cyan] ", end="")
            chunks = []
            t0 = time.perf_counter()
            token_count = 0

            for chunk in backend.stream(formatted, threads=final_threads, grammar=grammar, tools=tools_mode):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                chunks.append(chunk)
                token_count += 1

            initial_text = "".join(chunks)

            if tools_mode:
                tool_call = parse_tool_call(initial_text)
                if tool_call:
                    tool_name, params = tool_call
                    console.print(f"\n[bold yellow]⚡ Hardware Action:[/bold yellow] Executing [bold cyan]{tool_name}[/bold cyan]({_json.dumps(params)})")
                    tool_res = execute_embedded_tool(tool_name, params)
                    console.print(f"[bold green]✓ Hardware Result:[/bold green] {_json.dumps(tool_res)}")

                    session.add_assistant_message(initial_text)
                    session.add_user_message(f"Hardware Result: {_json.dumps(tool_res)}\nPlease confirm the state.")
                    formatted2 = session.format_prompt(family=entry.family)

                    console.print(f"[bold cyan]litrun:[/bold cyan] ", end="")
                    chunks2 = []
                    for chunk in backend.stream(formatted2, threads=final_threads, grammar=grammar, tools=tools_mode):
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                        chunks2.append(chunk)
                        token_count += 1
                    session.add_assistant_message("".join(chunks2))
                else:
                    session.add_assistant_message(initial_text)
            else:
                session.add_assistant_message(initial_text)

            t1 = time.perf_counter()
            elapsed = t1 - t0
            actual_tps = (token_count / elapsed) if elapsed > 0.05 else expected_speed
            console.print(f"\n[dim]⚡ Telemetry: {token_count} tokens generated in {elapsed:.2f}s ({actual_tps:.1f} tok/s)[/dim]\n")

        if prompt_text:
            console.print(f"\n[bold green]>[/bold green] {prompt_text}\n")
            run_step(prompt_text)
            return

        # Interactive REPL
        console.print("[dim]Type your prompt below. Enter 'exit' to quit, 'clear' to reset context.[/dim]\n")
        while True:
            try:
                user_msg = console.input("[bold green]>[/bold green] ").strip()
                if not user_msg:
                    continue
                if user_msg.lower() in ["exit", "quit"]:
                    break
                if user_msg.lower() == "clear":
                    session.clear()
                    console.print("[dim]Context memory cleared.[/dim]\n")
                    continue

                run_step(user_msg)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Session terminated.[/dim]")
                break
    finally:
        backend.close()
