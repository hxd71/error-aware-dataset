# Task 4 Comparison Experiment Framework

本目录是任务四的前置实验框架，用来验证：在同一多 Agent GIS 任务执行系统中，插入完整
Error-aware 插件后，是否比普通多 Agent 系统和普通自调试系统更能提升 GIS 任务正确率。

## 实验组

- `baseline_multi_agent`：共享宿主 Planner / Executor / Verifier / Reporter；只执行一次，不使用修复闭环，不访问任务一知识库。
- `self_debug_multi_agent`：在相同宿主上允许最多 2 次普通自修复；只能读取 traceback、运行日志和 agent-visible evaluator 报告。
- `error_aware_multi_agent`：在相同宿主上插入完整 Error-aware 插件；插件读取规则卡、标注指南和 verified 案例知识库。

案例知识库是 Error-aware 插件的一部分，本实验不单独做 rules-only 或 no-case 消融。

## Error-aware 插件

插件位于 `plugins/error_aware/`，只在执行失败或 evaluator 判 FAIL 后被调用。它不会替代宿主
Planner/Executor/Verifier，也不直接执行 GIS 工作流。

插件流程：

1. 汇总任务描述、代码、日志、输出状态和 agent-visible evaluator 报告。
2. 用 `knowledge_base/rule_cards.json` 做候选错误类别初筛。
3. 用根目录 `GIS_WORKFLOW_ERROR_ANNOTATION_GUIDE.md` 做根因解释和相邻类别排除。
4. 按 A-E 候选类别检索 `knowledge_base/cases/by_category/*.jsonl`，必要时回退 `all_cases.jsonl`。
5. 使用命中案例的 `repair_playbook` 生成修复建议、禁止做法和验证检查。

`knowledge_base/cases/candidates.jsonl` 默认不参与正式检索。

## 接入任务二和任务三

任务二完成后，将 `Benchmark_Tasks.json` 路径传给：

```powershell
python experiments/comparison/run_pilot.py --tasks path/to/Benchmark_Tasks.json --agent all
```

任务三完成后，在 `adapters/evaluator.py` 中新增一个 `EvaluatorAdapter` 实现，保持返回结构包含：

- `agent_visible_report`：给三组 agent 使用，不含 gold label、标准答案路径或正确代码。
- `scoring_report`：只用于离线统计，可包含 gold label、泄漏审计标记和人工评分备注。

## 当前可运行检查

运行 mock pilot：

```powershell
python experiments/comparison/run_pilot.py --agent all
```

运行 benchmark 与案例库重叠审计：

```powershell
python experiments/comparison/run_leakage_audit.py
```

运行 smoke test：

```powershell
python experiments/comparison/tests/smoke_test.py
```

所有实验输出写入 `experiments/comparison/runs/`，该目录已被 `.gitignore` 忽略。
