from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


AgentKind = Literal["baseline_multi_agent", "self_debug_multi_agent", "error_aware_multi_agent"]
Status = Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    prompt: str
    input_paths: list[str]
    expected_outputs: list[str]
    complexity: str
    requires_visual_check: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    scoring: dict[str, Any] = field(default_factory=dict)
    mock_behavior: dict[str, Any] = field(default_factory=dict)

    def agent_view(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "input_paths": self.input_paths,
            "expected_outputs": self.expected_outputs,
            "complexity": self.complexity,
            "requires_visual_check": self.requires_visual_check,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AgentVisibleReport:
    status: Status
    failure_kind: str = ""
    failure_reasons: list[str] = field(default_factory=list)
    metrics_diff: dict[str, Any] = field(default_factory=dict)
    requires_visual_check: bool = False
    output_path: str = ""


@dataclass(frozen=True)
class ScoringReport:
    status: Status
    gold_labels: list[str] = field(default_factory=list)
    leakage_risk: bool = False
    notes: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationResult:
    agent_visible_report: AgentVisibleReport
    scoring_report: ScoringReport


@dataclass
class AttemptTrace:
    attempt_index: int
    generated_code_path: str
    output_path: str
    execution_log: str
    evaluation: dict[str, Any]
    token_usage: dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    step_evaluation: dict[str, Any] = field(default_factory=dict)
    repair_instruction: dict[str, Any] | None = None
    plugin_diagnosis: dict[str, Any] | None = None


@dataclass
class AgentRunTrace:
    task: dict[str, Any]
    agent_kind: AgentKind
    max_repair_attempts: int
    runtime: dict[str, Any]
    attempts: list[AttemptTrace] = field(default_factory=list)
    final_status: Status = "FAIL"
    scoring_report: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["attempts"] = [asdict(attempt) for attempt in self.attempts]
        return data


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
