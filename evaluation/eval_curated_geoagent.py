"""
eval_curated_geoagent — 主入口模块
====================================
Curated GeoAgent Dataset 基准测试运行入口。

对应 README 中的运行命令:
    .venv\\Scripts\\python.exe -m src.evaluation.eval_curated_geoagent

功能:
    1. 加载 cases.json 获取全部任务配置
    2. 框架自动拼接 task 指令 + output_requirements 生成查询
       （评测元数据不会注入 Agent 任务上下文）
    3. 调用 GisEvaluator 对每个任务的 Agent 输出执行四层核验
    4. 生成 Evaluation_Reports/ 下的逐任务报告 + 汇总报告

用法:
    # 完整运行
    python -m evaluation.eval_curated_geoagent

    # 限制任务数（先导测试 Pilot Test）
    python -m evaluation.eval_curated_geoagent --limit 10

    # 指定 Agent 输出目录
    python -m evaluation.eval_curated_geoagent --agent-output path/to/outputs

    # 仅矢量 + 栅格核验
    python -m evaluation.eval_curated_geoagent --output-types vector raster
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from evaluation.batch_evaluate import BatchEvaluator
from evaluation.error_classifier import list_all_errors


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def print_banner():
    """打印横幅"""
    print(r"""
╔══════════════════════════════════════════════════════════╗
║     Curated GeoAgent Dataset — 基准测试评测框架         ║
║     GIS Error-aware Agent Benchmark Suite               ║
╚══════════════════════════════════════════════════════════╝
""")


def print_error_taxonomy():
    """打印错误分类体系"""
    print("GIS 错误分类体系 (A-E 五大类 15 子类):")
    print("-" * 55)
    errors = list_all_errors()
    for e in errors:
        print(f"  [{e['code']}] {e['name_cn']} ({e['name_en']})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Curated GeoAgent Dataset 基准测试评测入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m evaluation.eval_curated_geoagent
  python -m evaluation.eval_curated_geoagent --limit 10 --verbose
  python -m evaluation.eval_curated_geoagent --agent-output ../agent_runs/run_01
  python -m evaluation.eval_curated_geoagent --output-types vector raster
  python -m evaluation.eval_curated_geoagent --show-taxonomy
        """
    )

    parser.add_argument(
        "--cases", default="cases.json",
        help="cases.json 路径 (默认: cases.json)"
    )
    parser.add_argument(
        "--agent-output", default="agent_outputs",
        help="智能体输出根目录 (默认: agent_outputs)"
    )
    parser.add_argument(
        "--truth-base", default="evaluation/Ground_Truth",
        help="Ground Truth 根目录 (默认: evaluation/Ground_Truth)"
    )
    parser.add_argument(
        "--reports", default="evaluation/Reports",
        help="评测报告输出目录 (默认: evaluation/Reports)"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="限制评测任务数（用于先导测试 Pilot Test）"
    )
    parser.add_argument(
        "--case-ids", nargs="*", default=None,
        help="仅评测指定 case_id 列表"
    )
    parser.add_argument(
        "--output-types", nargs="*",
        choices=["vector", "raster", "table", "map"],
        default=None,
        help="指定核验分支 (默认全部)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="详细日志输出"
    )
    parser.add_argument(
        "--show-taxonomy", action="store_true",
        help="显示错误分类体系后退出"
    )
    parser.add_argument(
        "--output-format", choices=["json", "markdown", "both"],
        default="both",
        help="汇总报告格式 (默认: both)"
    )

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    # 显示错误分类体系
    if args.show_taxonomy:
        print_error_taxonomy()
        return

    # 配置日志
    setup_logging(args.verbose)

    logger = logging.getLogger("eval_curated_geoagent")
    logger.info("初始化评测框架...")

    # 验证必要路径
    if not os.path.exists(args.cases):
        logger.error(f"cases.json 不存在: {args.cases}")
        logger.info("请确保在项目根目录运行，或使用 --cases 指定路径")
        sys.exit(1)

    # 打印配置摘要
    logger.info(f"任务配置: {args.cases}")
    logger.info(f"Agent输出: {args.agent_output}")
    logger.info(f"Ground Truth: {args.truth_base}")
    logger.info(f"评测报告: {args.reports}")
    if args.limit:
        logger.info(f"限制任务数: {args.limit} (Pilot Test 模式)")
    if args.output_types:
        logger.info(f"核验分支: {args.output_types}")

    # 创建评测运行器
    runner = BatchEvaluator(
        cases_path=args.cases,
        agent_output_base=args.agent_output,
        truth_base=args.truth_base,
        reports_dir=args.reports,
    )

    # 运行评测
    logger.info("=" * 50)
    logger.info("开始批量评测...")
    logger.info("=" * 50)

    try:
        summary = runner.run(
            limit=args.limit,
            case_ids=args.case_ids,
            output_types=args.output_types,
        )
    except KeyboardInterrupt:
        logger.warning("用户中断评测")
        sys.exit(130)
    except Exception as e:
        logger.error(f"评测运行异常: {e}", exc_info=True)
        sys.exit(1)

    # 输出结果摘要
    stats = summary["overall_stats"]
    err_sum = summary["error_summary"]

    print(f"\n{'='*60}")
    print(f"📊 评测完成 — 结果摘要")
    print(f"{'='*60}")
    print(f"  总任务数:     {stats['total_tasks']}")
    print(f"  ✅ PASS:      {stats['pass']}")
    print(f"  ❌ FAIL:      {stats['fail']}")
    print(f"  △ PARTIAL:   {stats['partial']}")
    print(f"  — SKIP:       {stats['skip']}")
    print(f"  通过率:       {stats['pass_rate']}%")
    print(f"  总错误数:     {err_sum['total_errors']}")
    print(f"  需视觉审查:   {stats['requires_visual_check']}")
    print(f"{'='*60}")

    if err_sum["total_errors"] > 0:
        print(f"\n错误按大类分布:")
        category_names = {
            "A": "空间参考系错误",
            "B": "几何完整性错误",
            "C": "属性/表格错误",
            "D": "栅格数据错误",
            "E": "可视化/逻辑错误",
        }
        for cat, count in sorted(err_sum["by_category"].items()):
            bar = "█" * min(count, 40)
            print(f"  {cat} — {category_names.get(cat, '?')}: {count} {bar}")

    print(f"\n📁 详细报告已保存至: {args.reports}")
    print(f"   - evaluation_summary.json  (JSON汇总)")
    print(f"   - evaluation_summary.md    (Markdown汇总)")
    print(f"   - {{case_id}}_eval_report.json (逐任务报告)")
    print()

    sys.exit(0 if stats["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
