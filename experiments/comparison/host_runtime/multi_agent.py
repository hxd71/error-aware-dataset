from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from experiments.comparison.adapters.evaluator import EvaluatorAdapter
from experiments.comparison.host_runtime.models import (
    AgentKind,
    AgentRunTrace,
    AttemptTrace,
    BenchmarkTask,
    ensure_dir,
)
from experiments.comparison.plugins.error_aware import ErrorAwarePlugin


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
    ) -> None:
        self.repo_root = repo_root
        self.agent_kind = agent_kind
        self.evaluator = evaluator
        self.max_repair_attempts = 0 if agent_kind == "baseline_multi_agent" else max_repair_attempts
        self.model_config = model_config or {"provider": "mock", "model": "mock-deterministic", "temperature": 0}
        self.error_aware_plugin = (
            ErrorAwarePlugin(repo_root=repo_root) if agent_kind == "error_aware_multi_agent" else None
        )

    def run_task(self, task: BenchmarkTask, run_dir: Path) -> AgentRunTrace:
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
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            },
        )

        repair_instruction: dict[str, Any] | None = None
        scoring_report: dict[str, Any] = {}
        for attempt_index in range(self.max_repair_attempts + 1):
            attempt_dir = ensure_dir(task_dir / f"attempt_{attempt_index:02d}")
            generated_code = self._executor_generate_code(task, attempt_index, repair_instruction)
            code_path = attempt_dir / "generated_code.py"
            code_path.write_text(generated_code, encoding="utf-8")

            output_path = attempt_dir / "outputs"
            ensure_dir(output_path)
            (output_path / "result_stub.json").write_text(
                json.dumps(
                    {
                        "task_id": task.task_id,
                        "agent_kind": self.agent_kind,
                        "attempt_index": attempt_index,
                        "repair_mode": repair_instruction.get("mode", "none") if repair_instruction else "none",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            execution_log = self._executor_log(task, attempt_index, repair_instruction)
            (attempt_dir / "execution.log").write_text(execution_log, encoding="utf-8")

            evaluation = self.evaluator.evaluate(
                task=task,
                agent_kind=self.agent_kind,
                attempt_index=attempt_index,
                output_path=output_path,
                repair_mode=repair_instruction.get("mode", "none") if repair_instruction else "none",
            )
            visible_report = asdict(evaluation.agent_visible_report)
            scoring_report = asdict(evaluation.scoring_report)

            plugin_diagnosis = None
            next_repair_instruction = None
            if visible_report["status"] == "FAIL" and attempt_index < self.max_repair_attempts:
                if self.agent_kind == "self_debug_multi_agent":
                    next_repair_instruction = self._self_debug_repair(visible_report)
                elif self.agent_kind == "error_aware_multi_agent" and self.error_aware_plugin is not None:
                    plugin_diagnosis = self.error_aware_plugin.diagnose_and_advise(
                        task_view=task.agent_view(),
                        generated_code=generated_code,
                        execution_log=execution_log,
                        agent_visible_report=visible_report,
                    )
                    next_repair_instruction = {
                        "mode": "error_aware_repair",
                        "instruction": plugin_diagnosis["repair_advice"],
                    }

            trace.attempts.append(
                AttemptTrace(
                    attempt_index=attempt_index,
                    generated_code_path=code_path.relative_to(run_dir).as_posix(),
                    output_path=output_path.relative_to(run_dir).as_posix(),
                    execution_log=execution_log,
                    evaluation={"agent_visible_report": visible_report},
                    repair_instruction=next_repair_instruction,
                    plugin_diagnosis=plugin_diagnosis,
                )
            )

            if visible_report["status"] == "PASS":
                trace.final_status = "PASS"
                break
            repair_instruction = next_repair_instruction
            if repair_instruction is None:
                trace.final_status = "FAIL"
                break

        trace.scoring_report = scoring_report
        trace_path = task_dir / "trace.json"
        trace_path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return trace

    def _executor_generate_code(
        self,
        task: BenchmarkTask,
        attempt_index: int,
        repair_instruction: dict[str, Any] | None,
    ) -> str:
        repair_mode = repair_instruction.get("mode", "none") if repair_instruction else "none"
        return "\n".join(
            [
                "# Mock GIS workflow generated by the shared multi-agent host.",
                f"TASK_ID = {task.task_id!r}",
                f"AGENT_KIND = {self.agent_kind!r}",
                f"ATTEMPT_INDEX = {attempt_index!r}",
                f"REPAIR_MODE = {repair_mode!r}",
                "def main():",
                "    return {'status': 'mock-output'}",
                "",
                "if __name__ == '__main__':",
                "    main()",
                "",
            ]
        )

    def _executor_log(
        self,
        task: BenchmarkTask,
        attempt_index: int,
        repair_instruction: dict[str, Any] | None,
    ) -> str:
        if attempt_index == 0:
            reasons = task.mock_behavior.get("failure_reasons", [])
            return "Initial mock execution. " + " ".join(reasons)
        mode = repair_instruction.get("mode", "repair") if repair_instruction else "repair"
        return f"Mock repair execution using {mode}."

    @staticmethod
    def _self_debug_repair(visible_report: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": "self_debug_repair",
            "instruction": {
                "repair_instruction": "Revise code using traceback, execution log, and visible evaluator failure only.",
                "failure_kind": visible_report.get("failure_kind", ""),
                "failure_reasons": visible_report.get("failure_reasons", []),
                "metrics_diff": visible_report.get("metrics_diff", {}),
            },
        }


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
