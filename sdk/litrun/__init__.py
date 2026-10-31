"""
litrun: Universal Lightweight Embedded Linux AI Runtime
"""

from litrun.hardware import HardwareProfile, probe_hardware
from litrun.governor import GovernorStatus, poll_governor, check_ram_envelope
from litrun.model import Model
from litrun.registry import ModelEntry, ModelVariant, list_models, get_model
from litrun.grammar import resolve_grammar, json_schema_to_gbnf, STANDARD_JSON_GBNF
from litrun.tools import (
    GPIOController,
    gpio_write,
    gpio_read,
    gpio_get_all,
    get_hardware_telemetry,
    COMMON_PINS,
    parse_tool_call,
    execute_embedded_tool,
)
from litrun.rknn import (
    RKNNInfo,
    probe_rknn,
    RKNNRuntime,
)
from litrun.jetson import (
    JetsonInfo,
    probe_jetson,
    JetsonRuntime,
)
from litrun.rag import (
    EdgeVectorStore,
    compute_lightweight_embedding,
    build_rag_augmented_prompt,
)
from litrun.mqtt import (
    MQTTTelemetryAgent,
    build_mqtt_connect_packet,
    build_mqtt_publish_packet,
)

__version__ = "0.5.0"

__all__ = [
    "Model",
    "HardwareProfile",
    "probe_hardware",
    "GovernorStatus",
    "poll_governor",
    "check_ram_envelope",
    "ModelEntry",
    "ModelVariant",
    "list_models",
    "get_model",
    "resolve_grammar",
    "json_schema_to_gbnf",
    "STANDARD_JSON_GBNF",
    "GPIOController",
    "gpio_write",
    "gpio_read",
    "gpio_get_all",
    "get_hardware_telemetry",
    "COMMON_PINS",
    "parse_tool_call",
    "execute_embedded_tool",
    "RKNNInfo",
    "probe_rknn",
    "RKNNRuntime",
    "JetsonInfo",
    "probe_jetson",
    "JetsonRuntime",
    "EdgeVectorStore",
    "compute_lightweight_embedding",
    "build_rag_augmented_prompt",
    "MQTTTelemetryAgent",
    "build_mqtt_connect_packet",
    "build_mqtt_publish_packet",
    "__version__",
]

