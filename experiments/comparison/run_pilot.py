from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.comparison.adapters.benchmark_loader import (
    invalid_task_skip_record,
    load_benchmark_tasks,
    split_invalid_benchmark_tasks,
    split_manual_review_tasks,
    task_skip_record,
)
from experiments.comparison.adapters.evaluator import CuratedGeoAgentEvaluatorAdapter, EvaluatorAdapter, MockEvaluator
from experiments.comparison.host_runtime.executors import ExecutorBackend, create_executor_backend, load_llm_model_config
from experiments.comparison.host_runtime.models import AgentKind, AgentRunTrace, BenchmarkTask, ensure_dir
from experiments.comparison.host_runtime.multi_agent import ExecutedAttempt, MultiAgentHost
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
    parser.add_argument(
        "--overwrite-run",
        action="store_true",
        help="Delete an existing run directory before writing. Use only for disposable probes.",
    )
    parser.add_argument("--max-repair-attempts", type=int, default=2)
    parser.add_argument(
        "--shared-initial-attempt",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Generate, execute, and evaluate attempt 0 once per task with a neutral prompt, "
            "then reuse that same first attempt for every comparison group. Enabled by default."
        ),
    )
    parser.add_argument(
        "--reuse-shared-initial-from",
        type=Path,
        default=None,
        help=(
            "Optional prior run directory whose task_id/shared_initial/attempt_00 results should be reused. "
            "This avoids regenerating attempt 0 and keeps first-pass identical across tuned reruns."
        ),
    )
    parser.add_argument(
        "--skip-manual-review",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exclude manual and hybrid review tasks from automatic benchmark runs. Enabled by default.",
    )
    parser.add_argument(
        "--skip-invalid-benchmark-tasks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Exclude known CuratedGeoAgent evaluator/source-data issue tasks from formal automatic runs. "
            "Enabled by default so reported pass rates are not polluted by invalid benchmark items."
        ),
    )
    parser.add_argument(
        "--task-limit",
        type=int,
        default=0,
        help="Optional smoke-batch limit after manual-review filtering. 0 means run all selected tasks.",
    )
    parser.add_argument(
        "--task-ids",
        nargs="*",
        default=[],
        help=(
            "Optional task ids to run after manual-review filtering. Accepts space-separated ids or comma-separated "
            "groups, for example: --task-ids curated_geoagent_085 curated_geoagent_102,curated_geoagent_119."
        ),
    )
    parser.add_argument(
        "--evaluator",
        choices=["mock", "curated"],
        default="mock",
        help="Evaluator adapter to use. Use curated for CuratedGeoAgent cases.json.",
    )
    parser.add_argument(
        "--curated-python",
        default="",
        help="Python executable used by CuratedGeoAgent task evaluators. Defaults to CURATED_GEOAGENT_PYTHON or current Python.",
    )
    parser.add_argument(
        "--executor",
        choices=["mock", "template", "llm"],
        default="mock",
        help="Code generation/execution backend for the shared host.",
    )
    parser.add_argument(
        "--executor-python",
        default="",
        help="Python executable used to run generated workflow code. Defaults to --curated-python when set, otherwise current Python.",
    )
    parser.add_argument("--execution-timeout", type=int, default=300)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help=(
            "Maximum parallel tasks per comparison group. Agents still run in group order "
            "to keep baseline/self-debug/error-aware comparable."
        ),
    )
    parser.add_argument("--llm-config", type=Path, default=None, help="Optional config.ini for OpenAI-compatible executor.")
    parser.add_argument("--llm-model", default="", help="Model name for --executor llm.")
    parser.add_argument("--llm-base-url", default="", help="Base URL for --executor llm.")
    parser.add_argument("--llm-api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--llm-request-timeout", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loaded_tasks = load_benchmark_tasks(args.tasks)
    auto_tasks, manual_review_tasks = split_manual_review_tasks(loaded_tasks)
    valid_auto_tasks, invalid_benchmark_tasks = split_invalid_benchmark_tasks(auto_tasks)
    skipped_manual_review_tasks = manual_review_tasks if args.skip_manual_review else []
    skipped_invalid_benchmark_tasks = invalid_benchmark_tasks if args.skip_invalid_benchmark_tasks else []
    if args.skip_manual_review:
        tasks = valid_auto_tasks if args.skip_invalid_benchmark_tasks else auto_tasks
    else:
        tasks = (
            [task for task in loaded_tasks if not bool(task.scoring.get("invalid_benchmark_task", False))]
            if args.skip_invalid_benchmark_tasks
            else loaded_tasks
        )
    task_ids = _parse_task_ids(args.task_ids)
    if task_ids:
        task_by_id = {task.task_id: task for task in tasks}
        missing_task_ids = [task_id for task_id in task_ids if task_id not in task_by_id]
        if missing_task_ids:
            raise SystemExit(
                "Requested task ids are not in the runnable task pool: "
                + ", ".join(missing_task_ids)
                + ". Check --skip-manual-review and the benchmark task ids."
            )
        tasks = [task_by_id[task_id] for task_id in task_ids]
    task_limit = max(0, args.task_limit)
    if task_limit:
        tasks = tasks[:task_limit]
    evaluator = (
        CuratedGeoAgentEvaluatorAdapter(python_executable=args.curated_python or None)
        if args.evaluator == "curated"
        else MockEvaluator()
    )
    full_model_config, trace_model_config = load_llm_model_config(
        config_path=args.llm_config,
        model=args.llm_model,
        base_url=args.llm_base_url,
        api_key_env=args.llm_api_key_env,
        request_timeout_seconds=args.llm_request_timeout,
        temperature=args.temperature,
    )
    if args.executor != "llm":
        trace_model_config = {"provider": args.executor, "model": f"{args.executor}-deterministic", "temperature": 0}
    executor_python = args.executor_python or args.curated_python or sys.executable
    executor_backend = create_executor_backend(
        backend=args.executor,
        python_executable=executor_python,
        timeout_seconds=args.execution_timeout,
        model_config=full_model_config if args.executor == "llm" else trace_model_config,
    )
    run_id = args.run_id or f"pilot_{int(time.time())}"
    run_dir = _prepare_run_dir(args.output, run_id, overwrite=args.overwrite_run)
    skipped_records = [task_skip_record(task) for task in skipped_manual_review_tasks]
    skipped_invalid_records = [invalid_task_skip_record(task) for task in skipped_invalid_benchmark_tasks]
    (run_dir / "skipped_manual_review_tasks.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "skip_manual_review": args.skip_manual_review,
                "skipped_manual_review_count": len(skipped_records),
                "tasks": skipped_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "skipped_invalid_benchmark_tasks.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "skip_invalid_benchmark_tasks": args.skip_invalid_benchmark_tasks,
                "skipped_invalid_benchmark_task_count": len(skipped_invalid_records),
                "tasks": skipped_invalid_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    concurrency = max(1, args.concurrency)
    shared_initial_attempts: dict[str, ExecutedAttempt] = {}
    if args.reuse_shared_initial_from:
        shared_initial_attempts = _reuse_shared_initial_attempts(
            source_run_dir=args.reuse_shared_initial_from,
            target_run_dir=run_dir,
            tasks=tasks,
        )
    elif args.shared_initial_attempt:
        shared_initial_attempts = _run_shared_initial_attempts(
            tasks=tasks,
            run_dir=run_dir,
            evaluator=evaluator,
            model_config=trace_model_config,
            executor_backend=executor_backend,
            concurrency=concurrency,
        )
    traces = []
    for agent_kind in AGENT_ALIASES[args.agent]:
        traces.extend(
            _run_agent_tasks(
                agent_kind=agent_kind,
                tasks=tasks,
                run_dir=run_dir,
                evaluator=evaluator,
                max_repair_attempts=args.max_repair_attempts,
                model_config=trace_model_config,
                executor_backend=executor_backend,
                concurrency=concurrency,
                shared_initial_attempts=shared_initial_attempts,
            )
        )
    traces.sort(key=lambda trace: (AGENT_ALIASES["all"].index(trace.agent_kind), trace.task["task_id"]))

    run_scope = {
        "loaded_task_count": len(loaded_tasks),
        "auto_task_count": len(auto_tasks),
        "valid_auto_task_count": len(valid_auto_tasks),
        "invalid_benchmark_task_count": len(invalid_benchmark_tasks),
        "manual_review_task_count": len(manual_review_tasks),
        "skipped_manual_review_count": len(skipped_manual_review_tasks),
        "skipped_invalid_benchmark_task_count": len(skipped_invalid_benchmark_tasks),
        "executed_task_count": len(tasks),
        "task_limit": task_limit,
        "task_ids": task_ids,
        "skip_manual_review": args.skip_manual_review,
        "skip_invalid_benchmark_tasks": args.skip_invalid_benchmark_tasks,
        "concurrency": concurrency,
        "shared_initial_attempt": args.shared_initial_attempt,
        "reuse_shared_initial_from": str(args.reuse_shared_initial_from) if args.reuse_shared_initial_from else "",
        "skipped_manual_review_tasks_path": "skipped_manual_review_tasks.json",
        "skipped_invalid_benchmark_tasks_path": "skipped_invalid_benchmark_tasks.json",
    }
    summary = write_reports(traces, run_dir / "reports", run_scope=run_scope)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "tasks": str(args.tasks),
                "agents": AGENT_ALIASES[args.agent],
                "max_repair_attempts": args.max_repair_attempts,
                "evaluator": {"name": evaluator.evaluator_name, "version": evaluator.evaluator_version},
                "evaluator_adapter": args.evaluator,
                "executor": {
                    "adapter": args.executor,
                    "name": executor_backend.backend_name,
                    "version": executor_backend.backend_version,
                    "python": executor_python,
                    "execution_timeout": args.execution_timeout,
                },
                "concurrency": concurrency,
                "shared_initial_attempt": args.shared_initial_attempt,
                "reuse_shared_initial_from": str(args.reuse_shared_initial_from) if args.reuse_shared_initial_from else "",
                "model_config": trace_model_config,
                "run_scope": run_scope,
                "skipped_manual_review_tasks": skipped_records,
                "skipped_invalid_benchmark_tasks": skipped_invalid_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_dir": run_dir.as_posix(), "summary": summary}, ensure_ascii=False, indent=2))


def _parse_task_ids(raw_values: list[str]) -> list[str]:
    task_ids: list[str] = []
    for value in raw_values:
        task_ids.extend(item.strip() for item in value.split(",") if item.strip())
    return task_ids


def _run_agent_tasks(
    *,
    agent_kind: AgentKind,
    tasks: list[BenchmarkTask],
    run_dir: Path,
    evaluator: EvaluatorAdapter,
    max_repair_attempts: int,
    model_config: dict[str, Any],
    executor_backend: ExecutorBackend,
    concurrency: int,
    shared_initial_attempts: dict[str, ExecutedAttempt] | None = None,
) -> list[AgentRunTrace]:
    shared_initial_attempts = shared_initial_attempts or {}
    if concurrency <= 1 or len(tasks) <= 1:
        host = MultiAgentHost(
            repo_root=REPO_ROOT,
            agent_kind=agent_kind,
            evaluator=evaluator,
            max_repair_attempts=max_repair_attempts,
            model_config=model_config,
            executor_backend=executor_backend,
        )
        return [
            host.run_task(task, run_dir, shared_initial_attempts.get(task.task_id))
            for task in tasks
        ]

    traces = []
    print(f"[{agent_kind}] running {len(tasks)} tasks with concurrency={concurrency}", flush=True)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {}
        for task in tasks:
            host = MultiAgentHost(
                repo_root=REPO_ROOT,
                agent_kind=agent_kind,
                evaluator=evaluator,
                max_repair_attempts=max_repair_attempts,
                model_config=model_config,
                executor_backend=executor_backend,
            )
            futures[pool.submit(host.run_task, task, run_dir, shared_initial_attempts.get(task.task_id))] = task.task_id
        completed = 0
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                trace = future.result()
            except Exception as exc:
                raise RuntimeError(f"{agent_kind} failed on {task_id}") from exc
            traces.append(trace)
            completed += 1
            print(
                f"[{agent_kind}] completed {completed}/{len(tasks)} "
                f"{task_id} final={trace.final_status} attempts={len(trace.attempts)}",
                flush=True,
            )
    return traces


def _run_shared_initial_attempts(
    *,
    tasks: list[BenchmarkTask],
    run_dir: Path,
    evaluator: EvaluatorAdapter,
    model_config: dict[str, Any],
    executor_backend: ExecutorBackend,
    concurrency: int,
) -> dict[str, ExecutedAttempt]:
    if not tasks:
        return {}
    if concurrency <= 1 or len(tasks) <= 1:
        host = MultiAgentHost(
            repo_root=REPO_ROOT,
            agent_kind="baseline_multi_agent",
            evaluator=evaluator,
            max_repair_attempts=0,
            model_config=model_config,
            executor_backend=executor_backend,
        )
        return {task.task_id: host.run_shared_initial_attempt(task, run_dir) for task in tasks}

    attempts: dict[str, ExecutedAttempt] = {}
    print(f"[shared_initial] running {len(tasks)} tasks with concurrency={concurrency}", flush=True)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {}
        for task in tasks:
            host = MultiAgentHost(
                repo_root=REPO_ROOT,
                agent_kind="baseline_multi_agent",
                evaluator=evaluator,
                max_repair_attempts=0,
                model_config=model_config,
                executor_backend=executor_backend,
            )
            futures[pool.submit(host.run_shared_initial_attempt, task, run_dir)] = task.task_id
        completed = 0
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                attempts[task_id] = future.result()
            except Exception as exc:
                raise RuntimeError(f"shared initial attempt failed on {task_id}") from exc
            completed += 1
            status = attempts[task_id].visible_report.get("status", "FAIL")
            print(f"[shared_initial] completed {completed}/{len(tasks)} {task_id} first={status}", flush=True)
    return attempts


def _reuse_shared_initial_attempts(
    *,
    source_run_dir: Path,
    target_run_dir: Path,
    tasks: list[BenchmarkTask],
) -> dict[str, ExecutedAttempt]:
    source_run_dir = source_run_dir.resolve(strict=False)
    if not source_run_dir.is_dir():
        raise SystemExit(f"Prior run directory not found: {source_run_dir}")
    attempts: dict[str, ExecutedAttempt] = {}
    for task in tasks:
        source_shared_dir = source_run_dir / task.task_id / "shared_initial"
        source_attempt_dir = source_shared_dir / "attempt_00"
        source_meta_path = source_shared_dir / "shared_initial_attempt.json"
        if not source_attempt_dir.is_dir() or not source_meta_path.is_file():
            raise SystemExit(f"Prior shared initial attempt not found for {task.task_id}: {source_shared_dir}")

        target_shared_dir = ensure_dir(target_run_dir / task.task_id / "shared_initial")
        target_attempt_dir = target_shared_dir / "attempt_00"
        _reset_directory(target_attempt_dir)
        shutil.copytree(source_attempt_dir, target_attempt_dir)
        meta = json.loads(source_meta_path.read_text(encoding="utf-8"))

        code_path = target_attempt_dir / "generated_code.py"
        log_path = target_attempt_dir / "execution.log"
        output_path = target_attempt_dir / "outputs"
        if not code_path.is_file() or not log_path.is_file() or not output_path.is_dir():
            raise SystemExit(f"Prior shared initial attempt is incomplete for {task.task_id}: {source_attempt_dir}")

        generated_code_path = code_path.relative_to(target_run_dir).as_posix()
        output_rel = output_path.relative_to(target_run_dir).as_posix()
        copied_meta = {
            **meta,
            "generated_code_path": generated_code_path,
            "output_path": output_rel,
            "reused_from": str(source_run_dir),
        }
        (target_shared_dir / "shared_initial_attempt.json").write_text(
            json.dumps(copied_meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        attempts[task.task_id] = ExecutedAttempt(
            attempt_index=0,
            generated_code_path=generated_code_path,
            output_path=output_rel,
            generated_code=code_path.read_text(encoding="utf-8", errors="ignore"),
            execution_log=log_path.read_text(encoding="utf-8", errors="ignore"),
            visible_report=meta["evaluation"]["agent_visible_report"],
            scoring_report=meta["scoring_report"],
            step_report=meta.get("step_report") or _read_reused_step_report(output_path),
            token_usage=meta.get("token_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
        )
    print(f"[shared_initial] reused {len(attempts)} attempts from {source_run_dir}", flush=True)
    return attempts


def _reset_directory(path: Path) -> None:
    parent_resolved = path.parent.resolve(strict=False)
    path_resolved = path.resolve(strict=False)
    if path_resolved.parent != parent_resolved:
        raise RuntimeError(f"Refusing to reset directory outside its parent: {path}")
    if path.exists():
        shutil.rmtree(path)


def _read_reused_step_report(output_path: Path) -> dict[str, Any]:
    path = output_path / "workflow_steps.json"
    if not path.is_file():
        return {"schema_version": "0.1.0", "status": "missing", "steps": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": "0.1.0", "status": "invalid", "steps": []}
    if isinstance(data, list):
        return {
            "schema_version": "0.1.0",
            "status": "reported",
            "message": "workflow_steps.json used a list root; normalized to the standard object shape.",
            "steps": [step for step in data if isinstance(step, dict)][:12],
        }
    return data if isinstance(data, dict) else {"schema_version": "0.1.0", "status": "invalid", "steps": []}


def _prepare_run_dir(output_root: Path, run_id: str, *, overwrite: bool = False) -> Path:
    output_root = ensure_dir(output_root)
    run_dir = output_root / run_id
    output_root_resolved = output_root.resolve(strict=False)
    run_dir_resolved = run_dir.resolve(strict=False)
    if run_dir_resolved.parent != output_root_resolved:
        raise SystemExit(f"Refusing to write run outside output root: {run_dir}")
    if run_dir.exists() and any(run_dir.iterdir()):
        if not overwrite:
            raise SystemExit(
                f"Run directory already exists and is not empty: {run_dir}\n"
                "Use a fresh --run-id for formal experiments, or pass --overwrite-run for a disposable rerun."
            )
        shutil.rmtree(run_dir)
    return ensure_dir(run_dir)


if __name__ == "__main__":
    main()
