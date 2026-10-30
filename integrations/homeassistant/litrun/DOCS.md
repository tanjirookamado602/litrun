# litrun Local AI Runtime — Home Assistant Add-on

Run ultra-lightweight, hardware-accelerated local LLMs (Qwen 2.5, SmolLM2, Llama 3.2) and vision models (SmolVLM, Moondream2) directly on your Home Assistant server or Raspberry Pi 4/5 with active RAM and thermal protection.

---

## Features

- **Zero-Guesswork Auto-Quantization:** Automatically chooses the optimal GGUF quantization (e.g. Q4_K_M vs Q8_0) based on your hardware's real-time free RAM.
- **Kernel OOM Protection:** Dedicated C99 governor guarantees Home Assistant OS will never trigger an Out-Of-Memory kernel panic.
- **OpenAI Compatible:** Works out-of-the-box with **Home Assistant Assist**, **Extended OpenAI Conversation**, and **Local AI** integrations.
- **100% Offline & Private:** Zero cloud dependencies, zero telemetry tracking, 100% local edge inference.

---

## Installation

1. In Home Assistant, navigate to **Settings** → **Add-ons** → **Add-on Store**.
2. Click the three dots in the top-right corner and select **Repositories**.
3. Add this repository URL:
   ```text
   https://github.com/assassinaj602/litrun
   ```
4. Find **litrun Local AI Runtime** in the Add-on Store list and click **Install**.
5. Once installed, configure your preferred model (default: `qwen2.5-0.5b`) under the **Configuration** tab.
6. Click **Start** and toggle **Start on boot**.

---

## Configuration

| Option | Type | Default | Description |
|---|---|---|---|
| `model` | string | `qwen2.5-0.5b` | Model identifier (`qwen2.5-0.5b`, `smollm2-135m`, `llama-3.2-1b`, `smolvlm-256m`) |
| `quant` | string | `Q4_K_M` | Preferred quantization (`Q4_K_M`, `Q5_K_M`, `Q8_0`). Leave empty for automatic selection. |
| `threads` | int | `4` | Number of CPU inference threads. |
| `port` | int | `8080` | Port for the OpenAI-compatible REST API. |

---

## Integrating with Home Assistant Assist

### Step 1: Add OpenAI Conversation Integration
1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **OpenAI Conversation**.
3. Enter any string for the API Key (e.g. `litrun-local`).
4. Enter the base URL:
   ```text
   http://localhost:8080/v1
   ```
   *(or `http://homeassistant.local:8080/v1` if configured from another host)*

### Step 2: Set as Default Voice Assist Engine
1. Go to **Settings** → **Voice Assistants** → **Home Assistant Cloud** or your custom assist pipeline.
2. Under **Conversation Agent**, select **OpenAI Conversation (litrun)**.
3. Test by speaking or typing: *"Turn on the kitchen lights"* or *"What is the state of the living room temperature sensor?"*.

---

## Hardware Sizing & Recommended Models

| Hardware | Recommended Model | RAM Usage | Speed |
|---|---|---|---|
| **Raspberry Pi 4 (2GB)** | `smollm2-135m` (Q8_0) | ~220 MB | ~28 tok/s |
| **Raspberry Pi 4 (4GB)** | `qwen2.5-0.5b` (Q4_K_M) | ~490 MB | ~14 tok/s |
| **Raspberry Pi 5 (4GB/8GB)** | `llama-3.2-1b` (Q4_K_M) | ~890 MB | ~18 tok/s |
| **Home Assistant Yellow / CM4** | `qwen2.5-0.5b` (Q4_K_M) | ~490 MB | ~12 tok/s |
| **Intel N100 / x86 Mini PC** | `qwen2.5-1.5b` (Q4_K_M) | ~1.2 GB | ~35 tok/s |
