from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.comparison.adapters.leakage_audit import audit_benchmark_leakage


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit benchmark overlap with the verified case KB.")
    parser.add_argument(
        "--tasks",
        type=Path,
        default=REPO_ROOT / "experiments" / "comparison" / "mock" / "benchmark_tasks.json",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = audit_benchmark_leakage(REPO_ROOT, args.tasks)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
