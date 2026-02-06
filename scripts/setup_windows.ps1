param(
  [string]$Model = "llama3"
)

$ErrorActionPreference = "Stop"

Write-Host "[OpenClaw Local] Starting setup..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "Python is not installed or not on PATH. Please install Python 3.10+ and re-run." -ForegroundColor Red
  exit 1
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Write-Host "Ollama is not installed or not on PATH. Install from https://ollama.com/download and re-run." -ForegroundColor Red
  exit 1
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path .venv)) {
  Write-Host "Creating virtual environment..." -ForegroundColor Cyan
  python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -e .

Write-Host "Ensuring Ollama server is running..." -ForegroundColor Cyan
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaProcess) {
  Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
  Start-Sleep -Seconds 2
}

Write-Host "Pulling model $Model (this may take a while)..." -ForegroundColor Cyan
ollama pull $Model

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To launch the UI: scripts\\run_ui.bat" -ForegroundColor Green
