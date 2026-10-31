"""
litrun: Universal Lightweight Embedded Linux AI Runtime
"""

__version__ = "0.9.0"

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
from litrun.benchmark import (
    BenchmarkResult,
    BenchmarkReport,
    run_single_benchmark,
    run_benchmark_matrix,
    run_backend_comparison,
    get_public_leaderboard,
    export_leaderboard_json,
    LeaderboardEntry,
)
from litrun.vision import (
    capture_frame,
    VisionMotionDetector,
    compute_frame_motion_delta,
    format_detection_prompt,
    parse_detected_objects,
)
from litrun.engine_ffi import CtypesLlamaEngine
from litrun.swarm import (
    SwarmNode,
    SwarmMesh,
    SwarmRouter,
    SwarmBeacon,
)
from litrun.lora import (
    LoRAConfig,
    LoRALayer,
    LoRAAdapter,
)
from litrun.packaging import (
    build_deb_package,
    create_control_archive,
    create_data_archive,
)
from litrun.modelfile import (
    ParsedModelfile,
    ModelfileParser,
    CustomModelManifest,
    save_custom_model,
    get_custom_model,
    list_custom_models,
    delete_custom_model,
    export_custom_model_pack,
    import_custom_model_pack,
)
from litrun.quantize import (
    quantize_weights,
    quantize_f32_to_q8_0,
    dequantize_q8_0,
    quantize_f32_to_q4_0,
    dequantize_q4_0,
    estimate_ram_footprint,
    save_litquant,
    load_litquant,
    QuantizationMetrics,
)
from litrun.fleet import (
    FleetNodeProfile,
    OTAPackage,
    RolloutState,
    FleetManager,
    create_local_fleet_node,
)

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
    "BenchmarkResult",
    "BenchmarkReport",
    "run_single_benchmark",
    "run_benchmark_matrix",
    "run_backend_comparison",
    "get_public_leaderboard",
    "export_leaderboard_json",
    "LeaderboardEntry",
    "capture_frame",
    "VisionMotionDetector",
    "compute_frame_motion_delta",
    "format_detection_prompt",
    "parse_detected_objects",
    "CtypesLlamaEngine",
    "SwarmNode",
    "SwarmMesh",
    "SwarmRouter",
    "SwarmBeacon",
    "LoRAConfig",
    "LoRALayer",
    "LoRAAdapter",
    "build_deb_package",
    "create_control_archive",
    "create_data_archive",
    "ParsedModelfile",
    "ModelfileParser",
    "CustomModelManifest",
    "save_custom_model",
    "get_custom_model",
    "list_custom_models",
    "delete_custom_model",
    "export_custom_model_pack",
    "import_custom_model_pack",
    "quantize_weights",
    "quantize_f32_to_q8_0",
    "dequantize_q8_0",
    "quantize_f32_to_q4_0",
    "dequantize_q4_0",
    "estimate_ram_footprint",
    "save_litquant",
    "load_litquant",
    "QuantizationMetrics",
    "FleetNodeProfile",
    "OTAPackage",
    "RolloutState",
    "FleetManager",
    "create_local_fleet_node",
    "__version__",
]

