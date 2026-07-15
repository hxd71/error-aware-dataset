"""
Batch Evaluator — 批量评测运行器
=====================================
支持批量遍历全部 Benchmark 任务，输出统一评测日志与汇总报告。

功能:
    1. 遍历 all cases，逐个调用 gis_evaluator.evaluate()
    2. 汇总统计：总体通过率、错误分布、需人工审查任务列表
    3. 生成 Evaluation_Reports/ 目录下的逐任务报告与汇总报告

用法:
    python batch_evaluate.py --agent-output <dir> [--limit N] [--output reports/]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from .gis_evaluator import GisEvaluator
from .error_classifier import ErrorLabel

# ---------------------------------------------------------------------------
# NumPy → 原生 Python 类型转换工具
# ---------------------------------------------------------------------------

def _to_native(obj):
    """递归将 numpy 类型转换为原生 Python 类型，确保 JSON 可序列化"""
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj) if not np.isnan(obj) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [_to_native(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(x) for x in obj]
    return obj


# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logger = logging.getLogger("batch_evaluator")


# ===================================================================
# 批量评测器
# ===================================================================

class BatchEvaluator:
    """
    批量评测运行器
    
    遍历 cases.json 中的全部任务，对每个任务的 Agent 输出执行四层核验，
    生成逐任务 JSON 报告 + 汇总 HTML/Markdown 报告。
    """

    def __init__(self,
                 cases_path: str = "cases.json",
                 agent_output_base: str = "agent_outputs",
                 truth_base: str = "evaluation/Ground_Truth",
                 reports_dir: str = "evaluation/Reports"):
        self.cases_path = cases_path
        self.agent_output_base = Path(agent_output_base)
        self.truth_base = Path(truth_base)
        self.reports_dir = Path(reports_dir)
        self.evaluator = GisEvaluator()

    def load_cases(self) -> List[Dict[str, Any]]:
        """加载 cases.json"""
        if not os.path.exists(self.cases_path):
            raise FileNotFoundError(f"cases.json 不存在: {self.cases_path}")
        with open(self.cases_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "cases" in data:
                return data["cases"]
            if "tasks" in data:
                return data["tasks"]
            return list(data.values())
        return []

    def run(self,
            limit: Optional[int] = None,
            case_ids: Optional[List[str]] = None,
            output_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        批量运行评测

        Args:
            limit: 限制评测任务数
            case_ids: 仅评测指定任务
            output_types: 指定核验分支，默认全部

        Returns:
            汇总报告 dict
        """
        cases = self.load_cases()
        logger.info(f"加载了 {len(cases)} 条任务")

        if case_ids:
            cases = [c for c in cases if c.get("case_id") in case_ids]
            logger.info(f"筛选后 {len(cases)} 条")

        if limit:
            cases = cases[:limit]

        self.reports_dir.mkdir(parents=True, exist_ok=True)

        reports: List[Dict[str, Any]] = []
        all_errors: List[Dict] = []

        for i, case in enumerate(cases):
            case_id = case.get("case_id", f"task_{i:03d}")

            agent_dir = self.agent_output_base / case_id
            truth_dir = self.truth_base / case_id

            task_config = {
                "case_id": case_id,
                "output_types": output_types or case.get("output_types",
                                                         ["vector", "raster", "table", "map"]),
                "thresholds": self._load_thresholds(truth_dir),
                "expected_files": case.get("expected_files", {}),
                "task_type": case.get("task_type"),
                "trap_type": case.get("trap_type"),
            }

            logger.info(f"[{case_id}] ({i+1}/{len(cases)}) 评测中...")

            try:
                report = self.evaluator.evaluate(
                    agent_output_dir=str(agent_dir),
                    truth_dir=str(truth_dir),
                    task_config=task_config,
                )
                reports.append(report)
                all_errors.extend(report.get("errors", []))

                # 保存单任务报告
                self._save_report(report)

                status_icon = {"PASS": "✓", "FAIL": "✗", "PARTIAL": "△", "SKIP": "—"}
                logger.info(
                    f"  {status_icon.get(report['overall_result'], '?')} "
                    f"{report['overall_result']} "
                    f"(errors: {len(report.get('errors', []))}, "
                    f"visual_check: {report.get('requires_visual_check', False)})"
                )

            except Exception as e:
                logger.error(f"[{case_id}] 评测异常: {e}", exc_info=True)
                error_report = self._error_report(case_id, str(e))
                reports.append(error_report)
                self._save_report(error_report)

        # 生成汇总
        summary = self._build_summary(reports, all_errors)
        self._save_summary(summary)

        return summary

    @staticmethod
    def _load_thresholds(truth_dir: Path) -> Dict[str, Any]:
        """从 GT 目录加载自定义阈值"""
        thresholds_path = truth_dir / "thresholds.json"
        if thresholds_path.exists():
            with open(str(thresholds_path), "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_report(self, report: Dict[str, Any]):
        """保存单任务JSON报告"""
        case_id = report.get("case_id", "unknown")
        filename = f"{case_id}_eval_report.json"
        filepath = self.reports_dir / filename
        with open(str(filepath), "w", encoding="utf-8") as f:
            json.dump(_to_native(report), f, indent=2, ensure_ascii=False)

    def _error_report(self, case_id: str, error_msg: str) -> Dict[str, Any]:
        """生成异常报告"""
        return {
            "report_id": f"eval_{case_id}_error",
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_result": "SKIP",
            "vector_verification": {},
            "raster_verification": {},
            "table_verification": {},
            "visual_verification": {},
            "errors": [{
                "category": "E",
                "subcategory": "E3",
                "label_name": "评测系统异常",
                "description": error_msg,
            }],
            "requires_visual_check": True,
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "error_categories": ["E"],
                "failure_reasons": [f"评测系统异常: {error_msg}"],
                "metric_deltas": {},
            }
        }

    def _build_summary(self, reports: List[Dict],
                       all_errors: List[Dict]) -> Dict[str, Any]:
        """构建汇总报告"""
        total = len(reports)
        pass_count = sum(1 for r in reports if r["overall_result"] == "PASS")
        fail_count = sum(1 for r in reports if r["overall_result"] == "FAIL")
        partial_count = sum(1 for r in reports if r["overall_result"] == "PARTIAL")
        skip_count = sum(1 for r in reports if r["overall_result"] == "SKIP")
        visual_check_count = sum(1 for r in reports if r.get("requires_visual_check", False))

        # 错误分布统计
        error_distribution: Dict[str, int] = {}
        for e in all_errors:
            cat = e.get("category", "?")
            error_distribution[cat] = error_distribution.get(cat, 0) + 1

        sub_error_dist: Dict[str, int] = {}
        for e in all_errors:
            sub = e.get("subcategory", "??")
            sub_error_dist[sub] = sub_error_dist.get(sub, 0) + 1

        # 按任务类型的通过率
        pass_by_type: Dict[str, Dict] = {}
        for r in reports:
            case_id = r["case_id"]
            # 从 case_id 推断类型（简化）
            result = r["overall_result"]
            t = "all"
            if t not in pass_by_type:
                pass_by_type[t] = {"total": 0, "pass": 0}
            pass_by_type[t]["total"] += 1
            if result == "PASS":
                pass_by_type[t]["pass"] += 1

        summary = {
            "title": "GIS Agent 基准测试评测汇总报告",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_stats": {
                "total_tasks": total,
                "pass": pass_count,
                "fail": fail_count,
                "partial": partial_count,
                "skip": skip_count,
                "pass_rate": round(pass_count / total * 100, 1) if total > 0 else 0,
                "requires_visual_check": visual_check_count,
            },
            "error_summary": {
                "total_errors": len(all_errors),
                "by_category": error_distribution,
                "by_subcategory": sub_error_dist,
            },
            "pass_by_type": pass_by_type,
            "per_task": [
                {
                    "case_id": r["case_id"],
                    "result": r["overall_result"],
                    "errors": len(r.get("errors", [])),
                    "visual_check": r.get("requires_visual_check", False),
                }
                for r in reports
            ],
            "visual_check_required": [
                r["case_id"] for r in reports
                if r.get("requires_visual_check", False)
            ],
        }

        return summary

    def _save_summary(self, summary: Dict[str, Any]):
        """保存汇总报告（JSON + Markdown）"""
        # JSON 汇总
        json_path = self.reports_dir / "evaluation_summary.json"
        with open(str(json_path), "w", encoding="utf-8") as f:
            json.dump(_to_native(summary), f, indent=2, ensure_ascii=False)
        logger.info(f"汇总报告(JSON): {json_path}")

        # Markdown 汇总
        md_path = self.reports_dir / "evaluation_summary.md"
        self._write_markdown_summary(summary, md_path)
        logger.info(f"汇总报告(MD): {md_path}")

    def _write_markdown_summary(self, summary: Dict, path: Path):
        """输出 Markdown 格式汇总"""
        stats = summary["overall_stats"]
        err_sum = summary["error_summary"]

        lines = [
            f"# {summary['title']}",
            f"",
            f"**生成时间**: {summary['generated_at']}",
            f"",
            f"## 总体统计",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总任务数 | {stats['total_tasks']} |",
            f"| ✅ PASS | {stats['pass']} |",
            f"| ❌ FAIL | {stats['fail']} |",
            f"| △ PARTIAL | {stats['partial']} |",
            f"| — SKIP | {stats['skip']} |",
            f"| **通过率** | **{stats['pass_rate']}%** |",
            f"| 需人工视觉审查 | {stats['requires_visual_check']} |",
            f"",
            f"## 错误分布",
            f"",
            f"### 按大类",
            f"",
            f"| 类别 | 计数 |",
            f"|------|------|",
        ]

        category_names = {
            "A": "空间参考系错误",
            "B": "几何完整性错误",
            "C": "属性/表格错误",
            "D": "栅格数据错误",
            "E": "可视化/逻辑错误",
        }
        for cat, count in sorted(err_sum["by_category"].items()):
            lines.append(f"| {cat} — {category_names.get(cat, '?')} | {count} |")

        lines.append("")
        lines.append("### 按子类")
        lines.append("")
        lines.append("| 子类 | 计数 |")
        lines.append("|------|------|")
        for sub, count in sorted(err_sum["by_subcategory"].items()):
            lines.append(f"| {sub} | {count} |")

        lines.append("")
        lines.append("## 需人工视觉审查的任务")
        lines.append("")
        for cid in summary.get("visual_check_required", []):
            lines.append(f"- `{cid}`")
        if not summary.get("visual_check_required"):
            lines.append("（无）")

        lines.append("")
        lines.append("## 逐任务结果")
        lines.append("")
        lines.append("| Case ID | 结果 | 错误数 | 视觉审查 |")
        lines.append("|---------|------|--------|----------|")
        for t in summary.get("per_task", []):
            icon = {"PASS": "✅", "FAIL": "❌", "PARTIAL": "△", "SKIP": "—"}
            lines.append(
                f"| {t['case_id']} | {icon.get(t['result'], '?')} {t['result']} "
                f"| {t['errors']} | {'是' if t['visual_check'] else '否'} |"
            )

        with open(str(path), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


# ===================================================================
# CLI
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="批量遍历Benchmark任务输出统一评测日志"
    )
    parser.add_argument("--cases", default="cases.json", help="cases.json 路径")
    parser.add_argument("--agent-output", default="agent_outputs",
                        help="智能体输出根目录")
    parser.add_argument("--truth-base", default="evaluation/Ground_Truth",
                        help="Ground Truth 根目录")
    parser.add_argument("--reports", default="evaluation/Reports",
                        help="评测报告输出目录")
    parser.add_argument("--limit", type=int, default=None,
                        help="限制评测任务数")
    parser.add_argument("--case-ids", nargs="*", default=None,
                        help="仅评测指定case_id")
    parser.add_argument("--output-types", nargs="*",
                        choices=["vector", "raster", "table", "map"],
                        help="指定核验分支")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    runner = BatchEvaluator(
        cases_path=args.cases,
        agent_output_base=args.agent_output,
        truth_base=args.truth_base,
        reports_dir=args.reports,
    )

    summary = runner.run(
        limit=args.limit,
        case_ids=args.case_ids,
        output_types=args.output_types,
    )

    stats = summary["overall_stats"]
    print(f"\n{'='*50}")
    print(f"评测完成: {stats['total_tasks']} 任务")
    print(f"  通过率: {stats['pass_rate']}%")
    print(f"  需审查: {stats['requires_visual_check']} 任务")
    print(f"{'='*50}")

    sys.exit(0 if stats["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
