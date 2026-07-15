from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from experiments.comparison.adapters.benchmark_loader import load_benchmark_tasks


def audit_benchmark_leakage(repo_root: Path, benchmark_path: Path) -> dict[str, Any]:
    tasks = load_benchmark_tasks(benchmark_path)
    cases_path = repo_root / "knowledge_base" / "cases" / "all_cases.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    case_ids = {case["sample_id"].lower() for case in cases}
    case_paths = {Path(case["sample_path"]).name.lower() for case in cases}
    case_terms = set()
    for case in cases:
        case_terms.update(_strong_terms(case.get("retrieval_text", "")))

    findings = []
    for task in tasks:
        text = " ".join([task.task_id, task.prompt, " ".join(task.input_paths), " ".join(task.expected_outputs)]).lower()
        path_names = {Path(path).name.lower() for path in task.input_paths + task.expected_outputs}
        sample_id_hits = sorted(sample_id for sample_id in case_ids if sample_id and sample_id in text)
        path_hits = sorted(path_names & case_paths)
        term_overlap = sorted(_strong_terms(text) & case_terms)
        leakage_risk = bool(sample_id_hits or path_hits or len(term_overlap) >= 12)
        findings.append(
            {
                "task_id": task.task_id,
                "leakage_risk": leakage_risk,
                "sample_id_hits": sample_id_hits,
                "path_name_hits": path_hits,
                "strong_term_overlap_count": len(term_overlap),
                "strong_term_overlap_preview": term_overlap[:20],
            }
        )
    return {
        "schema_version": "0.1.0",
        "benchmark_path": benchmark_path.as_posix(),
        "case_kb": cases_path.relative_to(repo_root).as_posix(),
        "tasks": findings,
        "leakage_risk_count": sum(item["leakage_risk"] for item in findings),
    }


def _strong_terms(text: str) -> set[str]:
    stop = {
        "the",
        "and",
        "with",
        "from",
        "into",
        "输出",
        "任务",
        "结果",
        "空间",
        "错误",
        "数据",
        "分析",
    }
    terms = set(re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]{4,}", text.lower()))
    return {term for term in terms if term not in stop}
