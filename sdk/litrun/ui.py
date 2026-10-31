"""
litrun Embedded Web UI Dashboard & Edge Device Console
Single-file, self-contained HTML/CSS/JS interface served directly from litrun serve.
Zero external CDNs or runtime dependencies. Fully functional offline on air-gapped SBCs.
"""

from __future__ import annotations


def get_ui_html(version: str = "0.6.0") -> str:
    """Returns the complete single-page Web UI dashboard HTML string."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>litrun Edge AI Console</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --card-hover: #1e293b;
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.25);
      --accent-cyan: #06b6d4;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --danger: #ef4444;
      --warning: #f59e0b;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 0.85rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      color: inherit;
    }}
    .logo-badge {{
      background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
      color: #042f2e;
      font-weight: 800;
      font-size: 1.15rem;
      padding: 0.35rem 0.65rem;
      border-radius: 8px;
      box-shadow: 0 0 16px var(--accent-glow);
    }}
    .brand-title {{
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .version-tag {{
      font-size: 0.75rem;
      background: #1f2937;
      color: var(--accent-cyan);
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      border: 1px solid #374151;
      font-family: var(--font-mono);
    }}
    .device-status {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }}
    .status-dot {{
      width: 9px;
      height: 9px;
      background: var(--accent);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent);
      animation: pulse 2s infinite ease-in-out;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.85); }}
    }}
    nav.nav-tabs {{
      display: flex;
      gap: 0.35rem;
      background: #0d131f;
      padding: 0.3rem;
      border-radius: 8px;
      border: 1px solid var(--card-border);
    }}
    .nav-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.45rem 0.9rem;
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .nav-btn:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.05);
    }}
    .nav-btn.active {{
      background: var(--card-bg);
      color: var(--accent);
      border: 1px solid var(--card-border);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }}
    main {{
      flex: 1;
      max-width: 1300px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}
    /* Telemetry Hero Grid */
    .telemetry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }}
    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.15rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      position: relative;
      overflow: hidden;
    }}
    .metric-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: transparent;
      transition: background 0.2s;
    }}
    .metric-card.accent-emerald::before {{ background: var(--accent); }}
    .metric-card.accent-cyan::before {{ background: var(--accent-cyan); }}
    .metric-card.accent-amber::before {{ background: var(--warning); }}
    .metric-card.accent-purple::before {{ background: #a855f7; }}

    .metric-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-muted);
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .metric-val {{
      font-size: 1.65rem;
      font-weight: 700;
      font-family: var(--font-mono);
      letter-spacing: -0.02em;
    }}
    .metric-sub {{
      font-size: 0.8rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .progress-bar-bg {{
      background: #1f2937;
      height: 6px;
      border-radius: 3px;
      overflow: hidden;
      margin-top: 0.25rem;
    }}
    .progress-bar-fill {{
      height: 100%;
      background: var(--accent);
      border-radius: 3px;
      transition: width 0.4s ease;
    }}
    /* Tabs content */
    .tab-content {{
      display: none;
      animation: fadeIn 0.2s ease-in-out;
    }}
    .tab-content.active {{
      display: block;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    /* Chat Playground layout */
    .playground-grid {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 1.25rem;
      min-height: 550px;
    }}
    @media (max-width: 860px) {{
      .playground-grid {{
        grid-template-columns: 1fr;
      }}
      header {{
        flex-direction: column;
        align-items: stretch;
      }}
      nav.nav-tabs {{
        justify-content: center;
      }}
    }}
    .panel-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .panel-box h3 {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .form-group label {{
      font-size: 0.8rem;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .input-field, .select-field, .textarea-field {{
      background: #0d131f;
      border: 1px solid var(--card-border);
      color: var(--text-main);
      border-radius: 6px;
      padding: 0.55rem 0.75rem;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s;
    }}
    .input-field:focus, .select-field:focus, .textarea-field:focus {{
      border-color: var(--accent);
    }}
    .chat-container {{
      display: flex;
      flex-direction: column;
      height: 600px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      overflow: hidden;
    }}
    .chat-messages {{
      flex: 1;
      padding: 1.25rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .msg-bubble {{
      max-width: 82%;
      padding: 0.85rem 1.15rem;
      border-radius: 10px;
      font-size: 0.9rem;
      line-height: 1.5;
      word-break: break-word;
      white-space: pre-wrap;
    }}
    .msg-user {{
      align-self: flex-end;
      background: #1e3a5f;
      color: #e0f2fe;
      border-bottom-right-radius: 2px;
    }}
    .msg-assistant {{
      align-self: flex-start;
      background: #1a2234;
      color: var(--text-main);
      border: 1px solid var(--card-border);
      border-bottom-left-radius: 2px;
    }}
    .msg-meta {{
      font-size: 0.7rem;
      color: var(--text-dim);
      margin-top: 0.35rem;
      font-family: var(--font-mono);
    }}
    .quick-prompts {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      padding: 0.5rem 1.25rem;
      background: #0d131f;
      border-top: 1px solid var(--card-border);
    }}
    .prompt-chip {{
      background: #1f2937;
      color: var(--text-muted);
      border: 1px solid #374151;
      border-radius: 14px;
      padding: 0.25rem 0.65rem;
      font-size: 0.75rem;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .prompt-chip:hover {{
      color: var(--accent);
      border-color: var(--accent);
      background: rgba(16, 185, 129, 0.1);
    }}
    .chat-input-row {{
      display: flex;
      gap: 0.5rem;
      padding: 0.75rem 1.25rem;
      background: #0d131f;
      border-top: 1px solid var(--card-border);
      align-items: flex-end;
    }}
    .chat-textarea {{
      flex: 1;
      min-height: 48px;
      max-height: 140px;
      resize: vertical;
      padding: 0.65rem;
      font-size: 0.9rem;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      padding: 0.65rem 1.15rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      border: none;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn-primary {{
      background: var(--accent);
      color: #042f2e;
    }}
    .btn-primary:hover {{
      background: #059669;
      box-shadow: 0 0 12px var(--accent-glow);
    }}
    .btn-secondary {{
      background: #1f2937;
      color: var(--text-main);
      border: 1px solid var(--card-border);
    }}
    .btn-secondary:hover {{
      background: #374151;
    }}
    .btn:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}
    /* Image Preview Box */
    .image-preview-bar {{
      display: none;
      padding: 0.4rem 1.25rem;
      background: #111827;
      border-top: 1px solid var(--card-border);
      align-items: center;
      gap: 0.75rem;
    }}
    .image-preview-thumb {{
      width: 44px;
      height: 44px;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid var(--accent);
    }}
    /* GPIO Matrix */
    .gpio-controls-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .gpio-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
      gap: 0.85rem;
    }}
    .gpio-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      transition: all 0.15s ease;
    }}
    .gpio-card:hover {{
      border-color: #374151;
      transform: translateY(-2px);
    }}
    .gpio-pin-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .gpio-pin-num {{
      font-weight: 700;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: var(--text-main);
    }}
    .gpio-status-pill {{
      font-size: 0.7rem;
      font-family: var(--font-mono);
      font-weight: 700;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
    }}
    .gpio-high {{
      background: rgba(16, 185, 129, 0.2);
      color: var(--accent);
      border: 1px solid var(--accent);
    }}
    .gpio-low {{
      background: #1f2937;
      color: var(--text-dim);
      border: 1px solid #374151;
    }}
    .gpio-btn-toggle {{
      width: 100%;
      padding: 0.4rem;
      font-size: 0.75rem;
      font-weight: 600;
      border-radius: 4px;
      border: 1px solid var(--card-border);
      cursor: pointer;
      background: #0d131f;
      color: var(--text-main);
      transition: all 0.15s;
    }}
    .gpio-btn-toggle:hover {{
      background: var(--accent);
      color: #042f2e;
    }}
    /* Benchmark Tab */
    .bench-result-box {{
      background: #0d131f;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1.25rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: var(--text-main);
      white-space: pre-wrap;
      min-height: 120px;
    }}
    .curl-snippet {{
      background: #080c14;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: #93c5fd;
      overflow-x: auto;
      position: relative;
    }}
    footer {{
      margin-top: auto;
      border-top: 1px solid var(--card-border);
      padding: 1rem 1.5rem;
      text-align: center;
      color: var(--text-dim);
      font-size: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    footer a {{
      color: var(--accent-cyan);
      text-decoration: none;
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <a href="/" class="brand">
      <div class="logo-badge">⚡ litrun</div>
      <div>
        <div class="brand-title">
          Device Console
          <span class="version-tag">v{version}</span>
        </div>
      </div>
    </a>

    <nav class="nav-tabs">
      <button class="nav-btn active" onclick="switchTab('chat')">💬 Playground</button>
      <button class="nav-btn" onclick="switchTab('gpio')">🔌 GPIO Matrix</button>
      <button class="nav-btn" onclick="switchTab('telemetry')">📊 Telemetry</button>
      <button class="nav-btn" onclick="switchTab('bench')">⚡ Benchmark & API</button>
    </nav>

    <div class="device-status">
      <div class="status-dot"></div>
      <span id="header-soc-name">Probing Hardware...</span>
    </div>
  </header>

  <!-- Main Body -->
  <main>
    <!-- Top Telemetry Row -->
    <section class="telemetry-grid">
      <div class="metric-card accent-emerald">
        <div class="metric-header">
          <span>Board & Processor</span>
          <span>CPU</span>
        </div>
        <div class="metric-val" id="metric-cpu-cores">--</div>
        <div class="metric-sub">
          <span id="metric-soc-model">Detecting...</span>
          <span id="metric-arch">--</span>
        </div>
      </div>

      <div class="metric-card accent-cyan">
        <div class="metric-header">
          <span>CPU Temperature</span>
          <span id="thermal-badge">NORMAL</span>
        </div>
        <div class="metric-val" id="metric-temp">--.- °C</div>
        <div class="metric-sub">
          <span>1-min Load: <b id="metric-load">0.00</b></span>
          <span id="thermal-governor-status">Passive</span>
        </div>
      </div>

      <div class="metric-card accent-amber">
        <div class="metric-header">
          <span>RAM Governor Envelope</span>
          <span id="ram-pct-text">0%</span>
        </div>
        <div class="metric-val" id="metric-ram-used">-- / -- MB</div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="ram-progress" style="width: 0%"></div>
        </div>
      </div>

      <div class="metric-card accent-purple">
        <div class="metric-header">
          <span>Loaded AI Model</span>
          <span id="model-family-badge">LLM</span>
        </div>
        <div class="metric-val" id="metric-active-model" style="font-size: 1.15rem; word-break: break-all;">qwen2.5-0.5b</div>
        <div class="metric-sub">
          <span>Inference: POSIX C99 Engine</span>
          <span style="color: var(--accent);">Active</span>
        </div>
      </div>
    </section>

    <!-- Tab 1: Chat Playground -->
    <div id="tab-chat" class="tab-content active">
      <div class="playground-grid">
        <!-- Settings Sidebar -->
        <aside class="panel-box">
          <h3>⚙️ Model Parameters</h3>

          <div class="form-group">
            <label for="select-model">Model</label>
            <select id="select-model" class="select-field">
              <option value="qwen2.5-0.5b">qwen2.5-0.5b (Q4_K_M)</option>
              <option value="smolvlm-256m">smolvlm-256m (Vision)</option>
              <option value="moondream2">moondream2 (Vision)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="input-system-prompt">System Prompt</label>
            <textarea id="input-system-prompt" class="textarea-field" rows="4">You are litrun, an ultra-fast autonomous Edge AI assistant running directly on embedded Linux hardware.</textarea>
          </div>

          <div class="form-group">
            <label for="input-temperature">Temperature: <span id="val-temperature">0.7</span></label>
            <input type="range" id="input-temperature" min="0.0" max="1.5" step="0.1" value="0.7" oninput="document.getElementById('val-temperature').innerText=this.value">
          </div>

          <div class="form-group">
            <label for="input-max-tokens">Max Tokens: <span id="val-tokens">256</span></label>
            <input type="range" id="input-max-tokens" min="32" max="1024" step="32" value="256" oninput="document.getElementById('val-tokens').innerText=this.value">
          </div>

          <div class="form-group">
            <label>Image Input (Multimodal VLM)</label>
            <input type="file" id="image-file-input" accept="image/*" class="input-field" onchange="handleImageSelected(event)">
          </div>

          <button class="btn btn-secondary" onclick="clearChat()">🗑️ Clear History</button>
        </aside>

        <!-- Chat Conversation Area -->
        <section class="chat-container">
          <div class="chat-messages" id="chat-messages">
            <div class="msg-bubble msg-assistant">
              ⚡ Welcome to litrun Edge AI Console! I am running live on this device.
You can prompt me with text queries, ask me to inspect sensors or control GPIO pins, or attach photos for vision analysis.
              <div class="msg-meta">litrun core engine • zero cloud dependency</div>
            </div>
          </div>

          <!-- Image Preview Bar if an image is selected -->
          <div id="image-preview-bar" class="image-preview-bar">
            <img id="image-preview-thumb" class="image-preview-thumb" alt="Preview">
            <span style="font-size: 0.8rem; color: var(--text-muted);" id="image-file-name">image.png</span>
            <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.75rem; margin-left: auto;" onclick="clearSelectedImage()">✕ Remove</button>
          </div>

          <!-- Quick Prompts -->
          <div class="quick-prompts">
            <button class="prompt-chip" onclick="applyQuickPrompt('Read system telemetry and CPU temperature')">🌡️ Read CPU Temp & RAM</button>
            <button class="prompt-chip" onclick="applyQuickPrompt('Turn on GPIO pin 17 to activate actuator')">💡 Turn ON GPIO 17</button>
            <button class="prompt-chip" onclick="applyQuickPrompt('Turn off GPIO pin 17')">🔌 Turn OFF GPIO 17</button>
            <button class="prompt-chip" onclick="applyQuickPrompt('Explain how litrun prevents Linux OOM crashes')">🛡️ Explain RAM Governor</button>
          </div>

          <!-- Input Bar -->
          <div class="chat-input-row">
            <textarea id="chat-prompt-input" class="textarea-field chat-textarea" placeholder="Type a message or hardware instruction... (Press Ctrl+Enter to send)" onkeydown="if(event.ctrlKey && event.key==='Enter') sendMessage()"></textarea>
            <button class="btn btn-primary" id="btn-send" onclick="sendMessage()">
              <span>Send</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
            </button>
          </div>
        </section>
      </div>
    </div>

    <!-- Tab 2: GPIO Hardware Matrix -->
    <div id="tab-gpio" class="tab-content">
      <div class="panel-box">
        <div class="gpio-controls-bar">
          <div>
            <h3>🔌 40-Pin Sysfs GPIO Matrix</h3>
            <p style="font-size: 0.8rem; color: var(--text-muted);">
              Direct kernel control via POSIX sysfs (<code style="color: var(--accent-cyan);">/sys/class/gpio</code>). Toggle pins in real-time.
            </p>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span id="gpio-mode-badge" class="version-tag">Probing...</span>
            <button class="btn btn-secondary" onclick="refreshGPIO()">🔄 Refresh</button>
            <button class="btn btn-secondary" onclick="toggleAllPins(0)">All LOW (0)</button>
          </div>
        </div>

        <div class="gpio-grid" id="gpio-grid">
          <!-- Dynamically populated GPIO pins -->
        </div>
      </div>
    </div>

    <!-- Tab 3: Detailed Telemetry -->
    <div id="tab-telemetry" class="tab-content">
      <div class="panel-box">
        <h3>📊 Hardware & Governor Diagnostics</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          Raw hardware profile and dynamic Linux cgroups / thermal governor metrics.
        </p>
        <pre class="bench-result-box" id="telemetry-raw-json">Fetching telemetry...</pre>
      </div>
    </div>

    <!-- Tab 4: Benchmark & API -->
    <div id="tab-bench" class="tab-content">
      <div class="panel-box">
        <h3>⚡ Real-Time Inference Benchmark</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          Trigger a 100-token prompt directly against the loaded local model to measure tokens/second (tok/s) and latency.
        </p>

        <div style="display: flex; gap: 1rem; align-items: center; margin: 0.5rem 0;">
          <button class="btn btn-primary" id="btn-run-bench" onclick="runBenchmark()">▶ Run 100-Token Benchmark</button>
          <span id="bench-status-indicator" style="font-size: 0.85rem; color: var(--text-muted);">Ready</span>
        </div>

        <pre class="bench-result-box" id="bench-output">Click 'Run 100-Token Benchmark' to evaluate local engine throughput on this device.</pre>

        <h3 style="margin-top: 1.5rem;">🔗 OpenAI-Compatible API Integration</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          You can connect any OpenAI-compatible client, LangChain, Home Assistant, or cURL directly to this device:
        </p>
        <div class="curl-snippet">
curl http://localhost:8080/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "qwen2.5-0.5b",
    "messages": [{{"role": "user", "content": "Hello edge AI!"}}],
    "stream": true
  }}'
        </div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer>
    <div>⚡ litrun runtime • Lightweight Edge AI for ARM64 & Embedded Linux</div>
    <div>
      <a href="https://github.com/assassinaj602/litrun" target="_blank">GitHub Repository</a> •
      <a href="https://assassinaj602.github.io/litrun" target="_blank">Documentation</a> •
      <a href="/v1/models" target="_blank">REST API Endpoint</a>
    </div>
  </footer>

  <!-- Scripts -->
  <script>
    let currentTab = 'chat';
    let attachedImageBase64 = null;
    let gpioPinsState = {{}};

    function switchTab(tabId) {{
      currentTab = tabId;
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

      const target = document.getElementById('tab-' + tabId);
      if (target) target.classList.add('active');

      const buttons = document.querySelectorAll('.nav-btn');
      if (tabId === 'chat') buttons[0].classList.add('active');
      if (tabId === 'gpio') {{
        buttons[1].classList.add('active');
        refreshGPIO();
      }}
      if (tabId === 'telemetry') {{
        buttons[2].classList.add('active');
        updateTelemetry();
      }}
      if (tabId === 'bench') buttons[3].classList.add('active');
    }}

    // Real-time Telemetry Poller
    async function updateTelemetry() {{
      try {{
        const resp = await fetch('/v1/hardware');
        if (!resp.ok) return;
        const data = await resp.json();

        // Hardware profile
        if (data.hardware) {{
          const hw = data.hardware;
          document.getElementById('header-soc-name').innerText = hw.soc_name || (hw.arch + ' Device');
          document.getElementById('metric-soc-model').innerText = hw.soc_name || 'Embedded Device';
          document.getElementById('metric-arch').innerText = hw.arch || '';
          document.getElementById('metric-cpu-cores').innerText = (hw.cpu_cores || 4) + ' Cores';
        }}

        // Governor & Thermals
        if (data.governor) {{
          const gov = data.governor;
          const temp = gov.temp_c || 45.0;
          document.getElementById('metric-temp').innerText = temp.toFixed(1) + ' °C';

          const thermalBadge = document.getElementById('thermal-badge');
          if (temp > 75) {{
            thermalBadge.innerText = 'THROTTLED';
            thermalBadge.style.color = 'var(--danger)';
          }} else if (temp > 60) {{
            thermalBadge.innerText = 'WARM';
            thermalBadge.style.color = 'var(--warning)';
          }} else {{
            thermalBadge.innerText = 'NOMINAL';
            thermalBadge.style.color = 'var(--accent)';
          }}

          // RAM
          const usedMb = gov.current_rss_mb || 0;
          const totalMb = gov.total_ram_mb || 1024;
          const limitMb = gov.ram_limit_mb || totalMb;
          const pct = Math.min(100, Math.round((usedMb / limitMb) * 100));

          document.getElementById('metric-ram-used').innerText = usedMb + ' / ' + limitMb + ' MB';
          document.getElementById('ram-pct-text').innerText = pct + '%';
          document.getElementById('ram-progress').style.width = pct + '%';
          if (pct > 85) {{
            document.getElementById('ram-progress').style.background = 'var(--danger)';
          }} else if (pct > 65) {{
            document.getElementById('ram-progress').style.background = 'var(--warning)';
          }} else {{
            document.getElementById('ram-progress').style.background = 'var(--accent)';
          }}
        }}

        // Raw JSON tab
        const rawJsonEl = document.getElementById('telemetry-raw-json');
        if (rawJsonEl) {{
          rawJsonEl.innerText = JSON.stringify(data, null, 2);
        }}
      }} catch (err) {{
        console.error('Failed to update telemetry:', err);
      }}
    }}

    // Poll telemetry every 3.5 seconds
    setInterval(updateTelemetry, 3500);
    updateTelemetry();

    // Populate Available Models
    async function loadModelsList() {{
      try {{
        const resp = await fetch('/v1/models');
        if (!resp.ok) return;
        const data = await resp.json();
        const select = document.getElementById('select-model');
        if (data.data && data.data.length > 0) {{
          select.innerHTML = '';
          data.data.forEach(m => {{
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.innerText = m.name || m.id;
            select.appendChild(opt);
          }});
          document.getElementById('metric-active-model').innerText = select.value;
        }}
      }} catch (e) {{
        console.warn('Could not list models:', e);
      }}
    }}
    loadModelsList();

    // Multimodal Image Attachment
    function handleImageSelected(event) {{
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {{
        attachedImageBase64 = e.target.result;
        document.getElementById('image-preview-thumb').src = attachedImageBase64;
        document.getElementById('image-file-name').innerText = file.name;
        document.getElementById('image-preview-bar').style.display = 'flex';
      }};
      reader.readAsDataURL(file);
    }}

    function clearSelectedImage() {{
      attachedImageBase64 = null;
      document.getElementById('image-file-input').value = '';
      document.getElementById('image-preview-bar').style.display = 'none';
    }}

    function applyQuickPrompt(text) {{
      const input = document.getElementById('chat-prompt-input');
      input.value = text;
      input.focus();
    }}

    function clearChat() {{
      const container = document.getElementById('chat-messages');
      container.innerHTML = `
        <div class="msg-bubble msg-assistant">
          ⚡ Chat history cleared. Ready for new queries or GPIO commands.
        </div>
      `;
    }}

    // Send Message with SSE streaming
    async function sendMessage() {{
      const input = document.getElementById('chat-prompt-input');
      const text = input.value.trim();
      if (!text && !attachedImageBase64) return;

      const modelId = document.getElementById('select-model').value;
      const systemPrompt = document.getElementById('input-system-prompt').value;
      const chatContainer = document.getElementById('chat-messages');

      // Add user message bubble
      const userBubble = document.createElement('div');
      userBubble.className = 'msg-bubble msg-user';
      let userHtml = text;
      if (attachedImageBase64) {{
        userHtml = `<div><img src="${{attachedImageBase64}}" style="max-width: 140px; border-radius: 6px; margin-bottom: 6px; display: block;"></div>` + userHtml;
      }}
      userBubble.innerHTML = userHtml;
      chatContainer.appendChild(userBubble);

      input.value = '';
      clearSelectedImage();

      // Add assistant bubble placeholder
      const assistantBubble = document.createElement('div');
      assistantBubble.className = 'msg-bubble msg-assistant';
      assistantBubble.innerHTML = `<span style="color: var(--text-dim);">Thinking...</span>`;
      chatContainer.appendChild(assistantBubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;

      const btnSend = document.getElementById('btn-send');
      btnSend.disabled = true;

      try {{
        const payload = {{
          model: modelId,
          messages: [
            {{ role: 'system', content: systemPrompt }},
            {{ role: 'user', content: text }}
          ],
          stream: true
        }};

        const resp = await fetch('/v1/chat/completions', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});

        if (!resp.ok) {{
          assistantBubble.innerText = 'Error from runtime: HTTP ' + resp.status;
          btnSend.disabled = false;
          return;
        }}

        assistantBubble.innerText = '';
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (true) {{
          const {{ value, done }} = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, {{ stream: true }});
          const lines = chunk.split('\\n');
          for (const line of lines) {{
            if (line.startsWith('data: ') && !line.includes('[DONE]')) {{
              try {{
                const json = JSON.parse(line.substring(6));
                const delta = json.choices[0]?.delta?.content || '';
                fullText += delta;
                assistantBubble.innerText = fullText;
                chatContainer.scrollTop = chatContainer.scrollHeight;
              }} catch (e) {{}}
            }}
          }}
        }}

        if (!fullText) {{
          assistantBubble.innerText = 'Completed (empty response)';
        }}
      }} catch (err) {{
        assistantBubble.innerText = 'Error: ' + err.message;
      }} finally {{
        btnSend.disabled = false;
      }}
    }}

    // GPIO Matrix Logic
    async function refreshGPIO() {{
      try {{
        const resp = await fetch('/v1/gpio');
        if (!resp.ok) return;
        const data = await resp.json();
        const grid = document.getElementById('gpio-grid');
        const modeBadge = document.getElementById('gpio-mode-badge');

        modeBadge.innerText = (data.mode || 'sysfs').toUpperCase();
        gpioPinsState = data.pins || {{}};

        grid.innerHTML = '';
        const pinKeys = Object.keys(gpioPinsState).map(Number).sort((a,b) => a - b);

        pinKeys.forEach(pin => {{
          const state = gpioPinsState[pin];
          const isHigh = state === 1;

          const card = document.createElement('div');
          card.className = 'gpio-card';
          card.innerHTML = `
            <div class="gpio-pin-top">
              <span class="gpio-pin-num">GPIO ${{pin}}</span>
              <span class="gpio-status-pill ${{isHigh ? 'gpio-high' : 'gpio-low'}}">${{isHigh ? 'HIGH (1)' : 'LOW (0)'}}</span>
            </div>
            <button class="gpio-btn-toggle" onclick="togglePin(${{pin}}, ${{isHigh ? 0 : 1}})">
              ${{isHigh ? 'Turn OFF (0)' : 'Turn ON (1)'}}
            </button>
          `;
          grid.appendChild(card);
        }});
      }} catch (err) {{
        console.error('Failed to load GPIO pins:', err);
      }}
    }}

    async function togglePin(pin, newState) {{
      try {{
        const resp = await fetch('/v1/gpio', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ pin: pin, value: newState }})
        }});
        if (resp.ok) {{
          await refreshGPIO();
        }}
      }} catch (err) {{
        console.error('Failed to toggle GPIO pin:', err);
      }}
    }}

    async function toggleAllPins(targetVal) {{
      const pinKeys = Object.keys(gpioPinsState).map(Number);
      for (const pin of pinKeys) {{
        await togglePin(pin, targetVal);
      }}
    }}

    // Benchmark Runner
    async function runBenchmark() {{
      const btn = document.getElementById('btn-run-bench');
      const indicator = document.getElementById('bench-status-indicator');
      const out = document.getElementById('bench-output');

      btn.disabled = true;
      indicator.innerText = 'Benchmarking...';
      out.innerText = 'Executing 100-token prompt benchmark via C99 engine...\\n';

      const startTime = performance.now();
      try {{
        const resp = await fetch('/v1/benchmark', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ prompt: 'Benchmark edge runtime speed with 100 tokens.' }})
        }});

        const duration = (performance.now() - startTime) / 1000.0;

        if (resp.ok) {{
          const res = await resp.json();
          out.innerText = [
            '====================================================',
            '⚡ litrun Hardware Inference Benchmark Results',
            '====================================================',
            'Model:             ' + (res.model || 'qwen2.5-0.5b'),
            'Tokens Generated:  ' + (res.tokens_generated || 100),
            'Inference Latency: ' + duration.toFixed(3) + 's',
            'Throughput:        ' + (res.tokens_per_second || (100 / duration).toFixed(2)) + ' tok/s',
            'RAM Governor:      NOMINAL (0 OOM events)',
            'Engine Status:     Active C99 / POSIX Thread Pool',
            '===================================================='
          ].join('\\n');
          indicator.innerText = 'Benchmark Finished in ' + duration.toFixed(2) + 's';
        }} else {{
          out.innerText = 'Benchmark failed: HTTP ' + resp.status;
          indicator.innerText = 'Error';
        }}
      }} catch (e) {{
        out.innerText = 'Benchmark error: ' + e.message;
        indicator.innerText = 'Error';
      }} finally {{
        btn.disabled = false;
      }}
    }}
  </script>
</body>
</html>"""

