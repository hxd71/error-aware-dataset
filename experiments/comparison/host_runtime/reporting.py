from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from experiments.comparison.host_runtime.models import AgentRunTrace, ensure_dir


def write_reports(traces: list[AgentRunTrace], report_dir: Path) -> dict[str, Any]:
    ensure_dir(report_dir)
    task_rows = [_task_row(trace) for trace in traces]
    summary = _summary(task_rows)

    (report_dir / "task_results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in task_rows),
        encoding="utf-8",
    )
    with (report_dir / "task_results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(task_rows[0].keys()) if task_rows else [])
        if task_rows:
            writer.writeheader()
            writer.writerows(task_rows)
    (report_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
    return summary


def _task_row(trace: AgentRunTrace) -> dict[str, Any]:
    attempts = len(trace.attempts)
    first_status = trace.attempts[0].evaluation["agent_visible_report"]["status"] if trace.attempts else "FAIL"
    final_status = trace.final_status
    scoring = trace.scoring_report
    had_failure = any(attempt.evaluation["agent_visible_report"]["status"] == "FAIL" for attempt in trace.attempts)
    visual_required = any(
        bool(attempt.evaluation["agent_visible_report"].get("requires_visual_check", False)) for attempt in trace.attempts
    )
    plugin_used = any(attempt.plugin_diagnosis is not None for attempt in trace.attempts)
    return {
        "task_id": trace.task["task_id"],
        "agent_kind": trace.agent_kind,
        "first_status": first_status,
        "final_status": final_status,
        "attempts": attempts,
        "repair_success": first_status == "FAIL" and final_status == "PASS",
        "had_failure": had_failure,
        "requires_visual_check": visual_required,
        "plugin_used": plugin_used,
        "gold_labels": ";".join(scoring.get("gold_labels", [])),
        "leakage_risk": bool(scoring.get("leakage_risk", False)),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["agent_kind"]].append(row)
    summary: dict[str, Any] = {"agents": {}}
    for agent, agent_rows in grouped.items():
        n = len(agent_rows)
        first_pass = sum(row["first_status"] == "PASS" for row in agent_rows)
        final_pass = sum(row["final_status"] == "PASS" for row in agent_rows)
        repair_candidates = [row for row in agent_rows if row["first_status"] == "FAIL"]
        repair_success = sum(row["repair_success"] for row in repair_candidates)
        visual_rows = [row for row in agent_rows if row["requires_visual_check"]]
        summary["agents"][agent] = {
            "tasks": n,
            "first_pass_rate": first_pass / n if n else 0,
            "final_pass_rate": final_pass / n if n else 0,
            "repair_success_rate": repair_success / len(repair_candidates) if repair_candidates else 0,
            "silent_or_visual_error_detection_count": len(visual_rows),
            "average_attempts": sum(row["attempts"] for row in agent_rows) / n if n else 0,
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    return summary


def _summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Comparison Summary",
        "",
        "| Agent | Tasks | First-pass | Final-pass | Repair success | Avg attempts |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for agent, metrics in summary.get("agents", {}).items():
        lines.append(
            "| {agent} | {tasks} | {first:.2%} | {final:.2%} | {repair:.2%} | {attempts:.2f} |".format(
                agent=agent,
                tasks=metrics["tasks"],
                first=metrics["first_pass_rate"],
                final=metrics["final_pass_rate"],
                repair=metrics["repair_success_rate"],
                attempts=metrics["average_attempts"],
            )
        )
    lines.append("")
    lines.append("Main comparison: error_aware_multi_agent vs self_debug_multi_agent.")
    return "\n".join(lines) + "\n"
