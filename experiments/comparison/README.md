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
6. 生成 `step_branch_plan`：根据上一轮 `workflow_steps.json`、失败检查和错误类别，定位疑似失败步骤，并要求下一轮从该步骤建立 repair branch。

LLM 后端会被要求把工作流拆成有语义的步骤，并在 `OUTPUT_DIR/workflow_steps.json` 写入每步自检结果。Error-aware repair 会读取这个 agent-visible step report；若某一步已经标记 failed/suspect，就优先从该 step 开分支。若没有 step report，则根据 failed check 推断从 CRS/栅格/空间关系/统计/输出写入等步骤开分支。分支修复可以通过 `PREVIOUS_OUTPUT_DIR` 只读取上一轮自己产生的前序步骤 artifacts，不允许读取 evaluator、GT、reference、review 或 knowledge_base 文件。

`knowledge_base/cases/candidates.jsonl` 默认不参与正式检索。

## 接入任务二和任务三

任务二完成后，将 `Benchmark_Tasks.json` 路径传给：

```powershell
python experiments/comparison/run_pilot.py --tasks path/to/Benchmark_Tasks.json --agent all
```

当前已支持直接加载 CuratedGeoAgent 的 `cases.json` 格式，外部原始数据集保持只读，不会被框架改写：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe"
```

默认启用 `--skip-manual-review`，因此正式自动实验只运行 126 条可自动核验任务，并把 14 条 manual/hybrid 任务写入 `skipped_manual_review_tasks.json` 供汇报展示。若只是 smoke batch，先加 `--task-limit 10`：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --task-limit 10 `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe"
```

若要针对已知开发集问题定向验证，可用 `--task-ids` 只跑指定任务；例如验证 protected-road-length、line-vertex 和 bounded-Voronoi 三类修复：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --task-ids curated_geoagent_085 curated_geoagent_102 curated_geoagent_119 `
  --executor llm `
  --llm-config "F:\29145008\GeoAgent\config.ini" `
  --executor-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --execution-timeout 300 `
  --llm-request-timeout 180
```

说明：`--no-skip-manual-review` 只用于离线调试人工题分流，不用于正式自动正确率统计。

任务三完成后，在 `adapters/evaluator.py` 中新增一个 `EvaluatorAdapter` 实现，保持返回结构包含：

- `agent_visible_report`：给三组 agent 使用，不含 gold label、标准答案路径或正确代码。
- `scoring_report`：只用于离线统计，可包含 gold label、泄漏审计标记和人工评分备注。

CuratedGeoAgent 接入已经内置 `CuratedGeoAgentEvaluatorAdapter`：

- 自动评分题：运行每题 `evaluation/task_*/evaluate.py`，只把失败类型、失败检查名和聚合指标放进 `agent_visible_report`。
- 人工题：不向 agent 暴露人工 rubric；运行后进入离线人工评分流程。
- 混合题：默认随人工题一起跳过；若误传入自动运行，adapter 直接返回 `manual_review_required`，避免污染自动正确率统计。
- 报告输出包含 `auto_task_count`、`skipped_manual_review_count`、三组 pass rate，以及 `error_aware_vs_self_debug_delta`。
- 纠错指标同时包含：
  - `conditional_correction_rate`：纠错成功任务数 / 触发纠错任务数。
  - `end_to_end_correction_rate`：纠错成功任务数 / 总任务数。
  - `step_branch_trigger_count`：触发 step branch repair 的任务数。
  - `step_manifest_coverage`：至少有一轮产出可解析 `workflow_steps.json` 的任务比例。
  - `first_attempt_step_manifest_coverage`：初始 attempt 0 产出可解析 `workflow_steps.json` 的任务比例。
  - `step_branch_inferred_from_final_signal_count`：缺少可用 step report 时，只能根据最终失败信号推断 branch 的任务数。

## 信息权限与泄漏控制

任务 prompt 和 agent-visible metadata 只包含任务描述、输入数据路径、输出要求、任务难度和安全的数据摘要。它们不包含：

- A1-E3 错误类别、错误机制、预期诱发错误或 silent error 类型。
- Ground Truth、标准答案、参考输出路径、人工评分 rubric。
- 案例知识库 sample_id、修复答案或任务一样本文件名。

若某个任务本身把 "ground truth" 作为输入图层语义使用，例如要求比较估计点与人工标注点，这类输入数据名不视为评分泄漏；禁止泄漏的是 evaluator 私有参考答案、标准输出和评分细节。

三组系统获得同一份 `agent_visible_report` 失败信号。`scoring_report` 只进入离线统计和报告，不进入任何 agent prompt。

正式对比默认启用共享初始执行：`attempt 0` 只用中性任务 prompt 生成、执行和核验一次，然后三组都引用同一份初始代码、输出和 `agent_visible_report`。因此三组 `first-pass` 指标应完全一致，后续差异只来自 self-debug 或 Error-aware 修复闭环。

如果要验证 step-branch 的真实收益，不应使用缺少 `workflow_steps.json` 的旧 run 作为 `--reuse-shared-initial-from` 来源；应重新跑 fresh shared initial，让 attempt 0 生成 step manifest，再比较 `first_attempt_step_manifest_coverage` 和修复效果。

自动化核验发生在任务运行结束后：框架根据 agent 输出目录调用 evaluator，并将结果拆成 agent-visible 与 offline scoring 两份。对于需要人工审核的任务，自动化阶段只负责收集输出和可见失败信号，最终 PASS/FAIL 由人工或混合评分补齐。

## CuratedGeoAgent 人工审核任务

以下 14 个任务需要单独进入人工或混合审核队列，清单也保存在 `configs/curated_geoagent_manual_review_tasks.json`：

- Manual：`curated_geoagent_002`、`curated_geoagent_010`、`curated_geoagent_011`、`curated_geoagent_012`、`curated_geoagent_013`、`curated_geoagent_054`、`curated_geoagent_058`、`curated_geoagent_075`、`curated_geoagent_076`、`curated_geoagent_135`
- Hybrid：`curated_geoagent_057`、`curated_geoagent_074`、`curated_geoagent_093`、`curated_geoagent_127`

## 当前可运行检查

运行 mock pilot：

```powershell
python experiments/comparison/run_pilot.py --agent all
```

验证真实执行闭环，但不评估正确率：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --task-limit 1 `
  --executor template `
  --executor-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe"
```

运行真实 LLM 生成与修复闭环：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --task-limit 10 `
  --executor llm `
  --llm-config "F:\29145008\GeoAgent\config.ini" `
  --executor-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe"
```

运行 CuratedGeoAgent 全量自动核验对比实验时，不传 `--task-limit`，并可用 `--concurrency 5` 在每个实验组内部并发 5 个任务。默认会跳过 5 个已确认 evaluator/source-data 异常任务（037、043、072、095、132），因此正式自动评分分母为 121；如需审计这些任务，可显式传入 `--no-skip-invalid-benchmark-tasks`。

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --run-id curated_llm_full_auto_shared_c5_20260720 `
  --executor llm `
  --llm-config "F:\29145008\GeoAgent\config.ini" `
  --executor-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --execution-timeout 300 `
  --llm-request-timeout 180 `
  --concurrency 5
```

并发策略：先并发生成每个任务的共享 `attempt 0`，再按 baseline、self-debug、error-aware 三组顺序运行；每组内部最多 5 个任务并行。这样可以加速全量实验，同时保持三组之间的资源和知识权限边界清晰。若需复现旧版独立 first-pass 行为，可显式传入 `--no-shared-initial-attempt`，正式实验不建议关闭。

若只是微调 Error-aware 插件后复跑，为了减少首轮生成波动和 API 调用，可以复用上一轮全量实验的共享初始结果：

```powershell
python experiments/comparison/run_pilot.py `
  --tasks "F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset\curated_geoagent_dataset\cases.json" `
  --evaluator curated `
  --agent all `
  --run-id curated_llm_full_auto_shared_c5_tuned_20260720 `
  --reuse-shared-initial-from "F:\29145008\GeoAgent\gis_error_dataset\experiments\comparison\runs\curated_llm_full_auto_shared_c5_20260720" `
  --executor llm `
  --llm-config "F:\29145008\GeoAgent\config.ini" `
  --executor-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --curated-python "F:\29145008\GeoAgent\.venv\Scripts\python.exe" `
  --execution-timeout 300 `
  --llm-request-timeout 180 `
  --concurrency 5
```

`llm` 后端会把 agent-visible 任务信息发送给 OpenAI-compatible 模型，并执行模型返回的 Python 脚本。运行前需确认 API 凭据可用；生成代码会经过基础安全检查，禁止网络调用、安装包、子进程和明显删除操作。

运行 benchmark 与案例库重叠审计：

```powershell
python experiments/comparison/run_leakage_audit.py
```

运行 smoke test：

```powershell
python experiments/comparison/tests/smoke_test.py
```

运行 CuratedGeoAgent 接线测试：

```powershell
python experiments/comparison/tests/curated_benchmark_test.py
```

所有实验输出写入 `experiments/comparison/runs/`，该目录已被 `.gitignore` 忽略。
