from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.comparison.host_runtime.models import BenchmarkTask


REQUIRED_TASK_FIELDS = {"task_id", "prompt", "input_paths", "expected_outputs", "complexity"}


def load_benchmark_tasks(path: Path) -> list[BenchmarkTask]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_tasks: list[dict[str, Any]]
    if isinstance(payload, dict):
        raw_tasks = payload.get("tasks", [])
    elif isinstance(payload, list):
        raw_tasks = payload
    else:
        raise ValueError(f"Benchmark file must contain a list or an object with tasks: {path}")

    tasks: list[BenchmarkTask] = []
    for raw in raw_tasks:
        missing = sorted(REQUIRED_TASK_FIELDS - set(raw))
        if missing:
            task_id = raw.get("task_id", "<unknown>")
            raise ValueError(f"Task {task_id} missing required fields: {', '.join(missing)}")
        tasks.append(
            BenchmarkTask(
                task_id=raw["task_id"],
                prompt=raw["prompt"],
                input_paths=list(raw.get("input_paths", [])),
                expected_outputs=list(raw.get("expected_outputs", [])),
                complexity=str(raw["complexity"]),
                requires_visual_check=bool(raw.get("requires_visual_check", False)),
                metadata=dict(raw.get("metadata", {})),
                scoring=dict(raw.get("scoring", {})),
                mock_behavior=dict(raw.get("mock_behavior", {})),
            )
        )
    return tasks
