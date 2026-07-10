# GIS 错误数据集运行审计

本报告区分真实运行样本与论文研究补充样本。只有代码、成果和量化检查共同支持 GIS 专业错误时，
运行记录才进入 `observed_run`；系统失败、空运行和不确定案例不会被强行映射到 A–E。

## 运行记录覆盖

原始实验审计与自建定向任务审计分别保存，避免两套运行编号相互覆盖：

- 原始实验记录：882（完成 680，失败 160，缺少运行材料 42），见 `extraction_audit.csv/json`。
- 自建定向记录：28，见 `targeted_run_audit.csv/json`。
- 外部论文复现记录：12（LLM-Geo 3 条，GeoNatureAgent/GeoBenchX 7 条，GeoBenchX 官方调参集任务轨迹 2 条），其中 7 条经 GIS 审计进入主样本；GeoNature/GeoBenchX 审计见 `external_task_runs/geonature_audit_summary.json` 与 GeoBenchX 样本运行目录。
- 下表为可恢复运行清单的模式统计，不等同于原始实验记录总数。

| Mode / variant | Run records |
| :--- | ---: |
| no-thinking / main | 105 |
| no-thinking / self_built_targeted | 14 |
| no-thinking / viscritic_eval | 1 |
| text-only / viscritic_eval | 14 |
| thinking / early_full | 7 |
| thinking / legacy_session | 138 |
| thinking / main | 147 |
| thinking / main_retry | 17 |
| thinking / self_built_targeted | 14 |
| thinking / tokenrun | 36 |
| visual-all / viscritic_eval | 12 |
| visual-one / viscritic_eval | 20 |

- Total run records: 525
- Records without a recoverable benchmark task: 60
- observed_run 样本：65
- research_supplement 样本：2
- observed_run taxonomy 覆盖：14/15
- 尚无 observed_run 的类别：A1. Coordinate Axis Misinterpretation

## 自建定向任务运行

| 推理配置 | 运行数 | 目标错误 | 正确结果 | 排除 |
| :--- | ---: | ---: | ---: | ---: |
| thinking | 14 | 0 | 7 | 7 |
| no-thinking | 14 | 1 | 5 | 8 |

详细判定见 `targeted_run_audit.csv/json`。

## observed_run 样本

| 来源 | 主标签 | 推理配置 |
| :--- | :--- | :--- |
| GeoAgent Task 143 | A2. CRS Inconsistency | thinking 开关未单列记录 |
| GeoAgent Task 39 | A2. CRS Inconsistency | thinking 开关未单列记录 |
| GeoAgent Task 112 | A3. Unit Misinterpretation | thinking 已开启 |
| GeoAgent Task 116 | A3. Unit Misinterpretation | thinking 已开启 |
| GeoAgent Task 4 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 63 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 73 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 81 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 88 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 93 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 96 | A3. Unit Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 1 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |
| GeoAgent Task 107 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 126 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 127 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 140 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 146 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 21 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |
| GeoAgent Task 34 | B1. Dataset Integrity Violation | thinking 已开启 |
| GeoAgent Task 64 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |
| GeoAgent Task 70 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |
| GeoAgent Task 83 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |
| GeoNatureAgent BigEarthNet Forest Cover Rank | B1. Dataset Integrity Violation | direct request；thinking 开关未单列记录 |
| GeoAgent Task 100 | B2. Raster Alignment Failure | thinking 开关未单列记录 |
| GeoAgent Task 66 | B2. Raster Alignment Failure | thinking 开关未单列记录 |
| GeoAgent Task 67 | B2. Raster Alignment Failure | thinking 开关未单列记录 |
| GeoAgent Task 74 | B2. Raster Alignment Failure | thinking 开关未单列记录 |
| GeoAgent Task 77 | B2. Raster Alignment Failure | thinking 开关未单列记录 |
| GeoAgent Task 105 | B3. Missing Data Misinterpretation | thinking 已开启 |
| GeoAgent Task 12 | B3. Missing Data Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 55 | B3. Missing Data Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 56 | B3. Missing Data Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 113 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 124 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 30 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 31 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 41 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 57 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 7 | C1. Topological Predicate Confusion | thinking 开关未单列记录 |
| GeoAgent Task 94 | C1. Topological Predicate Confusion | thinking 已开启 |
| Self-built GIS Task C2-01 | C2. Invalid Geometry Handling | thinking 已关闭 |
| LLM-Geo Axis_order_SC_hospitals | C2. Invalid Geometry Handling | direct request；thinking 开关未单列记录 |
| GeoBenchX/GeoNature Murcia 50km Buffer | C2. Invalid Geometry Handling | direct request；thinking 开关未单列记录 |
| GeoAgent Task 82 | C3. Network Connectivity Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 133 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 22 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 40 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 65 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 76 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 89 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 92 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 95 | D1. Aggregation Scope Confusion | thinking 开关未单列记录 |
| GeoAgent Task 2 | D2. Spatial Allocation Error | thinking 已关闭 |
| GeoAgent Task 75 | D2. Spatial Allocation Error | thinking 已开启 |
| GeoBenchX Earthquake Population Heatmap | D2. Spatial Allocation Error | published tool-call trace; temperature 0 |
| GeoAgent Task 84 | D2. Spatial Allocation Error | thinking 开关未单列记录 |
| GeoAgent Task 104 | D3. Spatial Statistical Misinterpretation | thinking 开关未单列记录 |
| GeoAgent Task 119 | D3. Spatial Statistical Misinterpretation | thinking 开关未单列记录 |
| GeoNatureAgent CO2 Candidate Pool Comparison | D3. Spatial Statistical Misinterpretation | direct request；thinking 开关未单列记录 |
| GeoBenchX Rural Population Percentages | D3. Spatial Statistical Misinterpretation | published tool-call trace; temperature 0 |
| LLM-Geo Population_equal_interval_NC | E1. Classification Scheme Misuse | direct request；thinking 开关未单列记录 |
| GeoAgent Task 79 | E2. Symbolization Error | thinking 已开启 |
| GeoAgent Task 102 | E3. Map Composition Defect | thinking 开关未单列记录 |
| GeoAgent Task 78 | E3. Map Composition Defect | thinking 开关未单列记录 |
| GeoAgent Task 79 | E3. Map Composition Defect | thinking 开关未单列记录 |

## research_supplement 样本

| 来源 | 主标签 |
| :--- | :--- |
| GeoAgent Task 66 | A1. Coordinate Axis Misinterpretation |
| GeoAgent Task 79 | E1. Classification Scheme Misuse |
