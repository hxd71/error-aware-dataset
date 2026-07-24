from __future__ import annotations

import json
import platform
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from experiments.comparison.adapters.evaluator import EvaluatorAdapter
from experiments.comparison.host_runtime.executors import CodeGenerationError, ExecutorBackend, MockExecutorBackend
from experiments.comparison.host_runtime.models import (
    AgentKind,
    AgentRunTrace,
    AttemptTrace,
    BenchmarkTask,
    ensure_dir,
)
from experiments.comparison.plugins.error_aware import ErrorAwarePlugin


@dataclass(frozen=True)
class ExecutedAttempt:
    attempt_index: int
    generated_code_path: str
    output_path: str
    generated_code: str
    execution_log: str
    visible_report: dict[str, Any]
    scoring_report: dict[str, Any]
    step_report: dict[str, Any]
    token_usage: dict[str, int]


class MultiAgentHost:
    """Shared host workflow for all comparison groups.

    The host simulates Planner, Executor, Verifier, Repairer, and Reporter boundaries.
    Real LLM calls can replace the deterministic methods while preserving the trace
    and adapter contracts.
    """

    def __init__(
        self,
        repo_root: Path,
        agent_kind: AgentKind,
        evaluator: EvaluatorAdapter,
        max_repair_attempts: int = 2,
        model_config: dict[str, Any] | None = None,
        executor_backend: ExecutorBackend | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.agent_kind = agent_kind
        self.evaluator = evaluator
        self.max_repair_attempts = 0 if agent_kind == "baseline_multi_agent" else max_repair_attempts
        self.model_config = model_config or {"provider": "mock", "model": "mock-deterministic", "temperature": 0}
        self.executor_backend = executor_backend or MockExecutorBackend()
        self.error_aware_plugin = (
            ErrorAwarePlugin(repo_root=repo_root) if agent_kind == "error_aware_multi_agent" else None
        )

    def run_shared_initial_attempt(self, task: BenchmarkTask, run_dir: Path) -> ExecutedAttempt:
        task_dir = ensure_dir(run_dir / task.task_id / "shared_initial")
        attempt_dir = ensure_dir(task_dir / "attempt_00")
        executed = self._execute_attempt(
            task=task,
            run_dir=run_dir,
            attempt_dir=attempt_dir,
            attempt_index=0,
            generation_agent_kind="baseline_multi_agent",
            evaluator_agent_kind="baseline_multi_agent",
            repair_instruction=None,
            previous_code="",
            previous_execution_log="",
        )
        (task_dir / "shared_initial_attempt.json").write_text(
            json.dumps(
                {
                    "schema_version": "0.1.0",
                    "task_id": task.task_id,
                    "attempt_index": 0,
                    "generated_code_path": executed.generated_code_path,
                    "output_path": executed.output_path,
                    "evaluation": {"agent_visible_report": executed.visible_report},
                    "scoring_report": executed.scoring_report,
                    "step_report": executed.step_report,
                    "token_usage": executed.token_usage,
                    "generation_agent_kind": "baseline_multi_agent",
                    "role_boundary": "shared_neutral_initial_attempt",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return executed

    def run_task(
        self,
        task: BenchmarkTask,
        run_dir: Path,
        shared_initial_attempt: ExecutedAttempt | None = None,
    ) -> AgentRunTrace:
        task_dir = ensure_dir(run_dir / task.task_id / self.agent_kind)
        trace = AgentRunTrace(
            task=task.agent_view(),
            agent_kind=self.agent_kind,
            max_repair_attempts=self.max_repair_attempts,
            runtime={
                "python": platform.python_version(),
                "platform": platform.platform(),
                "model_config": self.model_config,
                "evaluator": {
                    "name": self.evaluator.evaluator_name,
                    "version": self.evaluator.evaluator_version,
                },
                "executor": {
                    "name": self.executor_backend.backend_name,
                    "version": self.executor_backend.backend_version,
                },
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "shared_initial_attempt": bool(shared_initial_attempt),
            },
        )
        trace.runtime["anti_regression"] = {
            "enabled": self.max_repair_attempts > 0,
            "best_source_switch_count": 0,
            "best_source_attempt_index": None,
        }

        repair_instruction: dict[str, Any] | None = None
        scoring_report: dict[str, Any] = {}
        previous_code = ""
        previous_execution_log = ""
        previous_step_report: dict[str, Any] = {}
        previous_output_path: Path | None = None
        best_attempt: ExecutedAttempt | None = None
        anti_regression_switch_count = 0
        start_attempt_index = 0
        if shared_initial_attempt is not None:
            visible_report = shared_initial_attempt.visible_report
            scoring_report = shared_initial_attempt.scoring_report
            previous_code = shared_initial_attempt.generated_code
            previous_execution_log = shared_initial_attempt.execution_log
            previous_step_report = shared_initial_attempt.step_report
            previous_output_path = run_dir / shared_initial_attempt.output_path
            best_attempt = shared_initial_attempt
            trace.runtime["anti_regression"]["best_source_attempt_index"] = best_attempt.attempt_index
            plugin_diagnosis, next_repair_instruction = self._next_repair_instruction(
                task=task,
                generated_code=previous_code,
                execution_log=previous_execution_log,
                visible_report=visible_report,
                step_report=previous_step_report,
                attempt_index=0,
            )
            trace.attempts.append(
                AttemptTrace(
                    attempt_index=0,
                    generated_code_path=shared_initial_attempt.generated_code_path,
                    output_path=shared_initial_attempt.output_path,
                    execution_log=shared_initial_attempt.execution_log,
                    evaluation={"agent_visible_report": visible_report},
                    token_usage=shared_initial_attempt.token_usage,
                    step_evaluation=previous_step_report,
                    repair_instruction=next_repair_instruction,
                    plugin_diagnosis=plugin_diagnosis,
                )
            )
            _add_token_usage(trace.runtime["token_usage"], shared_initial_attempt.token_usage)
            if visible_report["status"] == "PASS":
                trace.final_status = "PASS"
                trace.scoring_report = scoring_report
                self._write_trace(trace, task_dir)
                return trace
            repair_instruction = next_repair_instruction
            if repair_instruction is None:
                trace.final_status = "FAIL"
                trace.scoring_report = scoring_report
                self._write_trace(trace, task_dir)
                return trace
            start_attempt_index = 1

        for attempt_index in range(start_attempt_index, self.max_repair_attempts + 1):
            attempt_dir = ensure_dir(task_dir / f"attempt_{attempt_index:02d}")
            executed = self._execute_attempt(
                task=task,
                run_dir=run_dir,
                attempt_dir=attempt_dir,
                attempt_index=attempt_index,
                generation_agent_kind=self.agent_kind,
                evaluator_agent_kind=self.agent_kind,
                repair_instruction=repair_instruction,
                previous_code=previous_code,
                previous_execution_log=previous_execution_log,
                previous_output_path=previous_output_path,
            )
            scoring_report = executed.scoring_report
            visible_report = executed.visible_report
            if best_attempt is None or _attempt_rank(executed) > _attempt_rank(best_attempt):
                best_attempt = executed
                trace.runtime["anti_regression"]["best_source_attempt_index"] = best_attempt.attempt_index
            plugin_diagnosis, next_repair_instruction = self._next_repair_instruction(
                task=task,
                generated_code=executed.generated_code,
                execution_log=executed.execution_log,
                visible_report=visible_report,
                step_report=executed.step_report,
                attempt_index=attempt_index,
            )

            trace.attempts.append(
                AttemptTrace(
                    attempt_index=attempt_index,
                    generated_code_path=executed.generated_code_path,
                    output_path=executed.output_path,
                    execution_log=executed.execution_log,
                    evaluation={"agent_visible_report": visible_report},
                    token_usage=executed.token_usage,
                    step_evaluation=executed.step_report,
                    repair_instruction=next_repair_instruction,
                    plugin_diagnosis=plugin_diagnosis,
                )
            )
            _add_token_usage(trace.runtime["token_usage"], executed.token_usage)

            if visible_report["status"] == "PASS":
                trace.final_status = "PASS"
                break
            repair_instruction = next_repair_instruction
            if repair_instruction is None:
                trace.final_status = "FAIL"
                break
            repair_source = best_attempt or executed
            if repair_source.attempt_index != executed.attempt_index:
                anti_regression_switch_count += 1
                repair_instruction = dict(repair_instruction)
                repair_instruction["anti_regression"] = {
                    "enabled": True,
                    "source_attempt_index": repair_source.attempt_index,
                    "last_attempt_index": executed.attempt_index,
                    "source_rank": _attempt_rank(repair_source),
                    "last_rank": _attempt_rank(executed),
                    "reason": (
                        "Continue repair from the best prior attempt because the latest attempt "
                        "regressed in evaluator score, failed-check count, missing-output/API status, or execution stability."
                    ),
                }
            previous_code = repair_source.generated_code
            previous_execution_log = repair_source.execution_log
            previous_step_report = repair_source.step_report
            previous_output_path = run_dir / repair_source.output_path
            trace.runtime["anti_regression"]["best_source_switch_count"] = anti_regression_switch_count
            trace.runtime["anti_regression"]["best_source_attempt_index"] = (
                best_attempt.attempt_index if best_attempt is not None else None
            )

        trace.scoring_report = scoring_report
        self._write_trace(trace, task_dir)
        return trace

    def _execute_attempt(
        self,
        *,
        task: BenchmarkTask,
        run_dir: Path,
        attempt_dir: Path,
        attempt_index: int,
        generation_agent_kind: AgentKind,
        evaluator_agent_kind: AgentKind,
        repair_instruction: dict[str, Any] | None,
        previous_code: str,
        previous_execution_log: str,
        previous_output_path: Path | None = None,
    ) -> ExecutedAttempt:
        generation_error = ""
        token_usage = _zero_token_usage()
        try:
            generation = self.executor_backend.generate_code_with_usage(
                task=task,
                agent_kind=generation_agent_kind,
                attempt_index=attempt_index,
                repair_instruction=repair_instruction,
                previous_code=previous_code,
                previous_execution_log=previous_execution_log,
            )
            generated_code = generation.code
            token_usage = generation.token_usage
        except CodeGenerationError as exc:
            generation_error = f"Code generation failed before execution: {exc}"
            token_usage = exc.token_usage
            generated_code = "\n".join(
                [
                    "# Code generation failed; this placeholder lets the evaluator report missing outputs.",
                    f"GENERATION_ERROR = {generation_error!r}",
                    "def main():",
                    "    raise RuntimeError(GENERATION_ERROR)",
                    "",
                    "if __name__ == '__main__':",
                    "    main()",
                    "",
                ]
            )
        except Exception as exc:
            generation_error = f"Code generation failed before execution: {exc}"
            generated_code = "\n".join(
                [
                    "# Code generation failed; this placeholder lets the evaluator report missing outputs.",
                    f"GENERATION_ERROR = {generation_error!r}",
                    "def main():",
                    "    raise RuntimeError(GENERATION_ERROR)",
                    "",
                    "if __name__ == '__main__':",
                    "    main()",
                    "",
                ]
            )
        code_path = attempt_dir / "generated_code.py"
        code_path.write_text(generated_code, encoding="utf-8")

        output_path = attempt_dir / "outputs"
        _reset_child_dir(attempt_dir, output_path)
        execution = self.executor_backend.run_code(
            code_path=code_path,
            output_path=output_path,
            task=task,
            repair_instruction=repair_instruction,
            previous_output_path=previous_output_path,
        )
        execution_log = execution.to_log()
        if generation_error:
            execution_log = generation_error + "\n" + execution_log
        (attempt_dir / "execution.log").write_text(execution_log, encoding="utf-8")

        evaluation = self.evaluator.evaluate(
            task=task,
            agent_kind=evaluator_agent_kind,
            attempt_index=attempt_index,
            output_path=output_path,
            repair_mode=repair_instruction.get("mode", "none") if repair_instruction else "none",
        )
        return ExecutedAttempt(
            attempt_index=attempt_index,
            generated_code_path=code_path.relative_to(run_dir).as_posix(),
            output_path=output_path.relative_to(run_dir).as_posix(),
            generated_code=generated_code,
            execution_log=execution_log,
            visible_report=asdict(evaluation.agent_visible_report),
            scoring_report=asdict(evaluation.scoring_report),
            step_report=_read_step_report(output_path),
            token_usage=token_usage,
        )

    def _next_repair_instruction(
        self,
        *,
        task: BenchmarkTask,
        generated_code: str,
        execution_log: str,
        visible_report: dict[str, Any],
        step_report: dict[str, Any],
        attempt_index: int,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        plugin_diagnosis = None
        next_repair_instruction = None
        non_repairable_kinds = {
            "manual_review_required",
            "evaluator_configuration_error",
            "evaluator_dataset_issue",
        }
        if (
            visible_report["status"] == "FAIL"
            and attempt_index < self.max_repair_attempts
            and visible_report.get("failure_kind", "") not in non_repairable_kinds
        ):
            if self.agent_kind == "self_debug_multi_agent":
                next_repair_instruction = self._self_debug_repair(visible_report)
            elif self.agent_kind == "error_aware_multi_agent" and self.error_aware_plugin is not None:
                plugin_diagnosis = self.error_aware_plugin.diagnose_and_advise(
                    task_view=task.agent_view(),
                    generated_code=generated_code,
                    execution_log=execution_log,
                    agent_visible_report=visible_report,
                    step_report=step_report,
                )
                next_repair_instruction = {
                    "mode": "error_aware_repair",
                    "agent_visible_report": visible_report,
                    "step_evaluation": step_report,
                    "candidate_labels": plugin_diagnosis.get("candidate_labels", []),
                    "classification_basis": plugin_diagnosis.get("classification_basis", {}),
                    "step_branch_plan": plugin_diagnosis.get("step_branch_plan", {}),
                    "retrieved_cases": plugin_diagnosis.get("retrieved_cases", []),
                    "repair_advice": plugin_diagnosis.get("repair_advice", {}),
                }
        return plugin_diagnosis, next_repair_instruction

    @staticmethod
    def _write_trace(trace: AgentRunTrace, task_dir: Path) -> None:
        trace_path = task_dir / "trace.json"
        trace_path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _self_debug_repair(visible_report: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": "self_debug_repair",
            "agent_visible_report": visible_report,
            "instruction": {
                "repair_instruction": "Revise code using traceback, execution log, and visible evaluator failure only.",
                "failure_kind": visible_report.get("failure_kind", ""),
                "failure_reasons": visible_report.get("failure_reasons", []),
                "metrics_diff": visible_report.get("metrics_diff", {}),
            },
        }


def _attempt_rank(attempt: ExecutedAttempt) -> tuple[int, float, int, int, int, int]:
    """Rank visible attempt quality without looking at private gold/reference artifacts."""
    visible = attempt.visible_report if isinstance(attempt.visible_report, dict) else {}
    status_score = 1 if visible.get("status") == "PASS" else 0
    score = _visible_attempt_score(attempt)
    metrics = visible.get("metrics_diff", {})
    failed_count = 999
    if isinstance(metrics, dict):
        raw_failed_count = metrics.get("failed_check_count")
        if isinstance(raw_failed_count, int):
            failed_count = raw_failed_count
        elif isinstance(metrics.get("failed_checks"), list):
            failed_count = len(metrics["failed_checks"])
    failure_kind = str(visible.get("failure_kind", "")).lower()
    missing_penalty = -2 if failure_kind == "missing_output" else 0
    traceback_penalty = -1 if failure_kind == "traceback_error" else 0
    execution_penalty = -1 if _looks_like_generation_or_api_failure(attempt.execution_log) else 0
    return (
        status_score,
        score,
        missing_penalty,
        traceback_penalty + execution_penalty,
        -failed_count,
        attempt.attempt_index,
    )


def _visible_attempt_score(attempt: ExecutedAttempt) -> float:
    visible = attempt.visible_report if isinstance(attempt.visible_report, dict) else {}
    metrics = visible.get("metrics_diff", {})
    if isinstance(metrics, dict):
        score = _as_float(metrics.get("score"))
        if score is not None:
            return score
    scoring = attempt.scoring_report if isinstance(attempt.scoring_report, dict) else {}
    details = scoring.get("details", {})
    if isinstance(details, dict):
        raw_report = details.get("raw_report", {})
        if isinstance(raw_report, dict):
            score = _as_float(raw_report.get("score"))
            if score is not None:
                return score
    return 1.0 if visible.get("status") == "PASS" else 0.0


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _looks_like_generation_or_api_failure(execution_log: str) -> bool:
    lowered = execution_log.lower()
    return any(
        token in lowered
        for token in [
            "code generation failed before execution",
            "generated code failed safety validation",
            "unsupported_api",
            "modulenotfounderror",
            "importerror",
            "attributeerror",
        ]
    )


def _zero_token_usage() -> dict[str, int]:
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _add_token_usage(target: dict[str, Any], usage: dict[str, Any] | None) -> None:
    if not isinstance(usage, dict):
        return
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        target[key] = int(target.get(key, 0) or 0) + _token_int(usage.get(key))


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


def run_many(
    repo_root: Path,
    tasks: list[BenchmarkTask],
    agent_kinds: list[AgentKind],
    evaluator: EvaluatorAdapter,
    output_dir: Path,
    max_repair_attempts: int,
) -> list[AgentRunTrace]:
    started = int(time.time())
    run_dir = ensure_dir(output_dir / f"run_{started}")
    traces: list[AgentRunTrace] = []
    for agent_kind in agent_kinds:
        host = MultiAgentHost(
            repo_root=repo_root,
            agent_kind=agent_kind,
            evaluator=evaluator,
            max_repair_attempts=max_repair_attempts,
        )
        for task in tasks:
            traces.append(host.run_task(task, run_dir))
    return traces


def _reset_child_dir(parent: Path, child: Path) -> Path:
    parent_resolved = parent.resolve(strict=False)
    child_resolved = child.resolve(strict=False)
    if child_resolved.parent != parent_resolved:
        raise RuntimeError(f"Refusing to reset non-child output directory: {child}")
    if child.exists():
        shutil.rmtree(child)
    return ensure_dir(child)


def _read_step_report(output_path: Path) -> dict[str, Any]:
    manifest_path = output_path / "workflow_steps.json"
    if not manifest_path.is_file():
        return {
            "schema_version": "0.1.0",
            "status": "missing",
            "message": "workflow_steps.json was not produced by the generated workflow.",
            "steps": [],
        }
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "schema_version": "0.1.0",
            "status": "invalid",
            "message": f"workflow_steps.json could not be parsed: {exc}",
            "steps": [],
        }
    if isinstance(data, list):
        steps = [step for step in data if isinstance(step, dict)]
        return {
            "schema_version": "0.1.0",
            "status": "reported",
            "message": "workflow_steps.json used a list root; normalized to the standard object shape.",
            "steps": steps[:12],
        }
    if not isinstance(data, dict):
        return {
            "schema_version": "0.1.0",
            "status": "invalid",
            "message": "workflow_steps.json root value is not an object.",
            "steps": [],
        }
    steps = data.get("steps", [])
    if not isinstance(steps, list):
        steps = []
    return {
        "schema_version": str(data.get("schema_version", "0.1.0")),
        "status": str(data.get("status", "reported")),
        "message": str(data.get("message", "")),
        "steps": steps[:12],
    }
