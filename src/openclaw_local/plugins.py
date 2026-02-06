from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable


@dataclass(frozen=True)
class Plugin:
    name: str
    description: str
    handler: Callable[[str], str]


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")
        self._plugins[plugin.name] = plugin

    def list(self) -> Iterable[Plugin]:
        return self._plugins.values()

    def run(self, name: str, payload: str) -> str:
        if name not in self._plugins:
            raise KeyError(f"Unknown plugin: {name}")
        return self._plugins[name].handler(payload)
