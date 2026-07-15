# Evaluation Pipeline — GIS Error-aware Agent 自动化核验框架

## 目录结构总览

```
curated_geoagent_dataset/
├── cases.json                         # Benchmark 任务集 (≡ Benchmark_Tasks.json)
├── assets/                            # 原始输入空间数据（未做异常修复）
├── asset_fixes/                       # 陷阱任务扰动修复数据 + 修复清单
├── review/                            # 人工审核定稿任务总表
├── provenance.json                    # 全量数据溯源信息
├── README.md                          # 数据集说明
│
└── evaluation/                        # ★ 评测模块（禁止作为Agent任务输入）
    ├── __init__.py                    # Python 包入口
    ├── gis_evaluator.py               # 核心核验引擎（四层比对）
    ├── error_classifier.py            # GIS 错误分类器（A-E 五大类 15 子类）
    ├── generate_ground_truth.py       # Ground Truth 批量生成脚本
    ├── batch_evaluate.py              # 批量评测运行器
    ├── eval_curated_geoagent.py       # ★ 主入口（对应 README 运行命令）
    │
    ├── Schemas/
    │   └── evaluation_schema.json     # 评估报告 JSON Schema 定义
    │
    ├── Ground_Truth/                  # ★ 标准真值库
    │   ├── generation_manifest.json   # GT 生成清单
    │   ├── curated_geoagent_001/
    │   │   ├── expected_vector.geojson  # 矢量标准结果
    │   │   ├── expected_raster.tif      # 栅格标准结果
    │   │   ├── stats.csv                # 统计真值表
    │   │   ├── map.png                  # 标准制图结果
    │   │   ├── thresholds.json          # 量化验证阈值
    │   │   └── meta.json                # 任务元信息
    │   ├── curated_geoagent_002/
    │   └── ...
    │
    └── Reports/                       # ★ 评测报告输出
        ├── evaluation_summary.json    # JSON 汇总报告
        ├── evaluation_summary.md      # Markdown 汇总报告
        └── {case_id}_eval_report.json # 逐任务详细报告
```

---

## Ground Truth 目录与命名规范

### 目录结构

每个 Benchmark 任务在 `Ground_Truth/` 下拥有独立子目录，以 `case_id` 命名：

```
Ground_Truth/{case_id}/
```

### 文件命名规则

| 文件 | 规范命名 | 说明 |
|------|----------|------|
| 矢量标准结果 | `expected_vector.geojson` | 固定命名，GeoJSON 格式 |
| 栅格标准结果 | `expected_raster.tif` | 固定命名，GeoTIFF 格式 |
| 统计真值表 | `stats.csv` | 固定命名，UTF-8 CSV |
| 标准制图 | `map.png` | 固定命名，150 DPI PNG |
| 验证阈值 | `thresholds.json` | 固定命名，可覆盖默认容差 |
| 元信息 | `meta.json` | 固定命名，记录生成信息 |

### thresholds.json 格式

```json
{
  "area_tolerance_pct": 5.0,
  "length_tolerance_pct": 5.0,
  "extent_tolerance": 1e-6,
  "stats_tolerance": 0.05,
  "numeric_tolerance_pct": 1.0
}
```

---

## GIS 错误分类体系（A-E 五大类 15 子类）

| 代码 | 类别 | 错误名 | 触发条件 |
|------|------|--------|----------|
| **A1** | 空间参考系 | CRS不匹配 | 输出坐标系与GT不一致 |
| **A2** | 空间参考系 | 投影转换错误 | 投影参数或转换过程异常 |
| **A3** | 空间参考系 | 坐标越界 | 几何坐标超出有效范围 |
| **B1** | 几何完整性 | 无效几何/自相交 | 输出包含自相交环等无效结构 |
| **B2** | 几何完整性 | 拓扑错误 | 面重叠/空隙、线未正确连接 |
| **B3** | 几何完整性 | 几何类型不匹配 | 输出类型与期望不一致 |
| **C1** | 属性/表格 | 字段缺失/不匹配 | 缺少必要字段或包含多余字段 |
| **C2** | 属性/表格 | 属性值错误 | 字段值计算错误或类型不匹配 |
| **C3** | 属性/表格 | 统计量偏差 | 分组统计/聚合超出允许误差 |
| **D1** | 栅格数据 | 波段/分辨率不匹配 | 波段数或像元分辨率不一致 |
| **D2** | 栅格数据 | NoData异常 | NoData定义错误或处理不当 |
| **D3** | 栅格数据 | 栅格范围偏差 | 空间范围/原点偏移超阈值 |
| **E1** | 可视化/逻辑 | 图层错位/空白输出 | 图层空间偏移或空白渲染 |
| **E2** | 可视化/逻辑 | 制图元素缺失 | 缺少图例/比例尺/指北针/标题 |
| **E3** | 可视化/逻辑 | 隐形逻辑错误 | 表面正常但存在深层逻辑缺陷 |

---

## 快速开始

### 1. 环境准备

```powershell
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install geopandas rasterio shapely pandas numpy matplotlib pillow
```

### 2. 生成 Ground Truth 标准真值库

```powershell
# 全量生成
.venv\Scripts\python.exe -m evaluation.generate_ground_truth

# 先导测试（前10条）
.venv\Scripts\python.exe -m evaluation.generate_ground_truth --limit 10

# 跳过已有GT
.venv\Scripts\python.exe -m evaluation.generate_ground_truth --skip-existing

# 指定任务
.venv\Scripts\python.exe -m evaluation.generate_ground_truth --case-ids curated_geoagent_001 curated_geoagent_002
```

### 3. 运行基准评测

```powershell
# 完整运行（对应 README 命令）
.venv\Scripts\python.exe -m evaluation.eval_curated_geoagent

# Pilot Test 先导测试
.venv\Scripts\python.exe -m evaluation.eval_curated_geoagent --limit 10 --verbose

# 指定 Agent 输出目录
.venv\Scripts\python.exe -m evaluation.eval_curated_geoagent --agent-output path/to/agent/outputs

# 仅核验矢量和栅格
.venv\Scripts\python.exe -m evaluation.eval_curated_geoagent --output-types vector raster

# 查看错误分类体系
.venv\Scripts\python.exe -m evaluation.eval_curated_geoagent --show-taxonomy
```

### 4. 直接调用 Python API

```python
from evaluation import GisEvaluator

evaluator = GisEvaluator()

report = evaluator.evaluate(
    agent_output_dir="agent_outputs/curated_geoagent_001",
    truth_dir="evaluation/Ground_Truth/curated_geoagent_001",
    task_config={
        "case_id": "curated_geoagent_001",
        "output_types": ["vector", "raster", "table", "map"],
    }
)

print(report["overall_result"])  # PASS / FAIL / PARTIAL / SKIP
print(report["errors"])          # GIS错误标签列表
print(report["requires_visual_check"])  # 是否需人工审查
```

---

## cases.json 任务配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `case_id` | string | 全局唯一编号 `curated_geoagent_XXX` |
| `source_id` | int | 原始任务溯源编号 |
| `task_type` | string | `vector_single` / `raster_single` / `composite_workflow` / `trap` |
| `complexity_level` | int | 1=单步, 2=多流程, 3=逻辑推理 |
| `scenario` | string | 业务场景分类 |
| `task` | string | 自然语言任务指令 |
| `output_requirements` | string | 输出约束说明 |
| `inputs` | object | 输入数据路径映射 |
| `operations` | array | 操作链定义 |
| `output_types` | array | 期望输出类型 `["vector","raster","table","map"]` |
| `trap_type` | string | 陷阱类型（仅陷阱任务） |
| `is_trap` | bool | 是否陷阱任务 |
| `thresholds` | object | 自定义验证阈值 |

---

## 评估报告 JSON 结构

符合 `Schemas/evaluation_schema.json` 规范：

```json
{
  "report_id": "eval_curated_geoagent_001_20260715T120000Z",
  "case_id": "curated_geoagent_001",
  "timestamp": "2026-07-15T12:00:00+00:00",
  "overall_result": "PASS",
  "vector_verification": { ... },
  "raster_verification": { ... },
  "table_verification": { ... },
  "visual_verification": {
    "requires_visual_check": false,
    "anomaly_symptoms": []
  },
  "errors": [],
  "requires_visual_check": false,
  "summary": {
    "total_checks": 18,
    "passed_checks": 18,
    "failed_checks": 0,
    "error_categories": [],
    "failure_reasons": [],
    "metric_deltas": {}
  }
}
```

---

## 核验四大分支逻辑

### ① 矢量核验 (VectorVerifier)
- 文件存在性 → CRS一致性 → 几何有效性 → 要素数量 → 面积/长度误差 → 属性字段匹配
- 若CRS不匹配，自动将Agent数据重投影至GT坐标系后继续核验

### ② 栅格核验 (RasterVerifier)
- 文件存在性 → 波段数 → 分辨率 → 空间范围 → NoData值 → 统计指标(RMSE/MAE/R²)
- 若分辨率或范围不对齐，取公共区域交集对比

### ③ 属性统计表核验 (TableVerifier)
- 文件存在性 → 列名匹配 → 行数匹配 → 数值列逐行对比
- 支持缺失/多余列检测、NaN一致性判断

### ④ 可视化隐形错误核验 (VisualVerifier)
- 空白输出检测（纯白/纯黑/纯色）
- 与GT图像结构相似性对比（直方图相关、像素差异率）
- 启发性制图元素检测（图例/比例尺/标题/指北针）
- 交叉引用矢量/栅格核验结果推断可视化异常
- 自动标记 `Requires_Visual_Check`

---

## 隐形逻辑错误自动识别机制

以下情况将自动触发 `requires_visual_check = True`：

1. **空白输出**：输出图像为标准差<5的纯色图
2. **图层错位**：与GT像素差异率>90%或颜色直方图相关<0.3
3. **制图元素缺失**：底部/右侧/顶部条带均匀（启发性判断）
4. **交叉推理**：矢量CRS不匹配 + 栅格范围不一致 → 图层错位
5. **符号异常**：颜色分布与GT高度不相关

当 `requires_visual_check = True` 时，`anomaly_symptoms` 数组记录具体异常症状，
同时生成 `E3` 隐形逻辑错误标签，提示人工介入审查。

---

## 文件清单

| 文件 | 功能 | 行数 |
|------|------|------|
| `evaluation/__init__.py` | 包入口与导出 | ~60 |
| `evaluation/gis_evaluator.py` | 核心核验引擎（四层比对） | ~580 |
| `evaluation/error_classifier.py` | GIS错误分类器（15子类） | ~380 |
| `evaluation/generate_ground_truth.py` | GT批量生成脚本 | ~440 |
| `evaluation/batch_evaluate.py` | 批量评测运行器 | ~310 |
| `evaluation/eval_curated_geoagent.py` | 主入口模块 | ~200 |
| `evaluation/Schemas/evaluation_schema.json` | 报告JSON Schema | ~250 |
| `cases.json` | Benchmark任务配置模板 | ~160 |
