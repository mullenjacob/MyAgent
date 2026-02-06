$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path .venv)) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .
pip install pyinstaller

pyinstaller --noconfirm --clean --onefile --name OpenClawLocalDesktop `
  src/openclaw_local/desktop.py

Write-Host "Build finished. EXE is in dist\\OpenClawLocalDesktop.exe" -ForegroundColor Green
