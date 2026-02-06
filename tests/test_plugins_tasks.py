from openclaw_local.plugins import Plugin, PluginRegistry
from openclaw_local.tasks import Task, TaskRunner


def test_plugin_registry() -> None:
    registry = PluginRegistry()
    plugin = Plugin(name="echo", description="Echo plugin", handler=lambda x: x)
    registry.register(plugin)
    assert [p.name for p in registry.list()] == ["echo"]
    assert registry.run("echo", "hi") == "hi"


def test_task_runner() -> None:
    runner = TaskRunner()
    runner.add(Task(name="one", action=lambda: "ok"))
    results = runner.run_all()
    assert results[0].name == "one"
    assert results[0].output == "ok"
