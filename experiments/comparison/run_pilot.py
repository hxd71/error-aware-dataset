from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.comparison.adapters.benchmark_loader import load_benchmark_tasks
from experiments.comparison.adapters.evaluator import MockEvaluator
from experiments.comparison.host_runtime.models import AgentKind, ensure_dir
from experiments.comparison.host_runtime.multi_agent import MultiAgentHost
from experiments.comparison.host_runtime.reporting import write_reports


AGENT_ALIASES: dict[str, list[AgentKind]] = {
    "baseline": ["baseline_multi_agent"],
    "self_debug": ["self_debug_multi_agent"],
    "error_aware": ["error_aware_multi_agent"],
    "all": ["baseline_multi_agent", "self_debug_multi_agent", "error_aware_multi_agent"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the GIS agent comparison pilot framework.")
    parser.add_argument(
        "--agent",
        choices=sorted(AGENT_ALIASES),
        default="all",
        help="Comparison group to run.",
    )
    parser.add_argument(
        "--tasks",
        type=Path,
        default=REPO_ROOT / "experiments" / "comparison" / "mock" / "benchmark_tasks.json",
        help="Benchmark task JSON path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "experiments" / "comparison" / "runs",
        help="Directory for run traces and reports.",
    )
    parser.add_argument("--run-id", default="", help="Optional explicit run id.")
    parser.add_argument("--max-repair-attempts", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_benchmark_tasks(args.tasks)
    evaluator = MockEvaluator()
    run_id = args.run_id or f"pilot_{int(time.time())}"
    run_dir = ensure_dir(args.output / run_id)
    traces = []
    for agent_kind in AGENT_ALIASES[args.agent]:
        host = MultiAgentHost(
            repo_root=REPO_ROOT,
            agent_kind=agent_kind,
            evaluator=evaluator,
            max_repair_attempts=args.max_repair_attempts,
        )
        for task in tasks:
            traces.append(host.run_task(task, run_dir))

    summary = write_reports(traces, run_dir / "reports")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "tasks": str(args.tasks),
                "agents": AGENT_ALIASES[args.agent],
                "max_repair_attempts": args.max_repair_attempts,
                "evaluator": {"name": evaluator.evaluator_name, "version": evaluator.evaluator_version},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_dir": run_dir.as_posix(), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
