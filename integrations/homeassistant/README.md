# 🏠 litrun + Home Assistant Integration Guide

Deploy fully offline, local AI on your **Raspberry Pi 4, Pi 5, or Home Assistant Yellow / Green** with zero cloud latency and no monthly subscriptions.

---

## 🌟 Why Use litrun for Home Assistant?

| Typical Desktop Daemon (e.g. Ollama) | litrun Edge Runtime |
| :--- | :--- |
| **Consumes 150MB–250MB RAM** before loading models. | **<200KB C99 core** with near-zero background idle memory. |
| **No RAM envelope protection**: large prompts crash Home Assistant via kernel OOM panics. | **Active C Governor**: computes safe limits against Linux cgroups to guarantee stability. |
| **High TTFT** when re-invoked. | **Sub-50ms TTFT** via persistent model weights locked in RAM. |
| **Unconstrained outputs**: hallucinates invalid YAML/JSON for entity actions. | **Native GBNF Grammars**: enforces strict JSON Schema matching your entities. |

---

## 🚀 Quick Setup

### Method 1: 1-Click Home Assistant Add-on (Recommended)

1. Open Home Assistant → **Settings** → **Add-ons** → **Add-on Store**.
2. Click the three dots (top right) → **Repositories** → Add:
   ```text
   https://github.com/assassinaj602/litrun
   ```
3. Click on **litrun Local AI Runtime** and select **Install**.
4. Start the add-on. The local OpenAI API will now be live on `http://homeassistant.local:8080/v1`.

### Method 2: Docker Compose (Standalone SBC / Server)

Copy `docker-compose.yml` to your Home Assistant server or separate SBC:

```bash
docker compose up -d
```

Verify service health:
```bash
curl http://localhost:8080/health
# Returns: {"status": "healthy", "service": "litrun OpenAI-Compatible REST Server"}
```

---

## ⚙️ Home Assistant Configuration

### Method A: Native OpenAI Conversation Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **OpenAI Conversation**.
3. Configure the integration settings:
   - **API Key**: `litrun` (any placeholder string)
   - **Base URL**: `http://localhost:8080/v1` (or your Pi IP `http://192.168.1.X:8080/v1`)
   - **Model**: `qwen2.5-0.5b` (or `smollm2-135m`, `llama-3.2-1b`)
4. Click **Submit**.

You now have a local voice and automation agent capable of understanding conversational sensor queries!

---

### Method B: Deterministic Edge Actions via JSON Schema

For mission-critical automations (turning off heaters, triggering relays), run [`smart_home_controller.py`](smart_home_controller.py).

`litrun` uses GBNF grammar constraints to guarantee that the LLM only generates valid Home Assistant service payloads:

```json
{
  "domain": "climate",
  "service": "set_temperature",
  "entity_id": "climate.living_room",
  "reason": "Temperature reached 28.5C while room is occupied"
}
```

---

## 📊 Recommended Models by Hardware

| Single-Board Computer | RAM | Recommended Model | Tokens / Sec |
| :--- | :--- | :--- | :--- |
| **Raspberry Pi 4 Model B** | 2GB / 4GB | `smollm2-135m-Q8_0` | ~14.5 tok/s |
| **Raspberry Pi 4 Model B** | 4GB / 8GB | `qwen2.5-0.5b-Q4_K_M` | ~8.5 tok/s |
| **Raspberry Pi 5** | 4GB / 8GB | `qwen2.5-0.5b-Q8_0` | ~14.2 tok/s |
| **Raspberry Pi 5** | 8GB | `llama-3.2-1b-Q4_K_M` | ~11.0 tok/s |
| **Orange Pi 5 (RK3588)** | 8GB / 16GB | `qwen2.5-1.5b-Q4_K_M` | ~18.5 tok/s |

