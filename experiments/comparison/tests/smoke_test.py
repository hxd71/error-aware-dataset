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
from experiments.comparison.host_runtime.executors import (
    CodeGenerationResult,
    MockExecutorBackend,
    _prepare_execution_env,
    _validate_llm_code,
)
from experiments.comparison.host_runtime.multi_agent import ExecutedAttempt, MultiAgentHost, _attempt_rank
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
    assert "auto_task_count" in summary
    assert "skipped_manual_review_count" in summary
    assert "error_aware_vs_self_debug_delta" in summary["comparisons"]
    assert summary["agents"]["error_aware_multi_agent"]["silent_or_metric_error_detection_count"] > 0
    assert "visual_check_required_count" in summary["agents"]["error_aware_multi_agent"]
    assert "conditional_correction_rate" in summary["agents"]["error_aware_multi_agent"]
    assert "end_to_end_correction_rate" in summary["agents"]["error_aware_multi_agent"]
    assert "step_branch_trigger_count" in summary["agents"]["error_aware_multi_agent"]
    assert "step_manifest_coverage" in summary["agents"]["error_aware_multi_agent"]
    assert "first_attempt_step_manifest_coverage" in summary["agents"]["error_aware_multi_agent"]
    assert "step_branch_inferred_from_final_signal_count" in summary["agents"]["error_aware_multi_agent"]

    baseline_and_self = [trace for trace in traces if trace.agent_kind != "error_aware_multi_agent"]
    for trace in baseline_and_self:
        text = json.dumps(trace.to_dict(), ensure_ascii=False)
        assert "knowledge_base" not in text
        assert "rule_cards.json" not in text
        assert "retrieved_cases" not in text

    error_aware = [trace for trace in traces if trace.agent_kind == "error_aware_multi_agent"]
    assert any("retrieved_cases" in json.dumps(trace.to_dict(), ensure_ascii=False) for trace in error_aware)
    error_aware_repairs = [
        attempt.repair_instruction
        for trace in error_aware
        for attempt in trace.attempts
        if attempt.repair_instruction
    ]
    assert any("agent_visible_report" in repair for repair in error_aware_repairs)
    assert any("retrieved_cases" in repair for repair in error_aware_repairs)
    assert any("repair_advice" in repair for repair in error_aware_repairs)
    assert any("step_branch_plan" in repair for repair in error_aware_repairs)
    assert any("step_evaluation" in repair for repair in error_aware_repairs)
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
    _assert_llm_safety_validation_is_precise()
    _assert_gis_runtime_env_sanitizes_proj()
    _assert_best_attempt_ranking_penalizes_missing_output_regression()
    _assert_generation_failure_does_not_abort_batch(tasks[0], evaluator, run_dir)
    _assert_shared_initial_attempt_is_identical_across_groups(tasks[1], evaluator, run_dir)
    _assert_token_usage_is_reported(tasks[0], evaluator, run_dir)
    print("smoke ok: framework runs, isolation holds, mock leakage audit is clean")


class FailingGenerateExecutor(MockExecutorBackend):
    def generate_code(self, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("synthetic safety validation failure")


class TokenGenerateExecutor(MockExecutorBackend):
    def generate_code_with_usage(self, **kwargs):  # type: ignore[no-untyped-def]
        code = super().generate_code(**kwargs)
        attempt_index = int(kwargs.get("attempt_index", 0))
        return CodeGenerationResult(
            code=code,
            token_usage={
                "prompt_tokens": 100 + attempt_index,
                "completion_tokens": 20 + attempt_index,
                "total_tokens": 120 + 2 * attempt_index,
            },
        )


def _assert_generation_failure_does_not_abort_batch(task, evaluator, run_dir) -> None:  # type: ignore[no-untyped-def]
    failing_host = MultiAgentHost(
        REPO_ROOT,
        "baseline_multi_agent",
        evaluator,
        max_repair_attempts=0,
        executor_backend=FailingGenerateExecutor(),
    )
    trace = failing_host.run_task(task, run_dir / "generation_failure_probe")
    assert trace.final_status == "FAIL"
    assert trace.attempts
    assert "Code generation failed before execution" in trace.attempts[0].execution_log


def _assert_shared_initial_attempt_is_identical_across_groups(task, evaluator, run_dir) -> None:  # type: ignore[no-untyped-def]
    shared_run_dir = run_dir / "shared_initial_probe"
    initial_host = MultiAgentHost(
        REPO_ROOT,
        "baseline_multi_agent",
        evaluator,
        max_repair_attempts=0,
    )
    shared_initial = initial_host.run_shared_initial_attempt(task, shared_run_dir)
    traces = []
    for agent_kind in ["baseline_multi_agent", "self_debug_multi_agent", "error_aware_multi_agent"]:
        host = MultiAgentHost(REPO_ROOT, agent_kind, evaluator, max_repair_attempts=2)
        traces.append(host.run_task(task, shared_run_dir, shared_initial))

    first_code_paths = {trace.attempts[0].generated_code_path for trace in traces}
    first_output_paths = {trace.attempts[0].output_path for trace in traces}
    first_statuses = {
        trace.attempts[0].evaluation["agent_visible_report"]["status"]
        for trace in traces
    }
    assert first_code_paths == {shared_initial.generated_code_path}
    assert first_output_paths == {shared_initial.output_path}
    assert first_statuses == {shared_initial.visible_report["status"]}
    assert traces[0].agent_kind == "baseline_multi_agent"
    assert len(traces[0].attempts) == 1
    assert traces[1].attempts[0].repair_instruction["mode"] == "self_debug_repair"
    assert traces[2].attempts[0].repair_instruction["mode"] == "error_aware_repair"
    assert traces[2].attempts[0].repair_instruction["step_branch_plan"]["mode"] == "step_branch_repair"
    assert traces[2].attempts[0].step_evaluation["status"] in {"reported", "missing"}


def _assert_token_usage_is_reported(task, evaluator, run_dir) -> None:  # type: ignore[no-untyped-def]
    token_run_dir = run_dir / "token_usage_probe"
    host = MultiAgentHost(
        REPO_ROOT,
        "baseline_multi_agent",
        evaluator,
        max_repair_attempts=0,
        executor_backend=TokenGenerateExecutor(),
    )
    trace = host.run_task(task, token_run_dir)
    assert trace.attempts[0].token_usage["total_tokens"] == 120
    summary = write_reports([trace], token_run_dir / "reports")
    metrics = summary["agents"]["baseline_multi_agent"]
    assert metrics["token_usage"]["prompt_tokens"] == 100
    assert metrics["token_usage"]["completion_tokens"] == 20
    assert metrics["token_usage"]["total_tokens"] == 120
    assert metrics["average_total_tokens"] == 120


def _assert_llm_safety_validation_is_precise() -> None:
    _validate_llm_code(
        "\n".join(
            [
                "import ast",
                "def main():",
                "    value = ast.literal_eval(\"{'highway': 'residential'}\")",
                "    return value",
            ]
        )
    )
    for code in [
        "eval('1 + 1')",
        "import subprocess\nsubprocess.run(['echo', 'x'])",
        "import os\nos.environ['PROJ_LIB'] = 'bad-path'",
    ]:
        try:
            _validate_llm_code(code)
        except RuntimeError:
            continue
        raise AssertionError(f"unsafe generated code was not rejected: {code}")


def _assert_gis_runtime_env_sanitizes_proj() -> None:
    geoagent_python = REPO_ROOT.parent / ".venv" / "Scripts" / "python.exe"
    python_executable = str(geoagent_python if geoagent_python.is_file() else Path(sys.executable))
    env = _prepare_execution_env(python_executable)
    assert "PROJ_LIB" not in env or "PostgreSQL" not in env.get("PROJ_LIB", "")


def _assert_best_attempt_ranking_penalizes_missing_output_regression() -> None:
    partial_metric_failure = ExecutedAttempt(
        attempt_index=1,
        generated_code_path="task/agent/attempt_01/generated_code.py",
        output_path="task/agent/attempt_01/outputs",
        generated_code="",
        execution_log="returncode=0",
        visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "metrics_diff": {"score": 0.25, "failed_check_count": 5, "failed_checks": ["a", "b", "c", "d", "e"]},
        },
        scoring_report={},
        step_report={"status": "reported", "steps": [{"step_id": "analysis", "status": "completed"}]},
        token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    missing_output_regression = ExecutedAttempt(
        attempt_index=2,
        generated_code_path="task/agent/attempt_02/generated_code.py",
        output_path="task/agent/attempt_02/outputs",
        generated_code="",
        execution_log="Code generation failed before execution: Generated code failed safety validation: ['unsupported_api:union_all']",
        visible_report={
            "status": "FAIL",
            "failure_kind": "missing_output",
            "metrics_diff": {"score": 0.0, "failed_check_count": 1, "failed_checks": ["expected_output_exists"]},
        },
        scoring_report={},
        step_report={"status": "missing", "steps": []},
        token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    assert _attempt_rank(partial_metric_failure) > _attempt_rank(missing_output_regression)


if __name__ == "__main__":
    main()
