# GIS Error Knowledge Base

本目录存放面向 agent 的检索产物。它们从根目录 `manifest.json`、各样本目录的
`annotation.json` 和 `evidence/README.md` 再生成，不是新的真相源。

## 文件结构

- `rule_cards.json`：高召回初筛规则卡。它只帮助 agent 生成候选错误假设，不负责最终定类，也不提供修复答案。
- `cases/all_cases.jsonl`：全部 verified 案例库。每行一个案例，包含检索摘要、关键证据和修复 playbook。
- `cases/by_category/A_spatial_reference.jsonl`：A 类空间参考错误案例。
- `cases/by_category/B_spatial_data.jsonl`：B 类空间数据表示错误案例。
- `cases/by_category/C_spatial_reasoning.jsonl`：C 类空间关系与推理错误案例。
- `cases/by_category/D_spatial_analysis.jsonl`：D 类空间分析语义错误案例。
- `cases/by_category/E_cartographic.jsonl`：E 类地图表达错误案例。
- `cases/candidates.jsonl`：新任务回馈候选池，默认不参与 verified RAG。
- `cases/index.json`：案例数量、标签覆盖和分库路径索引。

## 推荐 Agent 流程

1. 使用 `rule_cards.json` 和根目录 `GIS_WORKFLOW_ERROR_ANNOTATION_GUIDE.md` 生成 top-k 候选标签。
2. 按候选标签的 A-E 大类优先检索对应 `cases/by_category/*.jsonl`。
3. 大类不确定时，再回退到 `cases/all_cases.jsonl`。
4. 命中案例后，只把案例作为类比、证据补强和修复参考；最终标签仍需按标注指南做互斥判断。
5. 每次返回案例时，应说明相似点、差异点、可迁移修复原则和验证检查。

`cases/candidates.jsonl` 只用于保存未验证的新任务回馈。只有具备运行证据、修复前后差异或人工确认后，候选案例才可晋升到 verified 主库。案例库更新不能自动改写 `rule_cards.json`；规则卡只能根据离线评测汇总后人工或脚本压缩更新。

## 再生成

运行：

```powershell
python tools/build_case_kb.py
```

该命令会重建 `cases/all_cases.jsonl`、五个 A-E 分库和 `cases/index.json`；若
`cases/candidates.jsonl` 不存在，会创建空候选池，但不会覆盖已有候选反馈。
