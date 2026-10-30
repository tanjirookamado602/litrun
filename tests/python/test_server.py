import json
import threading
import urllib.request
import urllib.error
from litrun.server import ThreadedHTTPServer, LitrunOpenAIHandler
from litrun.model import Model


def test_rest_server_endpoints():
    # Load mock model instance
    mock_model = Model.load("qwen2.5-0.5b", allow_mock=True)
    LitrunOpenAIHandler.model_instance = mock_model

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

        # 2. Test /v1/hardware
        with urllib.request.urlopen(f"{base_url}/v1/hardware") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "hardware" in data
            assert "governor" in data

        # 3. Test /v1/models
        with urllib.request.urlopen(f"{base_url}/v1/models") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["object"] == "list"
            assert len(data["data"]) > 0

        # 4. Test POST /v1/chat/completions (Non-streaming)
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

        # 5. Test POST /v1/chat/completions (Streaming SSE)
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

        # 6. Test POST /v1/chat/completions with response_format json_object
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

    finally:
        t = threading.Thread(target=server.shutdown, daemon=True)
        t.start()
        t.join(timeout=0.5)
        server.server_close()
