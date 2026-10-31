# ⚡ litrun

[![CI Matrix](https://github.com/assassinaj602/litrun/actions/workflows/ci.yml/badge.svg)](https://github.com/assassinaj602/litrun/actions)
[![Release & Distribution](https://github.com/assassinaj602/litrun/actions/workflows/release.yml/badge.svg)](https://github.com/assassinaj602/litrun/releases)
[![PyPI version](https://img.shields.io/pypi/v/litrun.svg?color=blue)](https://pypi.org/project/litrun/)
[![GitHub Pages](https://img.shields.io/badge/Docs%20%26%20Calculator-Live%20Demo-brightgreen.svg)](https://assassinaj602.github.io/litrun)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Supported SoCs](https://img.shields.io/badge/SoCs-BCM2711%20%7C%20BCM2712%20%7C%20RK3588%20%7C%20Jetson%20%7C%20x86__64-green.svg)](#hardware-support-matrix)
[![GitHub release](https://img.shields.io/github/v/release/assassinaj602/litrun?color=orange)](https://github.com/assassinaj602/litrun/releases/tag/v0.5.0)

> **Deploy any LLM to any embedded Linux device in one command.**  
> A lightweight, universal open-source runtime that eliminates hardware fragmentation for on-device AI across Raspberry Pi, Orange Pi, industrial SoCs, and ARM64 / RISC-V edge boards.

<p align="center">
  <img src="assets/demo.gif" alt="litrun terminal demo" width="850">
</p>

---

## 🚀 Quickstart: The One Working Moment

### 1. Instant POSIX Bootstrap (No toolchains, no cmake)
```bash
curl -sSL https://raw.githubusercontent.com/assassinaj602/litrun/main/scripts/install.sh | sh
```
*Or via pip:*
```bash
pip install litrun
```

### 2. Inspect Hardware Vector Capabilities (<5ms)
```bash
litrun inspect
```

### 3. Run Your First Model With Zero Guesswork
```bash
litrun run qwen2.5-0.5b
```

```text
→ Detected: Raspberry Pi 5 Model B (BCM2712 Cortex-A76, 8192 MB RAM)
→ Selected: qwen2.5-0.5b-Q4_K_M (optimal RAM envelope: 900MB required / 6800MB free)
→ Binary:   pulling precompiled ARM64 a76+dotprod build... done [cached]
→ Model:    streaming weights from HuggingFace (397MB)... done
→ Warmup complete. Running at 14.2 tokens/sec on 4 threads. Type to interact.

> Hello litrun! How do you prevent out-of-memory crashes on embedded devices?
litrun: I integrate a dedicated C resource governor that inspects Linux memory
cgroups and /proc/meminfo before model allocation, preventing kernel OOM-killer panics.
```

---

## 🧠 Why Litrun Exists

| The Amateur Edge AI Struggle | The Litrun Way |
| :--- | :--- |
| **45-minute on-device compilation** on Pi 4 that thermal throttles and crashes during linking. | **Instant prebuilt binaries** cross-compiled per microarchitecture (Cortex-A72 NEON, Cortex-A76 DotProd). |
| **Quantization guesswork**: Devs guess between Q4_K_M, Q5_K_S, IQ3_XS without knowing if RAM + KV cache fits. | **Hardware-aware envelope**: Evaluates free RAM + KV cache before launch, picking optimal accuracy safely. |
| **Silent kernel panics**: Linux OOM-killer randomly terminates services or hangs the board. | **Active Resource Governor**: Hard memory ceilings and dynamic thermal throttling. |
| **Disjoint vendor APIs**: llama.cpp, ONNX Runtime, and RKNN share zero API commonality. | **Unified Interface**: One CLI, Python SDK (`from litrun import Model`), and drop-in OpenAI REST API. |

---

## 🏛️ System Architecture

Litrun is architected in 5 decoupled layers:

```
┌────────────────────────────────────────────────────────┐
│  LAYER 1: User Surface (CLI, Python SDK, REST Server)  │
│  litrun run/pull/list/inspect/serve • from litrun import Model  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  LAYER 2: Orchestration & Active Resource Governor     │
│  RAM Safety Ceiling (85%) • Cgroup v1/v2 • Thermal Monitor│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  LAYER 3: Hardware Abstraction Native Engine (Pure C99) │
│  Devicetree • Aux Vector (NEON, DotProd, i8mm) • <5ms  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  LAYER 4: Pluggable Inference Backends                 │
│  llama.cpp (ARM DotProd) • RKNN NPU • ONNX Runtime     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  LAYER 5: Distributed Metadata Registries (Flat YAML)   │
│  models.yaml • hardware.yaml • binaries.yaml (GitHub CDN) │
└────────────────────────────────────────────────────────┘
```

---

## 💻 Python SDK Usage

```python
from litrun import Model, probe_hardware, poll_governor

# 1. Inspect hardware and active memory governor
hw = probe_hardware()
print(f"Board: {hw.board_name} | Profile: {hw.profile_id}")
print(f"Vector Acceleration: NEON={hw.has_neon}, DotProd={hw.has_dotprod}")

# 2. Automatically resolves hardware, checks RAM envelope, pulls weights
model = Model.load("qwen2.5-0.5b")

# 3. Stream tokens in real time
for chunk in model.stream("Summarize industrial sensor telemetry:"):
    print(chunk, end="", flush=True)

# 4. Or launch the local OpenAI-compatible REST server
# model.serve(host="0.0.0.0", port=8080)
```

---

## 🖥️ Visual Web UI Device Console (`litrun ui`)

Deploy a self-hosted, lightweight responsive Web UI dashboard directly from `litrun` with **zero external dependencies** and 100% offline edge capability:

```bash
# Launch the dashboard and automatically open your browser:
litrun ui

# Or specify model and bind network interface for LAN / phone access:
litrun ui qwen2.5-0.5b --host 0.0.0.0 --port 8080
```

Access the dashboard at `http://<device-ip>:8080`:

| Dashboard Feature | Capability |
| :--- | :--- |
| **Live Telemetry Gauges** | Real-time CPU temperature (°C) gauge, thermal throttling status, active RAM envelope vs cgroups ceiling, and 1-minute load average. |
| **Multimodal Chat Playground** | Interactive streaming chat (SSE) with system prompt editor, temperature/token sliders, quick hardware action chips, and multimodal image upload preview for VLMs. |
| **40-Pin GPIO Matrix** | Interactive visual pin grid for Raspberry Pi GPIOs (Pins 2–27). Real-time digital toggle switches (`HIGH (1)` / `LOW (0)`) via kernel sysfs with automated simulation fallback. |
| **On-Device Benchmarking** | One-click 100-token benchmark evaluating real-time throughput (tok/s), latency, and time-to-first-token (TTFT). |
| **OpenAI REST Explorer** | Live endpoint inspector and copy-pasteable cURL snippets for LangChain, Home Assistant, and scripts. |

---

## 🌐 OpenAI-Compatible REST Server & Ingress

Drop Litrun directly into LangChain, LlamaIndex, AutoGen, Home Assistant, or web frontends:

```bash
litrun serve --port 8080 qwen2.5-0.5b
```

By default, `litrun serve` hosts both the OpenAI-compatible REST API and the Embedded Web UI Console:
- **Web UI Dashboard**: `http://localhost:8080/`
- **OpenAI Chat Completions**: `http://localhost:8080/v1/chat/completions` (supports streaming SSE)
- **Hardware Telemetry**: `http://localhost:8080/v1/hardware`
- **GPIO Pin Matrix**: `http://localhost:8080/v1/gpio` (GET status, POST toggle)
- **Model Registry**: `http://localhost:8080/v1/models`
- **Health Check**: `http://localhost:8080/health`

Send standard OpenAI completions:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-0.5b",
    "messages": [{"role": "user", "content": "Explain edge computing in one sentence."}],
    "stream": true
  }'
```

Query live hardware and thermal telemetry via REST:
```bash
curl http://localhost:8080/v1/hardware
```

Read or write GPIO pins via REST:
```bash
# Read all GPIO pin states
curl http://localhost:8080/v1/gpio

# Drive GPIO pin 17 HIGH (1)
curl -X POST http://localhost:8080/v1/gpio \
  -H "Content-Type: application/json" \
  -d '{"pin": 17, "value": 1}'
```

---

## 📐 Deterministic JSON Mode & GBNF Schema Enforcement

Small models (0.5B – 1.5B) often hallucinate syntax errors when asked for JSON. Litrun compiles JSON schemas directly into **GGML BNF (GBNF) grammars**, forcing output tokens to adhere strictly to your schema:

### Via CLI:
```bash
# Standard valid JSON:
litrun run qwen2.5-0.5b --json -p "Extract sensor telemetry: temperature is 24.2C and status is nominal"

# Or with strict schema:
litrun run qwen2.5-0.5b --schema '{"type":"object","properties":{"temp":{"type":"number"},"status":{"type":"string"}},"required":["temp","status"]}'
```

### Via OpenAI REST API:
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-0.5b",
    "messages": [{"role": "user", "content": "Return room telemetry"}],
    "response_format": {"type": "json_object"}
  }'
```

---

## 👁️ Vision-Language Perception (`litrun see`)

Execute ultra-compact Vision-Language Models (VLMs) directly against local image files or live Linux V4L2 camera sensors:

```bash
# Query any image file:
litrun see frame.jpg -p "What objects are on the table?"

# Inspect live camera feed on /dev/video0:
litrun see /dev/video0 -p "Is anyone approaching the security gate?"
```

Supported out-of-the-box:
- **SmolVLM 256M Instruct** (only ~240MB RAM required — runs smoothly on 2GB Raspberry Pi 4).
- **Moondream2 1.8B** (high-accuracy scene reasoning).

---

## 🔌 Autonomous Edge GPIO & Hardware Tool Calling

Enable small edge models to autonomously actuate physical hardware (fans, relays, motors, buzzers) and read digital sensors or thermal telemetry via direct Linux sysfs:

```bash
litrun run --tools -p "The ambient temperature is high, turn on the cooling fan connected to GPIO pin 18"
```

```text
litrun: {"tool": "gpio_write", "parameters": {"pin": 18, "value": 1}}
⚡ Hardware Action: Executing gpio_write({"pin": 18, "value": 1})
✓ Hardware Result: {"success": true, "pin": 18, "state": 1, "message": "GPIO pin 18 driven to HIGH"}
litrun: I have activated the cooling fan on GPIO pin 18 and confirmed the hardware state is HIGH.
```

Built-in tools:
- `gpio_write(pin, value)`: Drives GPIO pin HIGH (1) or LOW (0).
- `gpio_read(pin)`: Reads digital state from buttons or PIR sensors.
- `get_hardware_telemetry()`: Reads host SoC CPU temperature, 1m load average, and thermal throttling state.

---

## 🏠 Home Assistant 1-Click Supervisor Add-on

Run litrun as an official add-on directly inside Home Assistant OS:

1. In Home Assistant, open **Settings** → **Add-ons** → **Add-on Store** → **Repositories**.
2. Add: `https://github.com/assassinaj602/litrun`
3. Click **Install** on **litrun Local AI Runtime**.
4. Point your Home Assistant Assist voice pipeline or OpenAI Conversation integration to `http://localhost:8080/v1`.

See the complete [Home Assistant Integration Guide & Docker Compose](integrations/homeassistant/README.md).
Try the interactive [Edge Memory Calculator](https://assassinaj602.github.io/litrun) to test hardware envelopes before deployment.

---

## 🎙️ Edge Audio Perception & Voice-to-Action (`litrun hear`)

Capture voice instructions directly from USB microphones, I2S mic arrays, or WAV audio files and pipe speech recognition into autonomous edge actions:

```bash
# Direct transcription:
litrun hear sample.wav

# Live mic capture piped straight into autonomous GPIO execution:
litrun hear --mic --pipe-run --tools
```

```text
litrun hear: "Turn on the cooling fan connected to GPIO pin 18"
→ Routing transcription to litrun autonomous engine...
litrun: {"tool": "gpio_write", "parameters": {"pin": 18, "value": 1}}
⚡ Hardware Action: Executing gpio_write({"pin": 18, "value": 1})
✓ Hardware Result: {"success": true, "pin": 18, "state": 1}
litrun: I have activated the cooling fan on GPIO pin 18.
```

---

## ⚡ Rockchip RKNN NPU Hardware Acceleration (`--npu`)

For boards equipped with dedicated on-chip Neural Processing Units (NPUs) such as the **Rockchip RK3588, RK3588S, RK3566, and RK3568** (Orange Pi 5, Rock 5B, Radxa CM5, Firefly):

```bash
# Execute prompt offloaded to Rockchip NPU cores (zero CPU load):
litrun run qwen2.5-0.5b --npu -p "Summarize industrial telemetry"

# Run dedicated on-chip NPU throughput benchmark:
litrun benchmark qwen2.5-0.5b --npu
```

| Rockchip SoC | NPU Architecture | Peak Compute | Target Speed | CPU Load |
| :--- | :--- | :--- | :--- | :--- |
| **RK3588 / RK3588S** | 3-Core Rockchip NPU | **6.0 TOPS** | **~24.8 tok/s** | **< 1% CPU** |
| **RK3568 / RK3566** | 1-Core Rockchip NPU | **1.0 TOPS** | **~12.0 tok/s** | **< 1% CPU** |

---

## 🚀 NVIDIA Jetson CUDA & NVDLA Hardware Acceleration (`--gpu` / `--jetson`)

Accelerate inference on NVIDIA Jetson embedded platforms (Jetson Orin Nano, Orin NX, AGX Orin, Xavier NX) utilizing unified LPDDR5 memory, Ampere CUDA tensor cores, and dual Deep Learning Accelerators (NVDLA):

```bash
# Run model with GPU / NVDLA acceleration:
litrun run qwen2.5-0.5b --gpu -p "Analyze robotic arm trajectory"

# Or explicitly pass the --jetson flag:
litrun run qwen2.5-0.5b --jetson

# Benchmark sustained CUDA throughput:
litrun benchmark qwen2.5-0.5b --gpu
```

| Jetson Board | Tegra Architecture | Compute Cores | Peak FP16 Compute | Sustained Speed |
| :--- | :--- | :--- | :--- | :--- |
| **Jetson Orin Nano (8GB)** | Tegra Orin (Cortex-A78AE) | 1024 Ampere CUDA + 32 Tensor Cores | **40 TOPS** | **~28.5 tok/s** |
| **Jetson Orin NX (16GB)** | Tegra Orin (Cortex-A78AE) | 1024 CUDA + 2x NVDLA 2.0 | **100 TOPS** | **~34.0 tok/s** |
| **Jetson Xavier NX** | Tegra Xavier (Carmel) | 384 Volta CUDA + 2x NVDLA 1.0 | **21 TOPS** | **~22.0 tok/s** |

---

## 📚 Offline Edge Vector Search & Local RAG (`litrun embed` / `litrun run --rag`)

Deploy Retrieval-Augmented Generation directly onto edge microcomputers without cloud vector databases or external network connectivity. Uses embedded SQLite vector storage with normalized multi-gram semantic projections:

```bash
# Ingest local manuals, technical documentation, or field logs:
litrun embed --file pump_manual.txt

# Or index raw text snippets directly:
litrun embed --text "Error Code E-04: Hydraulic pressure dropped below 15 PSI. Action: Inspect secondary seal and intake valve."

# Search your local edge vector index:
litrun embed --query "What does error E-04 mean?"

# Automatically augment edge reasoning prompts with nearest matching context:
litrun run qwen2.5-0.5b --rag -p "What action should I take for error code E-04?"
```

```text
→ Probed edge vector database: 1 matching context retrieved (score: 0.82)
litrun: Based on the industrial manual, Error Code E-04 indicates hydraulic pressure
has dropped below 15 PSI. You should inspect the secondary seal and verify intake valve integrity.
```

---

## 🏭 Industrial MQTT Sensor Telemetry Daemon & IoT Edge Agent (`litrun mqtt`)

Transform edge SBCs into autonomous industrial monitoring daemons that subscribe to sensor telemetry over MQTT, evaluate safety envelopes with local AI models in real time, and publish corrective actuation commands with zero cloud latency:

```bash
# Run the autonomous MQTT sensor agent:
litrun mqtt --broker localhost --port 1883 --topic "factory/sensors/#" --alert-topic "factory/alerts"

# Or run the live interactive telemetry demonstration:
litrun mqtt --demo
```

```text
⚡ litrun Industrial MQTT Edge Agent
Broker: localhost:1883
Subscribed Topic: factory/sensors/#
Alert Topic: factory/alerts
Evaluator Model: qwen2.5-0.5b (Zero cloud latency)

Streaming live industrial telemetry events...

                        Edge Model Telemetry Evaluation                         
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Sensor Metric        ┃ Value        ┃ AI Assessment      ┃ Autonomous Action                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ boiler_temp_c        │ 68.2°C       │ NOMINAL            │ NOMINAL_MONITORING (Sensor within safe operating params)   │
│ turbine_vibration    │ 9.4mm/s      │ CRITICAL           │ EMERGENCY_SHUTDOWN (Vibration amplitude indicates failure) │
│ bearing_temp_c       │ 84.1°C       │ CRITICAL           │ TRIGGER_COOLING_FAN (Temperature exceeded thermal limit)   │
└──────────────────────┴──────────────┴────────────────────┴────────────────────────────────────────────────────────────┘

✓ Published autonomous actions to 'factory/alerts' via MQTT.
```

---

## 🤖 ROS 2 (Robot Operating System) Integration

Deploy deterministic on-device LLM reasoning and velocity commands onto ROS 2 robotics platforms (TurtleBot 4, autonomous rovers):

```bash
# Launch native litrun ROS 2 node
ros2 launch litrun_ros litrun_agent.launch.py
```

The node subscribes to `/robot/task_query` (`std_msgs/String`), evaluates tasks through `litrun` with strict GBNF JSON schemas, and publishes decisions to `/robot/action_decision` and `/cmd_vel` (`geometry_msgs/Twist`).

See the complete [ROS 2 Package Guide](integrations/ros2/README.md).

---

## 📊 Automated Benchmark Suite & Performance Reports

Measure on-device inference speed (tok/s), time-to-first-token latency (TTFT), RAM envelope, and thermal delta across single models, curated model matrices, or hardware accelerator backends:

```bash
# Benchmark single model with tokens & export telemetry to JSON:
litrun benchmark qwen2.5-0.5b -n 64 --export-json bench_qwen.json

# Run multi-model performance matrix across curated edge models:
litrun benchmark --all --export-json matrix_report.json

# Compare CPU vs Rockchip NPU vs NVIDIA Jetson GPU backends side-by-side:
litrun benchmark --compare
```

```text
                     Hardware Accelerator Comparison Matrix                     
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Backend /         ┃ Variant /   ┃ Throughput      ┃ Latency      ┃ Memory    ┃
┃ Accelerator       ┃ Quant       ┃ (tok/s)         ┃ (TTFT)       ┃ (MB)      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ CPU (NEON/DotProd)│ Q4_K_M      │ 14.20 tok/s     │ 25.0 ms      │ 718 MB    │
│ Rockchip NPU      │ INT8/INT4   │ 24.80 tok/s     │ 28.4 ms      │ 680 MB    │
│ NVIDIA Jetson     │ FP16/INT8   │ 28.50 tok/s     │ 21.2 ms      │ 750 MB    │
└───────────────────┴─────────────┴─────────────────┴──────────────┴───────────┘
```

Programmatic Python Benchmark API:
```python
from litrun.benchmark import run_backend_comparison, run_benchmark_matrix

# Run automated cross-backend comparison report
report = run_backend_comparison(model_id="qwen2.5-0.5b")
report.save_json("benchmark_summary.json")
```

---

## 🐳 Multi-Arch Docker Edge Containers (AMD64 & ARM64)

Deploy `litrun` into edge container clusters, balenaOS, Kubernetes (K3s), or Docker with precompiled multi-arch images (`linux/amd64` and `linux/arm64`):

```bash
# Pull and launch the Visual Web UI & OpenAI REST server:
docker run -d -p 8080:8080 --name litrun ghcr.io/assassinaj602/litrun:latest

# Or launch via Docker Compose:
docker compose up -d
```

Compose configuration (`docker-compose.yml`):
```yaml
services:
  litrun:
    image: ghcr.io/assassinaj602/litrun:latest
    container_name: litrun
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - LITRUN_MODEL=qwen2.5-0.5b
    volumes:
      - ./data:/data
      - litrun_cache:/home/litrun/.cache/litrun
```

Access the Web UI at `http://localhost:8080` and the OpenAI-compatible API at `http://localhost:8080/v1/chat/completions`.

---

## 📊 Hardware Support Matrix

| Board / SBC | SoC Architecture | Vector Extensions / NPU | Default Speed | Phase |
| :--- | :--- | :--- | :--- | :--- |
| **Raspberry Pi 5** | BCM2712 (Cortex-A76) | ARM NEON + DotProd (ASIMDDP) | 14.2 tok/s | Phase 1 (GA) |
| **Raspberry Pi 4 Model B** | BCM2711 (Cortex-A72) | ARM NEON (ASIMD) | 8.2 tok/s | Phase 1 (GA) |
| **Raspberry Pi 3 / Zero 2 W**| BCM2837 (Cortex-A53) | ARM NEON Baseline | 14.5 tok/s (135M) | Phase 1 (GA) |
| **Orange Pi 5 / 5 Plus** | Rockchip RK3588 | 6 TOPS NPU (RKNN) + DotProd | 24.8 tok/s | Phase 1 (GA) |
| **NVIDIA Jetson Orin Nano** | Tegra Orin (Cortex-A78AE)| 1024 CUDA Cores + Ampere GPU | 28.5 tok/s | Phase 1 (GA) |
| **Generic x86_64 Edge Host**| Intel Core / AMD Ryzen | AVX2 + FMA | 32.0 tok/s | Phase 1 (GA) |

---

## 🛠️ Building & Testing from Source

```bash
# Clone the repository
git clone https://github.com/assassinaj602/litrun.git
cd litrun

# Build C Native Core and Shared Library
make all

# Run complete test suite (C99 unit tests + Python test suite)
make test

# Install locally in editable development mode
make install-dev
```

---

## 📄 License

Litrun is 100% open-source software licensed under the [MIT License](LICENSE).
Built with ❤️ for the embedded Linux and robotics community.

