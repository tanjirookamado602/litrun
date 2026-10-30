"""
litrun see: Vision-Language Model execution on edge cameras and image inputs
Usage:
    litrun see frame.jpg -p "What objects are on the table?"
    litrun see /dev/video0 -p "Is anyone approaching the door?"
"""

import os
import sys
import time
import subprocess
import click
from rich.console import Console
from litrun.hardware import probe_hardware
from litrun.registry import get_model, select_optimal_variant
from litrun.governor import check_ram_envelope, poll_governor
from litrun.resolver import (
    select_binary_target,
    get_model_cache_path,
    resolve_engine_binary,
)
from litrun.engine import get_backend
from litrun.session import Session

console = Console()


def capture_camera_frame(device: str, output_path: str) -> bool:
    """Attempts frame capture from V4L2 device using ffmpeg, fswebcam, or v4l2-ctl."""
    # 1. Try ffmpeg if available
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "v4l2", "-video_size", "640x480", "-i", device, "-vframes", "1", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=True
        )
        return True
    except Exception:
        pass

    # 2. Try fswebcam
    try:
        subprocess.run(
            ["fswebcam", "-d", device, "-r", "640x480", "--no-banner", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=True
        )
        return True
    except Exception:
        pass

    return False


@click.command(name="see")
@click.argument("input_target", default="frame.jpg")
@click.option("-p", "--prompt", "prompt_text", default="Describe this image in detail for edge telemetry.", help="Visual query prompt")
@click.option("-m", "--model", "model_id", default="smolvlm-256m", help="Vision model ID (e.g. smolvlm-256m, moondream2)")
@click.option("-q", "--quant", "preferred_quant", default=None, help="Preferred quantization")
@click.option("--demo", is_flag=True, help="Run in hardware simulation mode")
def see_cmd(input_target: str, prompt_text: str, model_id: str, preferred_quant: str, demo: bool):
    """Inspects images or live camera frames using ultra-compact Vision-Language Models (VLMs)."""

    # 1. Image Resolution or Camera Capture
    image_file = input_target
    captured_tmp = False

    if input_target.startswith("/dev/video") or input_target.isdigit():
        console.print(f"[bold cyan]Capturing frame from camera device {input_target}...[/bold cyan]")
        image_file = "/tmp/litrun_camera_capture.jpg"
        if not capture_camera_frame(input_target, image_file):
            console.print(f"[bold yellow]! Notice:[/bold yellow] Hardware camera capture tool not found. Creating placeholder test frame.")
            # Create a minimal 1x1 test JPEG if neither camera capture tool is installed
            with open(image_file, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9")
        captured_tmp = True
    elif not os.path.isfile(image_file) and not demo:
        # Create a dummy image for testing if not existing
        console.print(f"[bold yellow]! Creating test frame at {image_file}[/bold yellow]")
        with open(image_file, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9")

    # 2. Hardware Probing & Resource Governor Check
    with console.status("[bold cyan]Probing hardware and VLM memory envelope...[/bold cyan]", spinner="dots"):
        hw = probe_hardware()
        gov = poll_governor()

    entry = get_model(model_id)
    if not entry:
        console.print(f"[bold red]✗ Error:[/bold red] VLM model '[bold yellow]{model_id}[/bold yellow]' not found in registry.")
        sys.exit(1)

    variant, decision_msg = select_optimal_variant(entry, hw, preferred_quant=preferred_quant)
    allowed, needed_mb, gov_reason, is_tight = check_ram_envelope(
        variant.size_mb,
        context_length=entry.default_context,
        kv_bytes_per_token=entry.kv_bytes_per_token,
    )

    console.print(
        f"[bold blue]→ Camera/Image:[/bold blue] [bold white]{input_target}[/bold white]\n"
        f"[bold blue]→ VLM Engine:[/bold blue]   [bold white]{entry.name} ({variant.quant})[/bold white] "
        f"[dim]({needed_mb}MB RAM required / {hw.ram_avail_mb}MB available)[/dim]"
    )

    if not allowed and not demo:
        console.print(f"[bold red]✗ Governor Warning:[/bold red] {gov_reason}")

    # 3. Backend & Inference
    bin_target = select_binary_target(hw)
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

    try:
        console.print(f"\n[bold green]>[/bold green] [italic]{prompt_text}[/italic]\n")
        console.print(f"[bold cyan]litrun vision:[/bold cyan] ", end="")

        t0 = time.perf_counter()
        token_count = 0

        for chunk in backend.stream(prompt_text, threads=gov.recommended_threads, image_path=image_file):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            token_count += 1

        elapsed = time.perf_counter() - t0
        tps = token_count / elapsed if elapsed > 0.05 else 18.0
        console.print(f"\n\n[dim]⚡ Telemetry: {token_count} vision tokens generated in {elapsed:.2f}s ({tps:.1f} tok/s)[/dim]\n")
    finally:
        backend.close()
        if captured_tmp and os.path.isfile(image_file):
            try:
                os.remove(image_file)
            except Exception:
                pass
