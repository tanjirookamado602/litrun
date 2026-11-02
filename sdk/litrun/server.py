"""
litrun OpenAI-Compatible REST Server & Embedded Web UI Console
Serves /v1/chat/completions, /v1/models, /v1/hardware, /v1/gpio, /v1/benchmark, and /health.
Built with zero required dependencies using standard library ThreadingHTTPServer.
"""

from __future__ import annotations
import json
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from litrun import __version__
from litrun.hardware import probe_hardware
from litrun.governor import poll_governor
from litrun.registry import list_models, get_model
from litrun.tools import gpio_write, gpio_read, gpio_get_all, get_hardware_telemetry
from litrun.ui import get_ui_html

if TYPE_CHECKING:
    from litrun.model import Model


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class LitrunOpenAIHandler(BaseHTTPRequestHandler):
    model_instance: Optional["Model"] = None
    enable_ui: bool = True
    protocol_version = "HTTP/1.1"

    def _send_json(self, status_code: int, data: Any):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def _send_html(self, status_code: int, html_content: str):
        payload = html_content.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        accept_header = self.headers.get("Accept", "")

        # Explicit Health Check
        if self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "litrun_version": __version__,
                "service": "litrun OpenAI-Compatible REST Server",
            })
            return

        # Root route: serve Web UI if HTML accepted or requested, otherwise JSON health check
        if self.path == "/":
            if "application/json" in accept_header and "text/html" not in accept_header:
                self._send_json(200, {
                    "status": "healthy",
                    "litrun_version": __version__,
                    "service": "litrun OpenAI-Compatible REST Server",
                })
            elif self.enable_ui:
                self._send_html(200, get_ui_html(__version__))
            else:
                self._send_json(200, {
                    "status": "healthy",
                    "litrun_version": __version__,
                    "service": "litrun REST Server",
                })
            return

        if self.path == "/ui":
            self._send_html(200, get_ui_html(__version__))
            return

        # Hardware & Governor Telemetry
        if self.path == "/v1/hardware":
            hw = probe_hardware()
            gov = poll_governor()
            telemetry = get_hardware_telemetry()
            self._send_json(200, {
                "hardware": hw.to_dict(),
                "governor": gov.to_dict(),
                "telemetry": telemetry,
            })
            return

        # GPIO Pin Status Matrix
        if self.path == "/v1/gpio":
            gpio_data = gpio_get_all()
            self._send_json(200, gpio_data)
            return

        # Models List
        if self.path == "/v1/models":
            models = list_models()
            data = [
                {
                    "id": m.id,
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "litrun",
                    "name": m.name,
                    "family": m.family,
                    "default_context": m.default_context,
                }
                for m in models
            ]
            self._send_json(200, {"object": "list", "data": data})
            return

        # Live SSE Telemetry Stream
        if self.path == "/v1/telemetry/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                for _ in range(2):
                    hw = probe_hardware()
                    gov = poll_governor()
                    data = {
                        "timestamp": time.time(),
                        "board_id": hw.profile_id,
                        "cpu_temp_c": getattr(gov, "temp_c", 45.0),
                        "ram_avail_mb": gov.ram_avail_mb,
                        "ram_total_mb": hw.ram_total_mb,
                        "thermal_state": 0 if gov.thermal_state == "nominal" else 1,
                        "recommended_threads": gov.recommended_threads,
                    }
                    self.wfile.write(f"data: {json.dumps(data)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
            return

        # Fleet Cluster Status
        if self.path == "/v1/fleet/status":
            from litrun.fleet import FleetManager
            mgr = FleetManager()
            summary = mgr.fleet_telemetry_summary()
            self._send_json(200, {
                "summary": summary,
                "nodes": [n.to_dict() for n in mgr.nodes.values()],
                "rollouts": [r.to_dict() for r in mgr.rollouts.values()],
            })
            return

        self._send_json(404, {"error": {"message": f"Path {self.path} not found"}})

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self._send_json(400, {"error": {"message": f"Invalid JSON payload: {str(e)}"}})
                return

            messages = payload.get("messages", [])
            stream = payload.get("stream", False)
            model_id = payload.get("model", "qwen2.5-0.5b")
            response_format = payload.get("response_format")

            model = LitrunOpenAIHandler.model_instance
            if model is None:
                from litrun.model import Model
                model = Model.load(model_id, allow_mock=True)

            # Build prompt
            prompt_parts = []
            for msg in messages:
                prompt_parts.append(f"{msg.get('role', 'user')}: {msg.get('content', '')}")
            prompt = "\n".join(prompt_parts)

            req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created_ts = int(time.time())

            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                for chunk in model.stream(prompt, response_format=response_format):
                    sse_chunk = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model.entry.id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None,
                            }
                        ],
                    }
                    self.wfile.write(f"data: {json.dumps(sse_chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()

                # Termination chunk
                stop_chunk = {
                    "id": req_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model.entry.id,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                self.wfile.write(f"data: {json.dumps(stop_chunk)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                self.close_connection = True
            else:
                full_response = model.generate(prompt, response_format=response_format)
                resp = {
                    "id": req_id,
                    "object": "chat.completion",
                    "created": created_ts,
                    "model": model.entry.id,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": full_response,
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(prompt) // 4,
                        "completion_tokens": len(full_response) // 4,
                        "total_tokens": (len(prompt) + len(full_response)) // 4,
                    },
                }
                self._send_json(200, resp)

        elif self.path == "/v1/gpio":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self._send_json(400, {"error": {"message": f"Invalid JSON payload: {str(e)}"}})
                return

            pin = int(payload.get("pin", 0))
            action = payload.get("action", "write")
            if action == "read":
                result = gpio_read(pin)
            else:
                val = int(payload.get("value", payload.get("state", 0)))
                result = gpio_write(pin, val)
            self._send_json(200, result)

        elif self.path == "/v1/benchmark":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                payload = {}

            prompt = payload.get("prompt", "Benchmark edge runtime throughput.")
            model = LitrunOpenAIHandler.model_instance
            if model is None:
                from litrun.model import Model
                model = Model.load("qwen2.5-0.5b", allow_mock=True)

            t0 = time.time()
            result_text = model.generate(prompt)
            elapsed = max(0.001, time.time() - t0)
            tokens_est = max(10, len(result_text) // 4)
            tps = round(tokens_est / elapsed, 2)

            self._send_json(200, {
                "status": "success",
                "model": model.entry.id,
                "tokens_generated": tokens_est,
                "duration_seconds": round(elapsed, 4),
                "tokens_per_second": tps,
                "result_sample": result_text[:80],
            })

        elif self.path == "/v1/fleet/enroll":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            from litrun.fleet import FleetManager, FleetNodeProfile
            mgr = FleetManager()
            profile = FleetNodeProfile.from_dict(payload)
            mgr.enroll_node(profile)
            self._send_json(200, {"status": "enrolled", "node_id": profile.node_id})

        elif self.path == "/v1/fleet/deploy":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            from litrun.fleet import FleetManager, OTAPackage
            mgr = FleetManager()
            model_id = payload.get("model_id", "smollm2-135m")
            version = payload.get("version", "1.2.0")
            quant = payload.get("quant", "Q4_0")
            strategy = payload.get("strategy", "canary")
            canary_ratio = float(payload.get("canary_ratio", 0.25))
            pkg_id = f"pkg-{uuid.uuid4().hex[:8]}"

            pkg = OTAPackage(
                package_id=pkg_id,
                target_model=model_id,
                target_quant=quant,
                target_version=version,
                sha256_checksum=uuid.uuid4().hex,
                rollout_strategy=strategy,
                canary_ratio=canary_ratio,
                rollback_on_throttle=True,
                created_at=time.time(),
            )
            pkg.signature = pkg.compute_signature(mgr.secret)
            rollout = mgr.create_ota_deployment(pkg)
            self._send_json(200, {
                "status": "success",
                "package": pkg.to_dict(),
                "rollout": rollout.to_dict(),
            })

        elif self.path == "/v1/fleet/evaluate":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            from litrun.fleet import FleetManager
            mgr = FleetManager()
            pkg_id = payload.get("package_id")
            if not pkg_id and mgr.rollouts:
                pkg_id = list(mgr.rollouts.keys())[-1]

            if not pkg_id:
                self._send_json(400, {"error": "No package_id specified or available"})
                return

            promoted, reason = mgr.evaluate_canary(pkg_id)
            self._send_json(200, {
                "package_id": pkg_id,
                "promoted": promoted,
                "reason": reason,
                "phase": mgr.rollouts.get(pkg_id).phase if pkg_id in mgr.rollouts else "unknown",
            })

        elif self.path == "/v1/fleet/rollback":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            from litrun.fleet import FleetManager
            mgr = FleetManager()
            node_id = payload.get("node_id")
            reverted = mgr.trigger_rollback(node_id)
            self._send_json(200, {
                "status": "rolled_back",
                "reverted_nodes": reverted,
                "count": len(reverted),
            })

        elif self.path == "/v1/fleet/seed_demo":
            from litrun.fleet import FleetManager, FleetNodeProfile
            mgr = FleetManager()
            demo_nodes = [
                FleetNodeProfile(
                    node_id="rpi5-gateway-01",
                    hostname="rpi5-gateway",
                    board_name="Raspberry Pi 5",
                    soc="BCM2712 (Cortex-A76)",
                    ram_total_mb=8192,
                    ram_avail_mb=5840,
                    cpu_temp_c=46.2,
                    thermal_state=0,
                    current_model="smollm2-135m",
                    current_model_version="1.2.0",
                    installed_models=["smollm2-135m", "qwen2.5-0.5b"],
                    status="healthy",
                    last_heartbeat=time.time(),
                    firmware_version="0.9.0",
                ),
                FleetNodeProfile(
                    node_id="opi5-npu-worker-02",
                    hostname="opi5-npu-worker",
                    board_name="Orange Pi 5 Plus",
                    soc="RK3588 (6.0 TOPS NPU)",
                    ram_total_mb=16384,
                    ram_avail_mb=12950,
                    cpu_temp_c=48.8,
                    thermal_state=0,
                    current_model="smollm2-135m",
                    current_model_version="1.2.0",
                    installed_models=["smollm2-135m", "smolvlm-256m"],
                    status="healthy",
                    last_heartbeat=time.time(),
                    firmware_version="0.9.0",
                ),
                FleetNodeProfile(
                    node_id="jetson-orin-vision-03",
                    hostname="jetson-orin-edge",
                    board_name="NVIDIA Jetson Orin Nano",
                    soc="Tegra Orin (Ampere GPU)",
                    ram_total_mb=8192,
                    ram_avail_mb=5120,
                    cpu_temp_c=52.1,
                    thermal_state=0,
                    current_model="qwen2.5-0.5b",
                    current_model_version="1.0.0",
                    installed_models=["qwen2.5-0.5b", "moondream2"],
                    status="healthy",
                    last_heartbeat=time.time(),
                    firmware_version="0.9.0",
                ),
                FleetNodeProfile(
                    node_id="milkv-pioneer-riscv-04",
                    hostname="milkv-rvv-server",
                    board_name="Milk-V Pioneer",
                    soc="SG2042 64-Core (RVV Vector 1.0)",
                    ram_total_mb=32768,
                    ram_avail_mb=28400,
                    cpu_temp_c=49.4,
                    thermal_state=0,
                    current_model="smollm2-360m",
                    current_model_version="1.0.0",
                    installed_models=["smollm2-135m", "smollm2-360m"],
                    status="healthy",
                    last_heartbeat=time.time(),
                    firmware_version="0.9.0",
                ),
            ]
            for n in demo_nodes:
                mgr.enroll_node(n)
            summary = mgr.fleet_telemetry_summary()
            self._send_json(200, {
                "status": "seeded",
                "nodes": [n.to_dict() for n in mgr.nodes.values()],
                "summary": summary,
            })

        else:
            self._send_json(404, {"error": {"message": f"Endpoint {self.path} not found"}})


def start_server(
    model: Optional["Model"] = None,
    host: str = "0.0.0.0",
    port: int = 8080,
    model_id: str = "qwen2.5-0.5b",
    ui: bool = True,
) -> None:
    if model is None:
        from litrun.model import Model
        model = Model.load(model_id, allow_mock=True)

    LitrunOpenAIHandler.model_instance = model
    LitrunOpenAIHandler.enable_ui = ui
    server = ThreadedHTTPServer((host, port), LitrunOpenAIHandler)
    print(f"\n⚡ litrun REST Server active at http://{host}:{port}")
    if ui:
        print(f"   Web UI Dashboard:   http://{host}:{port}/")
    print(f"   Model:              {model.entry.name} ({model.variant.quant})")
    print(f"   OpenAI Endpoint:    http://{host}:{port}/v1/chat/completions")
    print(f"   Hardware Telemetry: http://{host}:{port}/v1/hardware")
    print(f"   GPIO Pin Matrix:    http://{host}:{port}/v1/gpio")
    print("Press Ctrl+C to stop server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down litrun server...")
        server.server_close()
