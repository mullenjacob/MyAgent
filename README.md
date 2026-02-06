# OpenClaw Local (Windows-first, no API keys)

This is a **local-first** assistant inspired by OpenClaw. It is designed to run entirely on a user's Windows PC using **Ollama** (or any local model that exposes the Ollama-compatible HTTP API). There are **no API keys** and no paid dependencies. The assistant can answer questions, solve problems, and complete tasks behind the scenes with a small, auditable tool set.

> Status: MVP (command-line). UI and background service can be added later.

## Features (current MVP)
- Local chat + reasoning using Ollama (`http://localhost:11434`).
- **Simple web UI** inspired by modern Ollama-style chat interfaces.
- Tool calling for common tasks:
  - Read/write files.
  - List directories.
  - Run shell commands.
- Windows-first configuration guidance.

## Requirements
- Windows 10/11
- Python 3.10+
- [Ollama for Windows](https://ollama.com/) installed and running locally

## Setup (Windows)
### One-click setup (recommended)
1. Install [Ollama for Windows](https://ollama.com/).
2. Double-click `scripts\\setup_windows.ps1` (or run it from PowerShell):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\\scripts\\setup_windows.ps1 -Model llama3
   ```
3. Launch the UI:
   ```powershell
   scripts\\run_ui.bat
   ```

### Manual setup (CLI)
```powershell
# 1) Clone repo
# 2) Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Install deps
pip install -e .

# 4) Make sure Ollama is running
ollama serve

# 5) Pull a model
ollama pull llama3

# 6) Run
python -m openclaw_local.main --model llama3
```

## Usage
```powershell
python -m openclaw_local.main --model llama3
```

## Web UI
```powershell
python -m openclaw_local.ui --model llama3 --host 127.0.0.1 --port 8080
```

Type your request and the assistant will either respond directly or use tools to complete the task locally.

## Configuration
You can control the tool permissions and model settings in `openclaw_local/config.py`.

## Roadmap (suggested)
- Background Windows service with system tray UI.
- GUI with task history and approvals.
- Plugin system for additional tools (email, browser automation, calendar).
- Sandboxed command execution with allowlists.

## Notes
This project ships with a **minimal** toolset for safety and simplicity. Expand tools carefully and consider adding explicit user approvals for sensitive actions.
