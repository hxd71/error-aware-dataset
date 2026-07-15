"""
curated_geoagent_dataset 评测模块包
=====================================
GIS Error-aware Agent Benchmark 自动化核验框架。

目录结构:
    evaluation/
    ├── __init__.py                     # 本文件
    ├── gis_evaluator.py                # 核心核验引擎
    ├── error_classifier.py             # GIS错误分类器
    ├── generate_ground_truth.py        # GT批量生成脚本
    ├── batch_evaluate.py               # 批量评测运行器
    ├── eval_curated_geoagent.py        # 主入口
    ├── Schemas/
    │   └── evaluation_schema.json      # 评估报告JSON Schema
    ├── Ground_Truth/                   # 标准真值库
    │   └── {case_id}/
    │       ├── expected_vector.geojson
    │       ├── expected_raster.tif
    │       ├── stats.csv
    │       ├── map.png
    │       ├── thresholds.json
    │       └── meta.json
    └── Reports/                        # 评测报告输出
        ├── {case_id}_eval_report.json
        ├── evaluation_summary.json
        └── evaluation_summary.md
"""

from .gis_evaluator import GisEvaluator, VectorVerifier, RasterVerifier, TableVerifier, VisualVerifier, evaluate
from .error_classifier import ErrorClassifier, ErrorLabel, ErrorCategory, ErrorSubCategory
from .generate_ground_truth import GroundTruthGenerator
from .batch_evaluate import BatchEvaluator

__all__ = [
    "GisEvaluator",
    "VectorVerifier",
    "RasterVerifier",
    "TableVerifier",
    "VisualVerifier",
    "evaluate",
    "ErrorClassifier",
    "ErrorLabel",
    "ErrorCategory",
    "ErrorSubCategory",
    "GroundTruthGenerator",
    "BatchEvaluator",
]

__version__ = "1.0.0"
