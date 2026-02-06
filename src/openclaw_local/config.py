from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolConfig:
    allow_run_command: bool = True
    allow_file_write: bool = True
    allow_file_read: bool = True
    allow_list_dir: bool = True
    working_directory: Path = Path.cwd()


@dataclass(frozen=True)
class ModelConfig:
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    request_timeout_s: int = 120


@dataclass(frozen=True)
class AppConfig:
    tool: ToolConfig = ToolConfig()
    model: ModelConfig = ModelConfig()
