from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class Task:
    name: str
    action: Callable[[], str]


@dataclass
class TaskResult:
    name: str
    output: str


@dataclass
class TaskRunner:
    tasks: List[Task] = field(default_factory=list)

    def add(self, task: Task) -> None:
        self.tasks.append(task)

    def run_all(self) -> List[TaskResult]:
        results: List[TaskResult] = []
        for task in self.tasks:
            results.append(TaskResult(name=task.name, output=task.action()))
        return results
