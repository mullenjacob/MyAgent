from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from openclaw_local.config import ToolConfig


@dataclass
class ToolResult:
    ok: bool
    output: str


class ToolExecutor:
    def __init__(self, config: ToolConfig) -> None:
        self._config = config

    def list_dir(self, path: str | None = None) -> ToolResult:
        if not self._config.allow_list_dir:
            return ToolResult(False, "list_dir is disabled by configuration")
        target = Path(path or self._config.working_directory)
        if not target.exists():
            return ToolResult(False, f"Path does not exist: {target}")
        if not target.is_dir():
            return ToolResult(False, f"Path is not a directory: {target}")
        entries = sorted(p.name for p in target.iterdir())
        return ToolResult(True, "\n".join(entries))

    def read_file(self, path: str) -> ToolResult:
        if not self._config.allow_file_read:
            return ToolResult(False, "read_file is disabled by configuration")
        target = Path(path)
        if not target.exists():
            return ToolResult(False, f"File does not exist: {target}")
        if not target.is_file():
            return ToolResult(False, f"Path is not a file: {target}")
        return ToolResult(True, target.read_text(encoding="utf-8"))

    def write_file(self, path: str, content: str) -> ToolResult:
        if not self._config.allow_file_write:
            return ToolResult(False, "write_file is disabled by configuration")
        target = Path(path)
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

    def execute(self, tool: str, args: Dict[str, Any]) -> ToolResult:
        if tool == "list_dir":
            return self.list_dir(path=args.get("path"))
        if tool == "read_file":
            return self.read_file(path=args.get("path", ""))
        if tool == "write_file":
            return self.write_file(path=args.get("path", ""), content=args.get("content", ""))
        if tool == "run_command":
            return self.run_command(command=args.get("command", ""))
        return ToolResult(False, f"Unknown tool: {tool}")
