from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.comparison.adapters.benchmark_loader import load_benchmark_tasks
from experiments.comparison.adapters.evaluator import MockEvaluator
from experiments.comparison.adapters.leakage_audit import audit_benchmark_leakage
from experiments.comparison.host_runtime.multi_agent import MultiAgentHost
from experiments.comparison.host_runtime.reporting import write_reports


def main() -> None:
    tasks = load_benchmark_tasks(REPO_ROOT / "experiments" / "comparison" / "mock" / "benchmark_tasks.json")
    evaluator = MockEvaluator()
    traces = []
    run_dir = REPO_ROOT / "experiments" / "comparison" / "runs" / "smoke_test_tmp"
    run_dir.mkdir(parents=True, exist_ok=True)
    for agent_kind in ["baseline_multi_agent", "self_debug_multi_agent", "error_aware_multi_agent"]:
        host = MultiAgentHost(REPO_ROOT, agent_kind, evaluator, max_repair_attempts=2)
        for task in tasks:
            traces.append(host.run_task(task, run_dir))
    summary = write_reports(traces, run_dir / "reports")
    assert set(summary["agents"]) == {
        "baseline_multi_agent",
        "self_debug_multi_agent",
        "error_aware_multi_agent",
    }

    baseline_and_self = [trace for trace in traces if trace.agent_kind != "error_aware_multi_agent"]
    for trace in baseline_and_self:
        text = json.dumps(trace.to_dict(), ensure_ascii=False)
        assert "knowledge_base" not in text
        assert "rule_cards.json" not in text
        assert "retrieved_cases" not in text

    error_aware = [trace for trace in traces if trace.agent_kind == "error_aware_multi_agent"]
    assert any("retrieved_cases" in json.dumps(trace.to_dict(), ensure_ascii=False) for trace in error_aware)
    assert all(
        "candidate_pool_used\": false" in json.dumps(trace.to_dict(), ensure_ascii=False)
        for trace in error_aware
        if any(attempt.plugin_diagnosis for attempt in trace.attempts)
    )

    leakage = audit_benchmark_leakage(
        REPO_ROOT,
        REPO_ROOT / "experiments" / "comparison" / "mock" / "benchmark_tasks.json",
    )
    assert leakage["leakage_risk_count"] == 0
    print("smoke ok: framework runs, isolation holds, mock leakage audit is clean")


if __name__ == "__main__":
    main()
