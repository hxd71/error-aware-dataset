from __future__ import annotations

from pathlib import Path

from experiments.comparison.host_runtime.models import (
    AgentKind,
    AgentVisibleReport,
    BenchmarkTask,
    EvaluationResult,
    ScoringReport,
)


class EvaluatorAdapter:
    """Interface for Task 3's future GIS verifier."""

    evaluator_name = "abstract"
    evaluator_version = "0.0.0"

    def evaluate(
        self,
        task: BenchmarkTask,
        agent_kind: AgentKind,
        attempt_index: int,
        output_path: Path,
        repair_mode: str,
    ) -> EvaluationResult:
        raise NotImplementedError


class MockEvaluator(EvaluatorAdapter):
    """Deterministic evaluator used only to validate the comparison framework."""

    evaluator_name = "mock_gis_evaluator"
    evaluator_version = "0.1.0"

    def evaluate(
        self,
        task: BenchmarkTask,
        agent_kind: AgentKind,
        attempt_index: int,
        output_path: Path,
        repair_mode: str,
    ) -> EvaluationResult:
        behavior = task.mock_behavior
        initial_status = behavior.get("initial_status", "FAIL")
        status = "PASS" if initial_status == "PASS" and attempt_index == 0 else "FAIL"
        if attempt_index > 0:
            if agent_kind == "self_debug_multi_agent" and behavior.get("self_debug_can_fix", False):
                status = "PASS"
            if agent_kind == "error_aware_multi_agent" and behavior.get("error_aware_can_fix", False):
                status = "PASS"

        visible = AgentVisibleReport(
            status=status,
            failure_kind="" if status == "PASS" else behavior.get("failure_kind", "silent_logic_error"),
            failure_reasons=[] if status == "PASS" else list(behavior.get("failure_reasons", [])),
            metrics_diff={} if status == "PASS" else dict(behavior.get("metrics_diff", {})),
            requires_visual_check=bool(task.requires_visual_check and status == "FAIL"),
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status=status,
            gold_labels=list(task.scoring.get("gold_labels", [])),
            leakage_risk=bool(task.scoring.get("leakage_risk", False)),
            notes=str(task.scoring.get("notes", "")),
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)
