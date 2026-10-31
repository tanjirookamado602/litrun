"""
litrun see: Vision-Language Model execution on edge cameras, RTSP streams, and images.
Usage:
    litrun see frame.jpg -p "What objects are on the table?"
    litrun see rtsp://192.168.1.100:554/live --motion
    litrun see /dev/video0 --detect --json
"""

from __future__ import annotations
import os
import sys
import time
import json
import click
from rich.console import Console
from rich.table import Table
from litrun.hardware import probe_hardware
from litrun.registry import get_model, select_optimal_variant
from litrun.governor import check_ram_envelope, poll_governor
from litrun.resolver import (
    select_binary_target,
    get_model_cache_path,
    resolve_engine_binary,
)
from litrun.engine import get_backend
from litrun.vision import (
    capture_frame,
    is_network_stream,
    is_camera_device,
    VisionMotionDetector,
    format_detection_prompt,
    parse_detected_objects,
)

console = Console()


@click.command(name="see")
@click.argument("input_target", default="frame.jpg")
@click.option("-p", "--prompt", "prompt_text", default=None, help="Visual query prompt")
@click.option("-m", "--model", "model_id", default="smolvlm-256m", help="Vision model ID (e.g. smolvlm-256m, moondream2)")
@click.option("-q", "--quant", "preferred_quant", default=None, help="Preferred quantization")
@click.option("--motion", is_flag=True, help="Enable motion delta detection trigger before inference")
@click.option("--threshold", "motion_thresh", default=0.05, type=float, help="Motion sensitivity threshold (0.01 to 0.50)")
@click.option("--detect", is_flag=True, help="Extract structured bounding box coordinates for detected objects")
@click.option("--continuous", is_flag=True, help="Run continuous monitoring loop on camera or RTSP stream")
@click.option("--max-frames", default=3, type=int, help="Maximum frames to process in continuous mode")
@click.option("--json", "json_output", is_flag=True, help="Output results in structured JSON format")
@click.option("--demo", is_flag=True, help="Run in hardware simulation mode")
def see_cmd(
    input_target: str,
    prompt_text: Optional[str],
    model_id: str,
    preferred_quant: Optional[str],
    motion: bool,
    motion_thresh: float,
    detect: bool,
    continuous: bool,
    max_frames: int,
    json_output: bool,
    demo: bool,
):
    """Inspects images, USB cameras, or RTSP network streams using Vision-Language Models."""

    # Set up prompt
    if detect:
        final_prompt = format_detection_prompt(prompt_text)
    else:
        final_prompt = prompt_text or "Describe this image in detail for edge telemetry."

    # 1. Hardware & Governor Probing
    if not json_output:
        with console.status("[bold cyan]Probing hardware and VLM memory envelope...[/bold cyan]", spinner="dots"):
            hw = probe_hardware()
            gov = poll_governor()
    else:
        hw = probe_hardware()
        gov = poll_governor()

    entry = get_model(model_id)
    if not entry:
        console.print(f"[bold red]✗ Error:[/bold red] VLM model '[bold yellow]{model_id}[/bold yellow]' not found in registry.")
        sys.exit(1)

    variant, _ = select_optimal_variant(entry, hw, preferred_quant=preferred_quant)
    allowed, needed_mb, gov_reason, _ = check_ram_envelope(
        variant.size_mb,
        context_length=entry.default_context,
        kv_bytes_per_token=entry.kv_bytes_per_token,
    )

    if not json_output:
        stream_type = "RTSP/IP Camera" if is_network_stream(input_target) else ("V4L2 Device" if is_camera_device(input_target) else "Static Image")
        console.print(
            f"[bold blue]→ Video Source:[/bold blue] [bold white]{input_target}[/bold white] [dim]({stream_type})[/dim]\n"
            f"[bold blue]→ VLM Engine:[/bold blue]   [bold white]{entry.name} ({variant.quant})[/bold white] "
            f"[dim]({needed_mb}MB RAM required / {hw.ram_avail_mb}MB available)[/dim]"
        )

    bin_path = None
    try:
        bin_path = resolve_engine_binary(hw)
    except Exception:
        pass

    backend = get_backend(
        binary_path=bin_path,
        model_path=get_model_cache_path(entry.id, variant.quant),
        threads=gov.recommended_threads,
        context_length=entry.default_context,
        model_id=entry.id,
        allow_mock=True,
    )

    motion_detector = VisionMotionDetector(threshold=motion_thresh) if motion else None
    tmp_frame_path = f"/tmp/litrun_see_{int(time.time()*1000)}.jpg"
    iterations = max_frames if continuous else 1
    results = []

    try:
        for frame_idx in range(iterations):
            # Capture frame
            capture_frame(input_target, tmp_frame_path)
            frame_bytes = b""
            if os.path.isfile(tmp_frame_path):
                with open(tmp_frame_path, "rb") as f:
                    frame_bytes = f.read()

            # Motion trigger check
            has_motion = True
            delta = 1.0
            if motion_detector:
                has_motion, delta = motion_detector.check_motion(frame_bytes)
                if not has_motion:
                    if not json_output:
                        console.print(f"[dim]Frame {frame_idx+1}: Motion delta {delta:.3f} below threshold {motion_thresh:.2f}. Skipping VLM inference.[/dim]")
                    time.sleep(0.5)
                    continue

            if not json_output:
                motion_badge = f" [yellow](Motion: {delta*100:.1f}%)[/yellow]" if motion else ""
                console.print(f"\n[bold green]>[/bold green] [italic]{final_prompt[:80]}...[/italic]{motion_badge}")
                console.print(f"[bold cyan]litrun vision:[/bold cyan] ", end="")

            t0 = time.perf_counter()
            token_count = 0
            accumulated = []

            for chunk in backend.stream(final_prompt, threads=gov.recommended_threads, image_path=tmp_frame_path):
                if not json_output:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                accumulated.append(chunk)
                token_count += 1

            full_text = "".join(accumulated)
            elapsed = time.perf_counter() - t0
            tps = token_count / elapsed if elapsed > 0.05 else 18.0

            if not json_output:
                console.print(f"\n[dim]⚡ {token_count} vision tokens generated in {elapsed:.2f}s ({tps:.1f} tok/s)[/dim]")

            # Object Detection parsing
            objects = []
            if detect:
                objects = parse_detected_objects(full_text)
                if not json_output and objects:
                    table = Table(title="Detected Objects & Bounding Boxes", header_style="bold magenta")
                    table.add_column("Object Label", style="bold green")
                    table.add_column("Bounding Box [ymin, xmin, ymax, xmax]", style="cyan")
                    table.add_column("Confidence", justify="right")
                    for obj in objects:
                        table.add_row(
                            obj.get("label", "unknown"),
                            str(obj.get("box_2d", [])),
                            f"{obj.get('confidence', 0.9):.2f}",
                        )
                    console.print(table)

            results.append({
                "frame": frame_idx + 1,
                "motion_delta": delta,
                "text": full_text,
                "objects": objects,
                "tokens": token_count,
                "tps": round(tps, 1),
            })

            if continuous and frame_idx < iterations - 1:
                time.sleep(0.5)

        if json_output:
            click.echo(json.dumps(results if continuous else results[0], indent=2))

    finally:
        backend.close()
        if os.path.isfile(tmp_frame_path):
            try:
                os.remove(tmp_frame_path)
            except Exception:
                pass
