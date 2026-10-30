"""
litrun Embedded Hardware Tool Dispatcher & Execution Engine
Enables small edge LLMs (SmolLM2, Qwen2.5-0.5B, TinyLlama) to perform autonomous
actuation and telemetry via direct Linux sysfs and hardware probes.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from litrun.tools.gpio import gpio_write, gpio_read, get_hardware_telemetry


EMBEDDED_TOOLS = [
    {
        "name": "gpio_write",
        "description": "Drive a hardware GPIO pin HIGH (1) or LOW (0) to control relays, LEDs, cooling fans, or motors.",
        "parameters": {
            "type": "object",
            "properties": {
                "pin": {"type": "integer", "description": "Linux GPIO pin number"},
                "value": {"type": "integer", "enum": [0, 1], "description": "1 for HIGH / ON, 0 for LOW / OFF"},
            },
            "required": ["pin", "value"],
        },
    },
    {
        "name": "gpio_read",
        "description": "Read the digital state (0 or 1) of a hardware GPIO pin from buttons, PIR sensors, or switches.",
        "parameters": {
            "type": "object",
            "properties": {
                "pin": {"type": "integer", "description": "Linux GPIO pin number"},
            },
            "required": ["pin"],
        },
    },
    {
        "name": "get_hardware_telemetry",
        "description": "Retrieve host SoC CPU temperature, load average, and thermal governor status.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]

EMBEDDED_TOOLS_SYSTEM_PROMPT = """You are an autonomous edge AI controller running on embedded Linux.
You have direct hardware access to GPIO pins and SoC telemetry.
To execute a hardware action, output a single JSON tool call block in this format:
{"tool": "<tool_name>", "parameters": {<arguments>}}

Available Tools:
1. gpio_write(pin: int, value: int) -> Control relays, fans, LEDs, motors (1=HIGH/ON, 0=LOW/OFF).
2. gpio_read(pin: int) -> Read digital state (0 or 1) from sensors or buttons.
3. get_hardware_telemetry() -> Read CPU temperature (°C), load average, and thermal throttling state.

If the user request requires hardware actuation or sensor telemetry, emit the JSON tool call block directly.
Once tool results are provided to you, explain the outcome concisely.
"""


def parse_tool_call(output_text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parses a tool call from LLM output.
    Supports raw JSON or markdown code blocks (```json ... ``` or ```tool_call ... ```).
    Returns (tool_name, parameters) or None.
    """
    cleaned = output_text.strip()

    # Match fenced code blocks
    code_block_match = re.search(r"```(?:json|tool_call)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if code_block_match:
        cleaned = code_block_match.group(1).strip()
    else:
        # Check if text contains JSON object
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            cleaned = json_match.group(0).strip()

    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            return None

        # Format A: {"tool": "gpio_write", "parameters": {...}}
        if "tool" in data:
            tool_name = str(data["tool"])
            params = data.get("parameters", {})
            return tool_name, params if isinstance(params, dict) else {}

        # Format B: OpenAI-style {"name": "gpio_write", "arguments": {...}}
        if "name" in data:
            tool_name = str(data["name"])
            params = data.get("arguments", {})
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except Exception:
                    params = {}
            return tool_name, params if isinstance(params, dict) else {}

        # Format C: {"function": "gpio_write", "parameters": {...}}
        if "function" in data:
            tool_name = str(data["function"])
            params = data.get("parameters", {})
            return tool_name, params if isinstance(params, dict) else {}

    except Exception:
        pass

    return None


def execute_embedded_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Executes the requested embedded tool and returns JSON-serializable output."""
    if tool_name == "gpio_write":
        pin = int(parameters.get("pin", 0))
        value = int(parameters.get("value", 0))
        return gpio_write(pin=pin, value=value)

    elif tool_name == "gpio_read":
        pin = int(parameters.get("pin", 0))
        return gpio_read(pin=pin)

    elif tool_name == "get_hardware_telemetry":
        return get_hardware_telemetry()

    else:
        return {
            "success": False,
            "error": f"Unknown tool '{tool_name}'. Available: gpio_write, gpio_read, get_hardware_telemetry",
        }
