# OpenClaw Local (Windows-first, no API keys)

OpenClaw Local is a local-first assistant that runs on a user's own machine with Ollama models (no cloud API keys required).

## Highlights
- Native desktop app mode (`pywebview`) and web mode.
- Multi-chat workspace with **new chat** support.
- **Model picker** for switching between installed Ollama models per chat.
- Local tools for file/system tasks plus automation helpers:
  - Open Google search tabs
  - Open WhatsApp compose links with a prefilled message
  - Open local files in their default app
- Camera page with optional hand-tracking overlays (`/camera`) when vision deps are installed.

## Requirements
- Windows 10/11
- Python 3.10+
- Ollama installed and running locally

## One-click setup (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -Model llama3
```

Then launch:
```powershell
# Desktop app (recommended)
scripts\run_desktop.bat

# Browser UI
scripts\run_ui.bat
```

## Run manually
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
ollama serve
ollama pull llama3
python -m openclaw_local.desktop --model llama3 --host 127.0.0.1 --port 8080
```

## Build a Windows .exe
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```
This produces:
- `dist\OpenClawLocalDesktop.exe`

## Optional vision dependencies
```powershell
pip install -r requirements-vision.txt
```
Then open camera page:
- `http://127.0.0.1:8080/camera`

## Example prompts
- "Open a Google tab for latest Python 3.12 features"
- "Send a WhatsApp message to +15551234567 saying Meeting starts in 10 minutes"
- "Open file docs/notes.txt"
- "List files in C:\\Users\\Me\\Documents"
