from __future__ import annotations

import argparse
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict

from flask import Flask, Response, jsonify, render_template_string, request

from openclaw_local.agent import OpenClawAgent
from openclaw_local.config import AppConfig, ModelConfig
from openclaw_local.vision import VisionService


@dataclass
class ChatSession:
    chat_id: str
    title: str
    model: str
    messages: list[dict[str, str]] = field(default_factory=list)
    agent: OpenClawAgent | None = None


class ChatStore:
    def __init__(self, base_config: AppConfig) -> None:
        self._base_config = base_config
        self._lock = threading.Lock()
        self._sessions: dict[str, ChatSession] = {}
        self.create_chat(title="New Chat", model=base_config.model.model)

    def _build_agent(self, model: str) -> OpenClawAgent:
        config = AppConfig(
            tool=self._base_config.tool,
            model=ModelConfig(
                base_url=self._base_config.model.base_url,
                model=model,
                request_timeout_s=self._base_config.model.request_timeout_s,
            ),
        )
        return OpenClawAgent(config)

    def create_chat(self, title: str, model: str) -> ChatSession:
        chat_id = str(uuid.uuid4())
        session = ChatSession(
            chat_id=chat_id,
            title=title,
            model=model,
            messages=[],
            agent=self._build_agent(model),
        )
        with self._lock:
            self._sessions[chat_id] = session
        return session

    def list_chats(self) -> list[dict[str, str]]:
        with self._lock:
            return [
                {"id": s.chat_id, "title": s.title, "model": s.model}
                for s in self._sessions.values()
            ]

    def get_chat(self, chat_id: str) -> ChatSession | None:
        with self._lock:
            return self._sessions.get(chat_id)


CAMERA_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenClaw Local Camera</title>
  <style>
    body { background: #0f1115; color: #e6e6e6; font-family: "Segoe UI", sans-serif; margin: 0; }
    .wrap { max-width: 1100px; margin: 20px auto; padding: 16px; }
    h1 { margin: 0 0 8px; }
    .hint { color: #9aa4b2; margin-bottom: 14px; }
    img { width: 100%; border-radius: 12px; border: 1px solid #2a2f3a; background: #000; }
    .error { padding: 12px; border-radius: 10px; background: #3a1f24; color: #ffb7c2; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Live Camera + Hand Tracking</h1>
    <p class="hint">Install <code>requirements-vision.txt</code> to enable overlays.</p>
    __CONTENT__
  </div>
</body>
</html>
"""

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
      font-family: "Inter", "Segoe UI", system-ui, sans-serif;
      --accent:#4f7cff;
      --bubble-radius:16px;
      --bg:#0d1117;
      --text:#e6edf3;
      --muted:#9fb0c7;
      --panel:#0f1724;
      --panel-2:#111b2b;
      --border:#1f2b3d;
      --input:#0c1420;
      --shadow:0 12px 28px rgba(0,0,0,.28);
    }
    [data-theme="light"] { color-scheme: light; }
    * { box-sizing:border-box; }
    body { margin:0; background:radial-gradient(circle at top,#111b2b 0%, var(--bg) 52%); color:var(--text); height:100vh; display:flex; }
    .sidebar { width:290px; background:linear-gradient(180deg,var(--panel),var(--panel-2)); border-right:1px solid var(--border); display:flex; flex-direction:column; }
    .side-top { padding:14px; border-bottom:1px solid var(--border); display:flex; gap:8px; flex-wrap:wrap; }
    .btn { background:var(--accent); color:white; border:none; padding:9px 12px; border-radius:10px; cursor:pointer; font-weight:600; box-shadow:var(--shadow); }
    .btn.secondary { background:#263345; box-shadow:none; }
    .chat-list { flex:1; overflow:auto; padding:10px; display:flex; flex-direction:column; gap:8px; }
    .chat-item { background:#162235; border:1px solid #22324a; border-radius:12px; padding:10px; cursor:pointer; transition:.15s ease; }
    .chat-item:hover { transform:translateY(-1px); border-color:#2f4f7c; }
    .chat-item.active { border-color:var(--accent); background:#1a2a42; }
    .chat-title { font-weight:600; font-size:14px; }
    .chat-model { color:var(--muted); font-size:12px; margin-top:2px; }
    .main { flex:1; display:flex; flex-direction:column; min-width:0; }
    .topbar { padding:14px 18px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; backdrop-filter: blur(6px); }
    .status { color:var(--muted); font-size:13px; }
    .view { flex:1; display:flex; flex-direction:column; min-height:0; }
    .messages { flex:1; overflow:auto; padding:20px; display:flex; flex-direction:column; gap:10px; }
    .bubble { max-width:min(900px,85%); padding:12px 14px; border-radius:var(--bubble-radius); line-height:1.45; white-space:pre-wrap; box-shadow:0 8px 16px rgba(0,0,0,.2); }
    .user { align-self:flex-end; background:linear-gradient(180deg,#3f6cb3,#315a9a); color:#eef4ff; }
    .assistant { align-self:flex-start; background:#17263b; border:1px solid #22324a; }
    .composer { border-top:1px solid var(--border); padding:14px; display:flex; gap:10px; background:rgba(0,0,0,.16); }
    textarea { flex:1; background:var(--input); color:var(--text); border:1px solid #233147; border-radius:12px; padding:10px; min-height:58px; }
    .settings-panel { padding:20px; display:grid; gap:14px; max-width:760px; }
    .setting-card { background:#162235; border:1px solid #233147; border-radius:14px; padding:14px; box-shadow:var(--shadow); }
    .setting-row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
    select, input[type='color'] { background:#0f1724; color:var(--text); border:1px solid #2a3b55; border-radius:10px; padding:8px; }
    .hidden { display:none; }
  </style>
</head>
<body>
  <aside class="sidebar">
    <div class="side-top">
      <button class="btn" id="newChat">+ New Chat</button>
      <button class="btn secondary" id="showSettings">Settings</button>
      <button class="btn secondary" id="openCamera">Camera</button>
    </div>
    <div class="chat-list" id="chatList"></div>
  </aside>
  <main class="main">
    <div class="topbar">
      <div>
        <div id="activeTitle" style="font-weight:600;">OpenClaw Local</div>
        <div class="status" id="status">Checking Ollama connection...</div>
      </div>
      <div class="status" id="activeModelBadge">Model: -</div>
    </div>

    <section class="view" id="chatView">
      <div class="messages" id="messages"></div>
      <form class="composer" id="composer">
        <textarea id="prompt" placeholder="Ask anything or request a task..."></textarea>
        <button class="btn" id="send" type="submit">Send</button>
      </form>
    </section>

    <section class="view hidden" id="settingsView">
      <div class="settings-panel">
        <div class="setting-card">
          <h3 style="margin-top:0;">Appearance</h3>
          <div class="setting-row">
            <label for="themeSelect">Theme</label>
            <select id="themeSelect">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
            <label for="accentPicker">Accent</label>
            <input id="accentPicker" type="color" value="#4f7cff" />
          </div>
        </div>

        <div class="setting-card">
          <h3 style="margin-top:0;">Chat Model</h3>
          <div class="setting-row">
            <label for="modelSelect">Model for current chat</label>
            <select id="modelSelect"></select>
          </div>
        </div>

        <div class="setting-card">
          <h3 style="margin-top:0;">Navigation</h3>
          <button class="btn" id="backToChat" type="button">Back to Chat</button>
        </div>
      </div>
    </section>
  </main>
<script>
  let chats = [];
  let activeChatId = null;
  let models = [];

  const chatList = document.getElementById('chatList');
  const messages = document.getElementById('messages');
  const statusEl = document.getElementById('status');
  const activeTitle = document.getElementById('activeTitle');
  const activeModelBadge = document.getElementById('activeModelBadge');
  const modelSelect = document.getElementById('modelSelect');
  const prompt = document.getElementById('prompt');
  const sendBtn = document.getElementById('send');
  const themeSelect = document.getElementById('themeSelect');
  const accentPicker = document.getElementById('accentPicker');
  const chatView = document.getElementById('chatView');
  const settingsView = document.getElementById('settingsView');

  function showSettings() {
    chatView.classList.add('hidden');
    settingsView.classList.remove('hidden');
  }

  function showChat() {
    settingsView.classList.add('hidden');
    chatView.classList.remove('hidden');
  }

  function applyTheme(theme, accent) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') {
      document.documentElement.style.setProperty('--bg', '#eef2f8');
      document.documentElement.style.setProperty('--text', '#172030');
      document.documentElement.style.setProperty('--panel', '#ffffff');
      document.documentElement.style.setProperty('--border', '#d6dde9');
    } else {
      document.documentElement.style.setProperty('--bg', '#0f1115');
      document.documentElement.style.setProperty('--text', '#e8ebf2');
      document.documentElement.style.setProperty('--panel', '#121822');
      document.documentElement.style.setProperty('--border', '#243041');
    }
    document.documentElement.style.setProperty('--accent', accent);
    localStorage.setItem('uiTheme', theme);
    localStorage.setItem('uiAccent', accent);
  }

  async function safeFetchJson(url, options) {
    try {
      const resp = await fetch(url, options);
      if (!resp.ok) return null;
      return await resp.json();
    } catch (_err) {
      return null;
    }
  }

  function renderChats() {
    chatList.innerHTML = '';
    for (const chat of chats) {
      const div = document.createElement('div');
      div.className = 'chat-item' + (chat.id === activeChatId ? ' active' : '');
      div.innerHTML = `<div class="chat-title">${chat.title}</div><div class="chat-model">${chat.model}</div>`;
      div.onclick = async () => {
        await loadChat(chat.id);
        showChat();
      };
      chatList.appendChild(div);
    }
  }

  function renderMessages(list) {
    messages.innerHTML = '';
    for (const m of list) {
      const b = document.createElement('div');
      b.className = `bubble ${m.role}`;
      b.textContent = m.content;
      messages.appendChild(b);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  async function loadStatus() {
    const data = await safeFetchJson('/api/status');
    if (data && data.ok) {
      models = data.models || [];
      statusEl.textContent = `Connected to Ollama • ${models.length} model(s)`;
    } else {
      models = [];
      statusEl.textContent = 'Ollama not connected. Start Ollama then refresh.';
    }

    modelSelect.innerHTML = '';
    const availableModels = models.length ? models : ['llama3'];
    for (const model of availableModels) {
      const o = document.createElement('option');
      o.value = model;
      o.textContent = model;
      modelSelect.appendChild(o);
    }
  }

  async function loadChats() {
    const data = await safeFetchJson('/api/chats');
    chats = (data && data.chats) ? data.chats : [];
    if (!activeChatId && chats.length) activeChatId = chats[0].id;
    renderChats();
    if (activeChatId) await loadChat(activeChatId);
  }

  async function loadChat(chatId) {
    const data = await safeFetchJson(`/api/chats/${chatId}`);
    if (!data) return;
    activeChatId = data.id;
    activeTitle.textContent = data.title;
    activeModelBadge.textContent = `Model: ${data.model}`;
    renderChats();
    renderMessages(data.messages || []);
    if (modelSelect.options.length) modelSelect.value = data.model;
  }

  document.getElementById('newChat').onclick = async () => {
    const model = modelSelect.value || (models[0] || 'llama3');
    const data = await safeFetchJson('/api/chats', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({title:'New Chat', model})
    });
    if (!data) return;
    chats.push(data);
    activeChatId = data.id;
    renderChats();
    await loadChat(activeChatId);
    showChat();
  };

  document.getElementById('showSettings').onclick = () => showSettings();
  document.getElementById('backToChat').onclick = () => showChat();
  document.getElementById('openCamera').onclick = () => window.open('/camera', '_blank');

  modelSelect.onchange = async () => {
    if (!activeChatId) return;
    await safeFetchJson(`/api/chats/${activeChatId}/model`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({model:modelSelect.value})
    });
    await loadChat(activeChatId);
    await loadChats();
  };

  document.getElementById('composer').onsubmit = async (e) => {
    e.preventDefault();
    const message = prompt.value.trim();
    if (!message || !activeChatId) return;
    prompt.value = '';
    sendBtn.disabled = true;
    try {
      await safeFetchJson(`/api/chats/${activeChatId}/messages`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message})
      });
      await loadChat(activeChatId);
    } finally {
      sendBtn.disabled = false;
    }
  };

  themeSelect.onchange = () => applyTheme(themeSelect.value, accentPicker.value);
  accentPicker.oninput = () => applyTheme(themeSelect.value, accentPicker.value);

  (async function init(){
    const savedTheme = localStorage.getItem('uiTheme') || 'dark';
    const savedAccent = localStorage.getItem('uiAccent') || '#4f7cff';
    themeSelect.value = savedTheme;
    accentPicker.value = savedAccent;
    applyTheme(savedTheme, savedAccent);
    await loadStatus();
    await loadChats();
    showChat();
  })();
</script>
</body>
</html>
"""


def create_app(config: AppConfig) -> Flask:
    app = Flask(__name__)
    vision = VisionService()
    store = ChatStore(config)

    @app.get("/")
    def index() -> str:
        return render_template_string(HTML_TEMPLATE)

    @app.get("/favicon.ico")
    def favicon() -> tuple[str, int]:
        return "", 204

    @app.get("/camera")
    def camera_page() -> str:
        support = vision.support()
        if not support.ok:
            missing = []
            if not support.cv2_available:
                missing.append("opencv-python")
            if not support.mediapipe_available:
                missing.append("mediapipe")
            content = (
                f'<div class="error">Missing dependencies: {", ".join(missing)}. '
                'Install requirements-vision.txt.</div>'
            )
            return render_template_string(CAMERA_TEMPLATE.replace("__CONTENT__", content))
        return render_template_string(
            CAMERA_TEMPLATE.replace("__CONTENT__", '<img src="/video_feed" alt="live camera" />')
        )

    @app.get("/video_feed")
    def video_feed() -> Response:
        support = vision.support()
        if not support.ok:
            return Response("Vision dependencies missing", status=503)
        return Response(
            vision.stream_mjpeg(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.get("/api/status")
    def status() -> Dict[str, Any]:
        first = store.list_chats()[0]
        session = store.get_chat(first["id"])
        if session is None or session.agent is None:
            return jsonify({"ok": False, "models": [], "error": "No chat session"})
        return jsonify(session.agent.status())

    @app.get("/api/chats")
    def chats() -> Dict[str, Any]:
        return jsonify({"chats": store.list_chats()})

    @app.post("/api/chats")
    def create_chat() -> Dict[str, Any]:
        payload = request.get_json(silent=True) or {}
        title = str(payload.get("title", "New Chat"))
        model = str(payload.get("model", config.model.model))
        session = store.create_chat(title=title, model=model)
        return jsonify({"id": session.chat_id, "title": session.title, "model": session.model})

    @app.get("/api/chats/<chat_id>")
    def get_chat(chat_id: str) -> Dict[str, Any]:
        session = store.get_chat(chat_id)
        if session is None:
            return jsonify({"error": "chat not found"}), 404
        return jsonify(
            {
                "id": session.chat_id,
                "title": session.title,
                "model": session.model,
                "messages": session.messages,
            }
        )

    @app.post("/api/chats/<chat_id>/model")
    def set_chat_model(chat_id: str) -> Dict[str, Any]:
        payload = request.get_json(silent=True) or {}
        model = str(payload.get("model", config.model.model))
        session = store.get_chat(chat_id)
        if session is None:
            return jsonify({"error": "chat not found"}), 404
        session.model = model
        session.agent = store._build_agent(model)
        session.messages.append(
            {
                "role": "assistant",
                "content": f"Switched model to {model}. New context started for this chat.",
            }
        )
        return jsonify({"ok": True, "model": model})

    @app.post("/api/chats/<chat_id>/messages")
    def chat_message(chat_id: str) -> Dict[str, Any]:
        session = store.get_chat(chat_id)
        if session is None or session.agent is None:
            return jsonify({"error": "chat not found"}), 404

        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        if not message:
            return jsonify({"reply": "Please enter a message."})

        session.messages.append({"role": "user", "content": message})
        reply = session.agent.ask(message)
        session.messages.append({"role": "assistant", "content": reply})
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
