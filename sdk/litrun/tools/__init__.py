"""
litrun Embedded Hardware Tools & Agent Dispatcher
Direct POSIX sysfs GPIO and telemetry tools for edge AI autonomy.
"""

from litrun.tools.gpio import (
    GPIOController,
    gpio_write,
    gpio_read,
    gpio_get_all,
    get_hardware_telemetry,
    COMMON_PINS,
)
from litrun.tools.dispatcher import (
    EMBEDDED_TOOLS,
    EMBEDDED_TOOLS_SYSTEM_PROMPT,
    parse_tool_call,
    execute_embedded_tool,
)

__all__ = [
    "GPIOController",
    "gpio_write",
    "gpio_read",
    "gpio_get_all",
    "get_hardware_telemetry",
    "COMMON_PINS",
    "EMBEDDED_TOOLS",
    "EMBEDDED_TOOLS_SYSTEM_PROMPT",
    "parse_tool_call",
    "execute_embedded_tool",
]
