from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from experiments.comparison.host_runtime.models import AgentRunTrace, ensure_dir


def write_reports(
    traces: list[AgentRunTrace],
    report_dir: Path,
    run_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_dir(report_dir)
    task_rows = [_task_row(trace) for trace in traces]
    summary = _summary(task_rows, run_scope or {})

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
    scoring_details = scoring.get("details", {}) if isinstance(scoring.get("details", {}), dict) else {}
    invalid_benchmark_task = bool(scoring_details.get("invalid_benchmark_task", False)) or scoring.get("notes") == "invalid_benchmark_task"
    manual_review_required = bool(scoring_details.get("manual_review_required", False))
    score_eligible = not invalid_benchmark_task and not manual_review_required
    had_failure = any(attempt.evaluation["agent_visible_report"]["status"] == "FAIL" for attempt in trace.attempts)
    failure_kinds = [
        str(attempt.evaluation["agent_visible_report"].get("failure_kind", ""))
        for attempt in trace.attempts
    ]
    silent_or_metric_detected = any(
        kind in {"silent_logic_error", "metric_mismatch"} for kind in failure_kinds
    )
    visual_required = any(
        bool(attempt.evaluation["agent_visible_report"].get("requires_visual_check", False)) for attempt in trace.attempts
    )
    plugin_used = any(attempt.plugin_diagnosis is not None for attempt in trace.attempts)
    correction_triggered = any(attempt.repair_instruction is not None for attempt in trace.attempts)
    correction_success = correction_triggered and final_status == "PASS"
    anti_regression = trace.runtime.get("anti_regression", {}) if isinstance(trace.runtime, dict) else {}
    anti_regression_switch_count = int(anti_regression.get("best_source_switch_count", 0) or 0)
    total_token_usage = _trace_token_usage(trace)
    repair_token_usage = _repair_token_usage(trace)
    first_attempt_token_usage = (
        _normalize_token_usage(trace.attempts[0].token_usage) if trace.attempts else _zero_token_usage()
    )
    step_branch_triggered = any(
        (attempt.repair_instruction or {}).get("step_branch_plan", {}).get("mode") == "step_branch_repair"
        for attempt in trace.attempts
    )
    step_manifest_available = any(_has_step_manifest(attempt.step_evaluation) for attempt in trace.attempts)
    first_step_manifest_available = _has_step_manifest(trace.attempts[0].step_evaluation) if trace.attempts else False
    step_branch_inferred_from_final_signal = any(
        (attempt.repair_instruction or {})
        .get("step_branch_plan", {})
        .get("suspected_failed_step", {})
        .get("source")
        == "inferred_from_failure_signal"
        for attempt in trace.attempts
    )
    return {
        "task_id": trace.task["task_id"],
        "agent_kind": trace.agent_kind,
        "first_status": first_status,
        "final_status": final_status,
        "attempts": attempts,
        "repair_success": first_status == "FAIL" and final_status == "PASS",
        "correction_triggered": correction_triggered,
        "correction_success": correction_success,
        "step_branch_triggered": step_branch_triggered,
        "step_manifest_available": step_manifest_available,
        "first_step_manifest_available": first_step_manifest_available,
        "step_branch_inferred_from_final_signal": step_branch_inferred_from_final_signal,
        "anti_regression_switch_count": anti_regression_switch_count,
        "anti_regression_used": anti_regression_switch_count > 0,
        "had_failure": had_failure,
        "failure_kinds": ";".join(kind for kind in failure_kinds if kind),
        "silent_or_metric_error_detected": silent_or_metric_detected,
        "requires_visual_check": visual_required,
        "plugin_used": plugin_used,
        "score_eligible": score_eligible,
        "invalid_benchmark_task": invalid_benchmark_task,
        "manual_review_required": manual_review_required,
        "gold_labels": ";".join(scoring.get("gold_labels", [])),
        "leakage_risk": bool(scoring.get("leakage_risk", False)),
        "prompt_tokens": total_token_usage["prompt_tokens"],
        "completion_tokens": total_token_usage["completion_tokens"],
        "total_tokens": total_token_usage["total_tokens"],
        "repair_prompt_tokens": repair_token_usage["prompt_tokens"],
        "repair_completion_tokens": repair_token_usage["completion_tokens"],
        "repair_total_tokens": repair_token_usage["total_tokens"],
        "first_attempt_prompt_tokens": first_attempt_token_usage["prompt_tokens"],
        "first_attempt_completion_tokens": first_attempt_token_usage["completion_tokens"],
        "first_attempt_total_tokens": first_attempt_token_usage["total_tokens"],
    }


def _summary(rows: list[dict[str, Any]], run_scope: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["agent_kind"]].append(row)
    summary: dict[str, Any] = {
        "auto_task_count": run_scope.get("auto_task_count", len({row["task_id"] for row in rows})),
        "valid_auto_task_count": run_scope.get("valid_auto_task_count", 0),
        "invalid_benchmark_task_count": run_scope.get("invalid_benchmark_task_count", 0),
        "skipped_manual_review_count": run_scope.get("skipped_manual_review_count", 0),
        "skipped_invalid_benchmark_task_count": run_scope.get("skipped_invalid_benchmark_task_count", 0),
        "executed_task_count": run_scope.get("executed_task_count", len({row["task_id"] for row in rows})),
        "run_scope": run_scope,
        "agents": {},
        "comparisons": {},
    }
    for agent, agent_rows in grouped.items():
        n = len(agent_rows)
        scored_rows = [row for row in agent_rows if row["score_eligible"]]
        scored_n = len(scored_rows)
        first_pass = sum(row["first_status"] == "PASS" for row in scored_rows)
        final_pass = sum(row["final_status"] == "PASS" for row in scored_rows)
        repair_candidates = [row for row in scored_rows if row["first_status"] == "FAIL"]
        repair_success = sum(row["repair_success"] for row in repair_candidates)
        correction_triggered_rows = [row for row in scored_rows if row["correction_triggered"]]
        correction_success = sum(row["correction_success"] for row in correction_triggered_rows)
        silent_or_metric_rows = [row for row in scored_rows if row["silent_or_metric_error_detected"]]
        visual_rows = [row for row in scored_rows if row["requires_visual_check"]]
        step_branch_rows = [row for row in scored_rows if row["step_branch_triggered"]]
        step_manifest_rows = [row for row in scored_rows if row["step_manifest_available"]]
        first_step_manifest_rows = [row for row in scored_rows if row["first_step_manifest_available"]]
        inferred_branch_rows = [row for row in scored_rows if row["step_branch_inferred_from_final_signal"]]
        anti_regression_rows = [row for row in scored_rows if row["anti_regression_used"]]
        token_usage = _sum_row_tokens(scored_rows, prefix="")
        repair_token_usage = _sum_row_tokens(scored_rows, prefix="repair_")
        first_attempt_token_usage = _sum_row_tokens(scored_rows, prefix="first_attempt_")
        summary["agents"][agent] = {
            "tasks": n,
            "scored_tasks": scored_n,
            "invalid_benchmark_task_count": sum(row["invalid_benchmark_task"] for row in agent_rows),
            "manual_review_required_count": sum(row["manual_review_required"] for row in agent_rows),
            "first_pass_count": first_pass,
            "final_pass_count": final_pass,
            "first_pass_rate": first_pass / scored_n if scored_n else 0,
            "final_pass_rate": final_pass / scored_n if scored_n else 0,
            "repair_success_rate": repair_success / len(repair_candidates) if repair_candidates else 0,
            "correction_triggered_count": len(correction_triggered_rows),
            "correction_success_count": correction_success,
            "conditional_correction_rate": correction_success / len(correction_triggered_rows) if correction_triggered_rows else 0,
            "end_to_end_correction_rate": correction_success / scored_n if scored_n else 0,
            "step_branch_trigger_count": len(step_branch_rows),
            "step_manifest_coverage": len(step_manifest_rows) / n if n else 0,
            "first_attempt_step_manifest_coverage": len(first_step_manifest_rows) / n if n else 0,
            "step_branch_inferred_from_final_signal_count": len(inferred_branch_rows),
            "anti_regression_used_count": len(anti_regression_rows),
            "anti_regression_switch_count": sum(row["anti_regression_switch_count"] for row in scored_rows),
            "silent_or_metric_error_detection_count": len(silent_or_metric_rows),
            "silent_or_visual_error_detection_count": len(silent_or_metric_rows),
            "visual_check_required_count": len(visual_rows),
            "average_attempts": sum(row["attempts"] for row in scored_rows) / scored_n if scored_n else 0,
            "token_usage": token_usage,
            "repair_token_usage": repair_token_usage,
            "first_attempt_token_usage": first_attempt_token_usage,
            "average_total_tokens": token_usage["total_tokens"] / scored_n if scored_n else 0,
            "average_repair_tokens": repair_token_usage["total_tokens"] / scored_n if scored_n else 0,
        }
    summary["comparisons"] = _comparison_metrics(summary["agents"])
    return summary


def _trace_token_usage(trace: AgentRunTrace) -> dict[str, int]:
    runtime_usage = trace.runtime.get("token_usage", {}) if isinstance(trace.runtime, dict) else {}
    normalized_runtime_usage = _normalize_token_usage(runtime_usage)
    if normalized_runtime_usage["total_tokens"]:
        return normalized_runtime_usage
    total = _zero_token_usage()
    for attempt in trace.attempts:
        _add_token_usage(total, attempt.token_usage)
    return total


def _repair_token_usage(trace: AgentRunTrace) -> dict[str, int]:
    total = _zero_token_usage()
    for attempt in trace.attempts:
        if attempt.attempt_index > 0:
            _add_token_usage(total, attempt.token_usage)
    return total


def _sum_row_tokens(rows: list[dict[str, Any]], *, prefix: str) -> dict[str, int]:
    return {
        "prompt_tokens": sum(_token_int(row.get(f"{prefix}prompt_tokens")) for row in rows),
        "completion_tokens": sum(_token_int(row.get(f"{prefix}completion_tokens")) for row in rows),
        "total_tokens": sum(_token_int(row.get(f"{prefix}total_tokens")) for row in rows),
    }


def _zero_token_usage() -> dict[str, int]:
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _normalize_token_usage(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return _zero_token_usage()
    return {
        "prompt_tokens": _token_int(value.get("prompt_tokens")),
        "completion_tokens": _token_int(value.get("completion_tokens")),
        "total_tokens": _token_int(value.get("total_tokens")),
    }


def _add_token_usage(target: dict[str, int], usage: dict[str, Any] | None) -> None:
    normalized = _normalize_token_usage(usage)
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        target[key] += normalized[key]


def _token_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    try:
        return max(0, int(str(value)))
    except (TypeError, ValueError):
        return 0


def _comparison_metrics(agents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = agents.get("baseline_multi_agent", {})
    self_debug = agents.get("self_debug_multi_agent", {})
    error_aware = agents.get("error_aware_multi_agent", {})
    comparisons: dict[str, Any] = {}
    if self_debug and error_aware:
        comparisons["error_aware_vs_self_debug_delta"] = {
            "final_pass_rate_delta": error_aware["final_pass_rate"] - self_debug["final_pass_rate"],
            "repair_success_rate_delta": error_aware["repair_success_rate"] - self_debug["repair_success_rate"],
            "conditional_correction_rate_delta": (
                error_aware["conditional_correction_rate"] - self_debug["conditional_correction_rate"]
            ),
            "end_to_end_correction_rate_delta": (
                error_aware["end_to_end_correction_rate"] - self_debug["end_to_end_correction_rate"]
            ),
            "average_attempts_delta": error_aware["average_attempts"] - self_debug["average_attempts"],
            "total_tokens_delta": (
                error_aware.get("token_usage", {}).get("total_tokens", 0)
                - self_debug.get("token_usage", {}).get("total_tokens", 0)
            ),
            "repair_tokens_delta": (
                error_aware.get("repair_token_usage", {}).get("total_tokens", 0)
                - self_debug.get("repair_token_usage", {}).get("total_tokens", 0)
            ),
            "average_total_tokens_delta": (
                error_aware.get("average_total_tokens", 0) - self_debug.get("average_total_tokens", 0)
            ),
        }
    if baseline and error_aware:
        comparisons["error_aware_vs_baseline_delta"] = {
            "final_pass_rate_delta": error_aware["final_pass_rate"] - baseline["final_pass_rate"],
            "first_pass_rate_delta": error_aware["first_pass_rate"] - baseline["first_pass_rate"],
        }
    if baseline and self_debug:
        comparisons["self_debug_vs_baseline_delta"] = {
            "final_pass_rate_delta": self_debug["final_pass_rate"] - baseline["final_pass_rate"],
            "first_pass_rate_delta": self_debug["first_pass_rate"] - baseline["first_pass_rate"],
        }
    return comparisons


def _has_step_manifest(step_report: dict[str, Any] | None) -> bool:
    if not isinstance(step_report, dict):
        return False
    status = str(step_report.get("status", "")).lower()
    steps = step_report.get("steps", [])
    return status not in {"", "missing", "invalid"} and isinstance(steps, list) and bool(steps)


def _summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Comparison Summary",
        "",
        f"- Auto task count: {summary.get('auto_task_count', 0)}",
        f"- Valid auto task count: {summary.get('valid_auto_task_count', 0) or summary.get('executed_task_count', 0)}",
        f"- Known invalid benchmark tasks: {summary.get('invalid_benchmark_task_count', 0)}",
        f"- Executed task count: {summary.get('executed_task_count', 0)}",
        f"- Skipped manual/hybrid review tasks: {summary.get('skipped_manual_review_count', 0)}",
        f"- Skipped invalid benchmark tasks: {summary.get('skipped_invalid_benchmark_task_count', 0)}",
        "",
        "| Agent | Tasks | Scored | Invalid | First-pass | Final-pass | Conditional correction | End-to-end correction | Step manifest | Avg attempts | Total tokens | Repair tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for agent, metrics in summary.get("agents", {}).items():
        token_usage = metrics.get("token_usage", {})
        repair_token_usage = metrics.get("repair_token_usage", {})
        lines.append(
            "| {agent} | {tasks} | {scored} | {invalid} | {first:.2%} | {final:.2%} | {conditional:.2%} | {e2e:.2%} | {manifest:.2%} | {attempts:.2f} | {tokens} | {repair_tokens} |".format(
                agent=agent,
                tasks=metrics["tasks"],
                scored=metrics.get("scored_tasks", metrics["tasks"]),
                invalid=metrics.get("invalid_benchmark_task_count", 0),
                first=metrics["first_pass_rate"],
                final=metrics["final_pass_rate"],
                conditional=metrics["conditional_correction_rate"],
                e2e=metrics["end_to_end_correction_rate"],
                manifest=metrics.get("step_manifest_coverage", 0),
                attempts=metrics["average_attempts"],
                tokens=int(token_usage.get("total_tokens", 0) or 0),
                repair_tokens=int(repair_token_usage.get("total_tokens", 0) or 0),
            )
        )
    lines.append("")
    lines.append("Main comparison: error_aware_multi_agent vs self_debug_multi_agent.")
    main_delta = summary.get("comparisons", {}).get("error_aware_vs_self_debug_delta")
    if main_delta:
        lines.append(
            "- Final-pass delta: {delta:.2%}".format(
                delta=main_delta.get("final_pass_rate_delta", 0),
            )
        )
        lines.append(
            "- Conditional-correction delta: {delta:.2%}".format(
                delta=main_delta.get("conditional_correction_rate_delta", 0),
            )
        )
        lines.append(
            "- End-to-end-correction delta: {delta:.2%}".format(
                delta=main_delta.get("end_to_end_correction_rate_delta", 0),
            )
        )
    return "\n".join(lines) + "\n"
