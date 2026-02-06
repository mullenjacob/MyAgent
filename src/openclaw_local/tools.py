from __future__ import annotations

import importlib
import os
import shlex
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

from openclaw_local.config import ToolConfig


@dataclass
class ToolResult:
    ok: bool
    output: str


class ToolExecutor:
    def __init__(self, config: ToolConfig) -> None:
        self._config = config

    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return self._config.working_directory / candidate

    def list_dir(self, path: str | None = None) -> ToolResult:
        if not self._config.allow_list_dir:
            return ToolResult(False, "list_dir is disabled by configuration")
        target = self._resolve_path(path) if path else Path(self._config.working_directory)
        if not target.exists():
            return ToolResult(False, f"Path does not exist: {target}")
        if not target.is_dir():
            return ToolResult(False, f"Path is not a directory: {target}")
        entries = sorted(p.name for p in target.iterdir())
        return ToolResult(True, "\n".join(entries))

    def read_file(self, path: str) -> ToolResult:
        if not self._config.allow_file_read:
            return ToolResult(False, "read_file is disabled by configuration")
        target = self._resolve_path(path)
        if not target.exists():
            return ToolResult(False, f"File does not exist: {target}")
        if not target.is_file():
            return ToolResult(False, f"Path is not a file: {target}")
        return ToolResult(True, target.read_text(encoding="utf-8"))

    def write_file(self, path: str, content: str) -> ToolResult:
        if not self._config.allow_file_write:
            return ToolResult(False, "write_file is disabled by configuration")
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Wrote {len(content)} characters to {target}")

    def run_command(self, command: str) -> ToolResult:
        if not self._config.allow_run_command:
            return ToolResult(False, "run_command is disabled by configuration")
        args = shlex.split(command, posix=os.name != "nt")
        try:
            result = subprocess.run(
                args,
                cwd=self._config.working_directory,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            return ToolResult(False, f"Command failed: {exc}")
        output_parts: List[str] = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(result.stderr)
        if not output_parts:
            output_parts.append("(no output)")
        return ToolResult(result.returncode == 0, "\n".join(output_parts).strip())

    def camera_snapshot(self) -> ToolResult:
        spec = importlib.util.find_spec("cv2")
        if spec is None:
            return ToolResult(
                False,
                "OpenCV is not installed. Install requirements-vision.txt to enable camera.",
            )
        cv2 = importlib.import_module("cv2")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return ToolResult(False, "Unable to access camera 0")
        success, frame = cap.read()
        cap.release()
        if not success:
            return ToolResult(False, "Failed to capture frame")
        height, width = frame.shape[:2]
        return ToolResult(True, f"Captured frame {width}x{height}")

    def open_google_tab(self, query: str) -> ToolResult:
        q = quote_plus(query.strip())
        url = f"https://www.google.com/search?q={q}" if q else "https://www.google.com"
        opened = webbrowser.open(url, new=2)
        if not opened:
            return ToolResult(False, f"Failed to open browser for URL: {url}")
        return ToolResult(True, f"Opened Google tab: {url}")

    def send_whatsapp_message(self, phone: str, message: str) -> ToolResult:
        encoded = quote_plus(message)
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded}"
        opened = webbrowser.open(url, new=2)
        if not opened:
            return ToolResult(False, "Failed to open WhatsApp web")
        return ToolResult(True, f"Opened WhatsApp compose URL for {phone}")

    def open_file_with_default_app(self, path: str) -> ToolResult:
        target = self._resolve_path(path)
        if not target.exists():
            return ToolResult(False, f"File does not exist: {target}")

        if os.name == "nt":
            os.startfile(str(target))  # type: ignore[attr-defined]
            return ToolResult(True, f"Opened file: {target}")

        if sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
            return ToolResult(True, f"Opened file: {target}")

        subprocess.run(["xdg-open", str(target)], check=False)
        return ToolResult(True, f"Opened file: {target}")

    def open_url(self, url: str) -> ToolResult:
        opened = webbrowser.open(url, new=2)
        if not opened:
            return ToolResult(False, f"Failed to open URL: {url}")
        return ToolResult(True, f"Opened URL: {url}")

    def execute(self, tool: str, args: Dict[str, Any]) -> ToolResult:
        if tool == "list_dir":
            return self.list_dir(path=args.get("path"))
        if tool == "read_file":
            return self.read_file(path=args.get("path", ""))
        if tool == "write_file":
            return self.write_file(path=args.get("path", ""), content=args.get("content", ""))
        if tool == "run_command":
            return self.run_command(command=args.get("command", ""))
        if tool == "camera_snapshot":
            return self.camera_snapshot()
        if tool == "open_google_tab":
            return self.open_google_tab(query=args.get("query", ""))
        if tool == "send_whatsapp_message":
            return self.send_whatsapp_message(
                phone=args.get("phone", ""),
                message=args.get("message", ""),
            )
        if tool == "open_file":
            return self.open_file_with_default_app(path=args.get("path", ""))
        if tool == "open_url":
            return self.open_url(url=args.get("url", ""))
        return ToolResult(False, f"Unknown tool: {tool}")
