@echo off
setlocal
cd /d %~dp0\..
call .venv\Scripts\activate
python -m openclaw_local.ui --model llama3 --host 127.0.0.1 --port 8080
endlocal
