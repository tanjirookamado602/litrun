"""
litrun mqtt: Industrial MQTT Sensor Telemetry Daemon & Edge Agent CLI
"""

import json
import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from litrun.mqtt import MQTTTelemetryAgent

console = Console()


@click.command(name="mqtt")
@click.option("--broker", default="localhost", help="MQTT broker host (default: localhost)")
@click.option("--port", default=1883, type=int, help="MQTT broker port (default: 1883)")
@click.option("--topic", default="factory/sensors/#", help="Telemetry topic to subscribe to")
@click.option("--alert-topic", default="factory/alerts", help="Actuator/Alert topic to publish to")
@click.option("--model", "model_id", default="qwen2.5-0.5b", help="Local evaluator model")
@click.option("--demo", is_flag=True, default=False, help="Run an interactive edge sensor telemetry demonstration")
def mqtt_cmd(
    broker: str,
    port: int,
    topic: str,
    alert_topic: str,
    model_id: str,
    demo: bool,
):
    """Subscribes to MQTT sensor telemetry streams and evaluates anomalies locally."""
    console.print(
        Panel(
            f"[bold green]⚡ litrun Industrial MQTT Edge Agent[/bold green]\n"
            f"[cyan]Broker:[/cyan] {broker}:{port}\n"
            f"[cyan]Subscribed Topic:[/cyan] {topic}\n"
            f"[cyan]Alert Topic:[/cyan] {alert_topic}\n"
            f"[cyan]Evaluator Model:[/cyan] {model_id} (Zero cloud latency)",
            title="[bold]IoT Edge Daemon[/bold]",
            border_style="green",
        )
    )

    agent = MQTTTelemetryAgent(
        broker_host=broker,
        broker_port=port,
        topic=topic,
        alert_topic=alert_topic,
        model_id=model_id,
        mock=demo,
    )
    agent.connect()

    if demo:
        console.print("\n[bold yellow]Streaming live industrial telemetry events...[/bold yellow]\n")

        events = [
            {"sensor": "boiler_temp_c", "value": 68.2, "unit": "°C"},
            {"sensor": "turbine_vibration", "value": 9.4, "unit": "mm/s"},
            {"sensor": "bearing_temp_c", "value": 84.1, "unit": "°C"},
        ]

        table = Table(title="Edge Model Telemetry Evaluation", show_header=True, header_style="bold magenta")
        table.add_column("Sensor Metric", style="bold white", width=20)
        table.add_column("Value", style="cyan", width=12)
        table.add_column("AI Assessment", width=18)
        table.add_column("Autonomous Action", style="bold yellow")

        for ev in events:
            time.sleep(0.08)
            decision = agent.evaluate_telemetry(ev)
            agent.publish_alert(decision)

            status_style = "[bold red]CRITICAL[/bold red]" if decision["status"] == "CRITICAL_ANOMALY" else "[bold green]NOMINAL[/bold green]"
            table.add_row(
                ev["sensor"],
                f"{ev['value']}{ev['unit']}",
                status_style,
                f"{decision['action_required']} ({decision['reasoning']})"
            )

        console.print(table)
        console.print(f"\n[bold green]✓ Published autonomous actions to '{alert_topic}' via MQTT.[/bold green]")
        agent.close()
        return

    console.print(f"[bold cyan]Agent active. Listening for telemetry on '{topic}'... (Press Ctrl+C to stop)[/bold cyan]")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping MQTT agent daemon...[/yellow]")
        agent.close()
