from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from experiments.comparison.host_runtime.models import BenchmarkTask


REQUIRED_TASK_FIELDS = {"task_id", "prompt", "input_paths", "expected_outputs", "complexity"}
OUTPUT_FILE_RE = re.compile(
    r"[\w\u4e00-\u9fff.\-()]+?\.(?:shp|tif|tiff|gpkg|csv|png|txt|html|geojson|json|xlsx)",
    re.IGNORECASE,
)
CURATED_INVALID_BENCHMARK_TASKS: dict[str, str] = {
    "curated_geoagent_037": "curated_evaluator_did_not_emit_json",
    "curated_geoagent_043": "curated_source_dataset_missing",
    "curated_geoagent_072": "curated_source_dataset_missing",
    "curated_geoagent_095": "curated_evaluator_did_not_emit_json",
    "curated_geoagent_132": "curated_source_dataset_missing",
}


def load_benchmark_tasks(path: Path) -> list[BenchmarkTask]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_tasks: list[dict[str, Any]]
    if isinstance(payload, dict):
        if "tasks" in payload:
            raw_tasks = payload["tasks"]
        elif "cases" in payload:
            return _load_curated_geoagent_cases(payload, path.parent)
        else:
            raise ValueError(f"Benchmark object must contain tasks or cases: {path}")
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


def split_manual_review_tasks(tasks: list[BenchmarkTask]) -> tuple[list[BenchmarkTask], list[BenchmarkTask]]:
    runnable: list[BenchmarkTask] = []
    manual_review: list[BenchmarkTask] = []
    for task in tasks:
        if bool(task.scoring.get("manual_review_required", False)):
            manual_review.append(task)
        else:
            runnable.append(task)
    return runnable, manual_review


def split_invalid_benchmark_tasks(tasks: list[BenchmarkTask]) -> tuple[list[BenchmarkTask], list[BenchmarkTask]]:
    runnable: list[BenchmarkTask] = []
    invalid: list[BenchmarkTask] = []
    for task in tasks:
        if bool(task.scoring.get("invalid_benchmark_task", False)):
            invalid.append(task)
        else:
            runnable.append(task)
    return runnable, invalid


def task_skip_record(task: BenchmarkTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "complexity": task.complexity,
        "evaluation_mode": task.scoring.get("evaluation_mode"),
        "manual_review_required": bool(task.scoring.get("manual_review_required", False)),
        "reason": "manual_or_hybrid_review_required",
    }


def invalid_task_skip_record(task: BenchmarkTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "complexity": task.complexity,
        "evaluation_mode": task.scoring.get("evaluation_mode"),
        "manual_review_required": bool(task.scoring.get("manual_review_required", False)),
        "invalid_benchmark_task": True,
        "invalid_reason": task.scoring.get("invalid_reason", "invalid_benchmark_task"),
        "reason": "invalid_benchmark_task_excluded_from_formal_scoring",
    }


def _load_curated_geoagent_cases(payload: dict[str, Any], dataset_root: Path) -> list[BenchmarkTask]:
    tasks: list[BenchmarkTask] = []
    dataset_root = dataset_root.resolve()
    dataset_id = str(payload.get("dataset_id", "curated_geoagent"))
    for raw in payload.get("cases", []):
        case_id = str(raw["case_id"])
        evaluation = dict(raw.get("evaluation", {}))
        assets = list(raw.get("assets", []))
        output_requirements = str(raw.get("output_requirements", ""))
        prompt = _compose_curated_prompt(raw)
        invalid_reason = CURATED_INVALID_BENCHMARK_TASKS.get(case_id, "")
        tasks.append(
            BenchmarkTask(
                task_id=case_id,
                prompt=prompt,
                input_paths=[_resolve_asset_path(dataset_root, str(asset.get("path", ""))) for asset in assets],
                expected_outputs=_extract_expected_outputs(output_requirements),
                complexity=str(raw.get("task_level", "")),
                requires_visual_check=bool(evaluation.get("manual_review_required", False)),
                metadata={
                    "dataset_id": dataset_id,
                    "task_level": raw.get("task_level"),
                    "asset_types": sorted({str(asset.get("asset_type", "")) for asset in assets if asset.get("asset_type")}),
                    "asset_count": len(assets),
                    "output_requirements": output_requirements,
                },
                scoring={
                    "benchmark_format": "curated_geoagent",
                    "dataset_root": dataset_root.as_posix(),
                    "case_id": case_id,
                    "source_id": raw.get("source_id"),
                    "evaluation_mode": evaluation.get("mode"),
                    "evaluator": evaluation.get("evaluator"),
                    "manual_review_required": bool(evaluation.get("manual_review_required", False)),
                    "manual_rubric": evaluation.get("manual_rubric"),
                    "asset_resolution_status": evaluation.get("asset_resolution_status"),
                    "missing_paths": list(evaluation.get("missing_paths", [])),
                    "invalid_benchmark_task": bool(invalid_reason),
                    "invalid_reason": invalid_reason,
                },
            )
        )
    return tasks


def _compose_curated_prompt(raw: dict[str, Any]) -> str:
    task = str(raw.get("task", "")).strip()
    output_requirements = str(raw.get("output_requirements", "")).strip()
    if not output_requirements:
        return task
    return f"{task}\n\nOutput requirements:\n{output_requirements}"


def _resolve_asset_path(dataset_root: Path, asset_path: str) -> str:
    path = Path(asset_path)
    if path.is_absolute():
        return path.as_posix()
    return (dataset_root / path).resolve(strict=False).as_posix()


def _extract_expected_outputs(output_requirements: str) -> list[str]:
    seen: set[str] = set()
    outputs: list[str] = []
    for match in OUTPUT_FILE_RE.findall(output_requirements):
        cleaned = match.strip("`'\".,;:()[]{}")
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            outputs.append(cleaned)
    return outputs
