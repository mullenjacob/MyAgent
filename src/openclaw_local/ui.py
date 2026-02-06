from __future__ import annotations

import argparse
from typing import Any, Dict

from flask import Flask, jsonify, render_template_string, request

from openclaw_local.agent import OpenClawAgent
from openclaw_local.config import AppConfig, ModelConfig

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenClaw Local</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: #0f1115;
      color: #e6e6e6;
    }
    body {
      margin: 0;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    header {
      padding: 16px 24px 12px;
      border-bottom: 1px solid #1e222a;
      background: #12151b;
    }
    .title {
      font-size: 18px;
      font-weight: 600;
    }
    .status {
      margin-top: 6px;
      font-size: 13px;
      color: #9aa4b2;
    }
    .chat {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
    }
    .message {
      max-width: 820px;
      margin: 0 auto 16px;
      padding: 14px 16px;
      border-radius: 12px;
      background: #1b1f27;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .message.user {
      background: #223248;
    }
    .composer {
      padding: 16px 24px 24px;
      border-top: 1px solid #1e222a;
      background: #12151b;
      display: flex;
      gap: 12px;
    }
    textarea {
      flex: 1;
      min-height: 56px;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid #2a2f3a;
      background: #0f1115;
      color: #e6e6e6;
      resize: vertical;
    }
    button {
      padding: 12px 20px;
      border-radius: 10px;
      border: none;
      background: #4f7cff;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  </style>
</head>
<body>
  <header>
    <div class="title">OpenClaw Local</div>
    <div class="status" id="status">Checking Ollama status...</div>
  </header>
  <div id="chat" class="chat"></div>
  <form id="composer" class="composer">
    <textarea id="prompt" placeholder="Ask anything..." required></textarea>
    <button id="send" type="submit">Send</button>
  </form>
  <script>
    const chat = document.getElementById('chat');
    const status = document.getElementById('status');
    const form = document.getElementById('composer');
    const prompt = document.getElementById('prompt');
    const sendBtn = document.getElementById('send');

    const addMessage = (text, role) => {
      const bubble = document.createElement('div');
      bubble.className = `message ${role}`;
      bubble.textContent = text;
      chat.appendChild(bubble);
      chat.scrollTop = chat.scrollHeight;
    };

    const loadStatus = async () => {
      try {
        const response = await fetch('/api/status');
        const data = await response.json();
        if (data.ok) {
          const models = data.models.length ? data.models.join(', ') : 'No models found';
          status.textContent = `Ollama: connected • Models: ${models}`;
        } else {
          status.textContent = `Ollama: unavailable • ${data.error}`;
        }
      } catch (err) {
        status.textContent = `Ollama: unavailable • ${err.message}`;
      }
    };

    loadStatus();

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const text = prompt.value.trim();
      if (!text) return;
      addMessage(text, 'user');
      prompt.value = '';
      sendBtn.disabled = true;

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        addMessage(data.reply, 'assistant');
      } catch (err) {
        addMessage('Error: ' + err.message, 'assistant');
      } finally {
        sendBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def create_app(config: AppConfig) -> Flask:
    app = Flask(__name__)
    agent = OpenClawAgent(config)

    @app.get("/")
    def index() -> str:
        return render_template_string(HTML_TEMPLATE)

    @app.get("/favicon.ico")
    def favicon() -> tuple[str, int]:
        return "", 204

    @app.get("/api/status")
    def status() -> Dict[str, Any]:
        return jsonify(agent.status())

    @app.post("/api/chat")
    def chat() -> Dict[str, Any]:
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        if not message:
            return jsonify({"reply": "Please enter a message."})
        reply = agent.ask(message)
        return jsonify({"reply": reply})

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw Local UI server")
    parser.add_argument("--model", default="llama3", help="Ollama model name")
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama base URL",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AppConfig(model=ModelConfig(base_url=args.base_url, model=args.model))
    app = create_app(config)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
