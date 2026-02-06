from pathlib import Path

from openclaw_local.config import ToolConfig
from openclaw_local.tools import ToolExecutor


def test_write_and_read_file(tmp_path: Path) -> None:
    config = ToolConfig(working_directory=tmp_path)
    executor = ToolExecutor(config)
    target = tmp_path / "note.txt"

    write_result = executor.write_file(str(target), "hello")
    assert write_result.ok is True

    read_result = executor.read_file(str(target))
    assert read_result.ok is True
    assert read_result.output == "hello"


def test_list_dir(tmp_path: Path) -> None:
    config = ToolConfig(working_directory=tmp_path)
    executor = ToolExecutor(config)
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")

    result = executor.list_dir()
    assert result.ok is True
    assert "a.txt" in result.output
    assert "b.txt" in result.output
