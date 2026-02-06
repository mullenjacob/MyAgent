import os
from pathlib import Path

from openclaw_local.config import ToolConfig
from openclaw_local.tools import ToolExecutor


def test_open_google_tab(monkeypatch, tmp_path: Path) -> None:
    config = ToolConfig(working_directory=tmp_path)
    executor = ToolExecutor(config)

    called = {}

    def fake_open(url: str, new: int = 0):
        called["url"] = url
        called["new"] = new
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)
    result = executor.open_google_tab("python testing")
    assert result.ok is True
    assert "google.com/search" in called["url"]


def test_send_whatsapp_message(monkeypatch, tmp_path: Path) -> None:
    config = ToolConfig(working_directory=tmp_path)
    executor = ToolExecutor(config)

    called = {}

    def fake_open(url: str, new: int = 0):
        called["url"] = url
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)
    result = executor.send_whatsapp_message("+15551234567", "hello there")
    assert result.ok is True
    assert "web.whatsapp.com/send" in called["url"]


def test_open_file_with_default_app_linux(monkeypatch, tmp_path: Path) -> None:
    config = ToolConfig(working_directory=tmp_path)
    executor = ToolExecutor(config)
    target = tmp_path / "a.txt"
    target.write_text("a")

    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr("sys.platform", "linux")

    called = {}

    def fake_run(args, check=False):
        called["args"] = args

    monkeypatch.setattr("subprocess.run", fake_run)
    result = executor.open_file_with_default_app("a.txt")
    assert result.ok is True
    assert called["args"][0] == "xdg-open"
