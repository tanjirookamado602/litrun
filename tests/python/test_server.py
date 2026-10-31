import json
import threading
import urllib.request
import urllib.error
from click.testing import CliRunner
from litrun.server import ThreadedHTTPServer, LitrunOpenAIHandler
from litrun.model import Model
from litrun.cli.cmd_ui import ui_cmd


def test_rest_server_endpoints():
    # Load mock model instance
    mock_model = Model.load("qwen2.5-0.5b", allow_mock=True)
    LitrunOpenAIHandler.model_instance = mock_model
    LitrunOpenAIHandler.enable_ui = True

    # Bind to ephemeral port
    server = ThreadedHTTPServer(("127.0.0.1", 0), LitrunOpenAIHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Test /health
        with urllib.request.urlopen(f"{base_url}/health") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"

        # 2. Test / (Web UI HTML)
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            content_type = resp.headers.get("Content-Type", "")
            assert "text/html" in content_type
            html_text = resp.read().decode("utf-8")
            assert "litrun Edge AI Console" in html_text
            assert "Playground" in html_text
            assert "GPIO Matrix" in html_text

        # 3. Test /ui route
        with urllib.request.urlopen(f"{base_url}/ui") as resp:
            assert resp.status == 200
            html_text = resp.read().decode("utf-8")
            assert "litrun" in html_text

        # 4. Test / with Accept: application/json
        req_root_json = urllib.request.Request(
            f"{base_url}/",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req_root_json) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"

        # 5. Test /v1/hardware
        with urllib.request.urlopen(f"{base_url}/v1/hardware") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "hardware" in data
            assert "governor" in data
            assert "telemetry" in data

        # 6. Test /v1/gpio GET
        with urllib.request.urlopen(f"{base_url}/v1/gpio") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["success"] is True
            assert "pins" in data
            assert "mode" in data

        # 7. Test /v1/gpio POST (write pin)
        gpio_post = json.dumps({"pin": 17, "value": 1}).encode("utf-8")
        req_gpio = urllib.request.Request(
            f"{base_url}/v1/gpio",
            data=gpio_post,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_gpio) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["success"] is True
            assert data["pin"] == 17
            assert data["state"] == 1

        # 8. Test /v1/benchmark POST
        bench_post = json.dumps({"prompt": "Benchmark test prompt"}).encode("utf-8")
        req_bench = urllib.request.Request(
            f"{base_url}/v1/benchmark",
            data=bench_post,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_bench) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert "tokens_generated" in data
            assert "tokens_per_second" in data

        # 9. Test /v1/models
        with urllib.request.urlopen(f"{base_url}/v1/models") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["object"] == "list"
            assert len(data["data"]) > 0

        # 10. Test POST /v1/chat/completions (Non-streaming)
        post_data = json.dumps({
            "model": "qwen2.5-0.5b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=post_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["object"] == "chat.completion"
            assert len(data["choices"]) > 0
            assert "content" in data["choices"][0]["message"]

        # 11. Test POST /v1/chat/completions (Streaming SSE)
        stream_data = json.dumps({
            "model": "qwen2.5-0.5b",
            "messages": [{"role": "user", "content": "Explain edge AI"}],
            "stream": True,
        }).encode("utf-8")

        req_stream = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=stream_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_stream) as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "data: " in content
            assert "data: [DONE]" in content

        # 12. Test POST /v1/chat/completions with response_format json_object
        json_req_data = json.dumps({
            "model": "qwen2.5-0.5b",
            "messages": [{"role": "user", "content": "Return telemetry"}],
            "response_format": {"type": "json_object"},
            "stream": False,
        }).encode("utf-8")

        req_json = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=json_req_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_json) as resp:
            assert resp.status == 200
            res_json = json.loads(resp.read().decode("utf-8"))
            content_str = res_json["choices"][0]["message"]["content"]
            parsed = json.loads(content_str)
            assert parsed.get("status") == "ok"

        # 13. Test GET /v1/telemetry/stream (SSE)
        with urllib.request.urlopen(f"{base_url}/v1/telemetry/stream") as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "data: " in content
            assert "cpu_temp_c" in content

        # 14. Test GET /v1/fleet/status
        with urllib.request.urlopen(f"{base_url}/v1/fleet/status") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "summary" in data
            assert "nodes" in data

        # 15. Test POST /v1/fleet/enroll
        enroll_post = json.dumps({
            "node_id": "test-web-node-01",
            "hostname": "pi5-box",
            "board_name": "Raspberry Pi 5",
            "soc": "BCM2712",
            "ram_total_mb": 8192,
            "ram_avail_mb": 4096,
            "cpu_temp_c": 49.0,
            "thermal_state": 0,
            "current_model": "smollm2-135m",
            "current_model_version": "1.0.0",
        }).encode("utf-8")
        req_enroll = urllib.request.Request(
            f"{base_url}/v1/fleet/enroll",
            data=enroll_post,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_enroll) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "enrolled"
            assert data["node_id"] == "test-web-node-01"

    finally:
        t = threading.Thread(target=server.shutdown, daemon=True)
        t.start()
        t.join(timeout=0.5)
        server.server_close()


def test_cli_ui_help():
    runner = CliRunner()
    result = runner.invoke(ui_cmd, ["--help"])
    assert result.exit_code == 0
    assert "Launch the litrun visual Web UI device dashboard" in result.output
    assert "--port" in result.output
    assert "--host" in result.output
