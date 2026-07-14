from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
RULE_CARDS_PATH = KNOWLEDGE_BASE_DIR / "rule_cards.json"
CASES_DIR = KNOWLEDGE_BASE_DIR / "cases"
BY_CATEGORY_DIR = CASES_DIR / "by_category"
CASE_KB_PATH = CASES_DIR / "all_cases.jsonl"
CANDIDATE_KB_PATH = CASES_DIR / "candidates.jsonl"
INDEX_PATH = CASES_DIR / "index.json"


CATEGORY_OUTPUTS: dict[str, dict[str, Any]] = {
    "A": {
        "name": "A. Spatial Reference Errors",
        "path": BY_CATEGORY_DIR / "A_spatial_reference.jsonl",
        "description": "CRS, axis, coordinate frame, and spatial measurement semantics.",
    },
    "B": {
        "name": "B. Spatial Data Errors",
        "path": BY_CATEGORY_DIR / "B_spatial_data.jsonl",
        "description": "GIS file, attribute, raster, NoData, and data model representation semantics.",
    },
    "C": {
        "name": "C. Spatial Reasoning Errors",
        "path": BY_CATEGORY_DIR / "C_spatial_reasoning.jsonl",
        "description": "Topological, geometry validity, and network connectivity semantics.",
    },
    "D": {
        "name": "D. Spatial Analysis Errors",
        "path": BY_CATEGORY_DIR / "D_spatial_analysis.jsonl",
        "description": "Aggregation scope, allocation, and spatial statistical analysis semantics.",
    },
    "E": {
        "name": "E. Cartographic Errors",
        "path": BY_CATEGORY_DIR / "E_cartographic.jsonl",
        "description": "Classification, symbolization, and map composition semantics.",
    },
}


LABEL_TAGS: dict[str, list[str]] = {
    "A1. Coordinate Axis Misinterpretation": ["axis_order", "dimension_identity", "coordinate_semantics"],
    "A2. CRS Inconsistency": ["crs", "spatial_reference", "reprojection", "comparability"],
    "A3. Unit Misinterpretation": ["unit", "distance", "area", "measurement_semantics"],
    "B1. Dataset Integrity Violation": ["dataset_integrity", "metadata", "schema", "gis_file_model"],
    "B2. Raster Alignment Failure": ["raster_alignment", "grid", "transform", "resolution"],
    "B3. Missing Data Misinterpretation": ["nodata", "mask", "missing_values", "valid_observation"],
    "C1. Topological Predicate Confusion": ["topological_predicate", "spatial_relation", "relation_semantics"],
    "C2. Invalid Geometry Handling": ["invalid_geometry", "topology_validity", "geometry_precondition"],
    "C3. Network Connectivity Misinterpretation": ["network_connectivity", "routing", "reachability", "graph_semantics"],
    "D1. Aggregation Scope Confusion": ["aggregation_scope", "grouping", "local_vs_global", "analysis_extent"],
    "D2. Spatial Allocation Error": ["spatial_allocation", "spatial_support", "weighting", "variable_transfer"],
    "D3. Spatial Statistical Misinterpretation": ["spatial_statistics", "threshold", "derived_indicator", "statistical_semantics"],
    "E1. Classification Scheme Misuse": ["map_classification", "class_breaks", "classification_scheme"],
    "E2. Symbolization Error": ["symbolization", "visual_encoding", "visual_variable"],
    "E3. Map Composition Defect": ["map_composition", "legend", "context_layer", "map_deliverable"],
}


REPAIR_TEMPLATES: dict[str, dict[str, Any]] = {
    "A1. Coordinate Axis Misinterpretation": {
        "repair_goal": "恢复坐标轴、维度、行列或接口轴序的空间身份，使输出位置回到任务预期位置。",
        "repair_principle": "保持 x/y、lon/lat、easting/northing、row/col 等维度语义在读取、转换、分析和输出中一致。",
        "recommended_actions": [
            "确认每个坐标字段或数组维度的空间身份，再执行几何构造或坐标写出。",
            "在不同接口约定之间转换时显式记录轴序语义。",
            "用输出位置与预期研究区或参考对象的空间一致性验证轴序。",
        ],
        "forbidden_actions": [
            "在字段语义未知时自动猜测并交换坐标。",
            "只依赖数值范围判断经纬度或投影坐标轴序。",
        ],
        "validation_checks": [
            "检查输出空间范围与任务研究区是否一致。",
            "检查交换轴序后是否不再比原输出更接近参考位置。",
            "检查依赖位置的下游采样或空间分析是否使用修正后的几何。",
        ],
        "success_criteria": [
            "输出对象的位置语义与任务输入、字段含义和参考预览一致。",
            "轴序调整不再改变结果到更合理的位置。",
        ],
    },
    "A2. CRS Inconsistency": {
        "repair_goal": "让参与空间比较、叠加、裁剪、连接或测量的对象处于可比较空间参考框架。",
        "repair_principle": "先声明和核验 CRS，再把需要共同运算的对象转换到合适的共同 CRS。",
        "recommended_actions": [
            "检查所有空间对象的 CRS 定义和坐标域。",
            "为缺失但可确定的 CRS 明确定义元数据；对不同 CRS 对象执行真实重投影。",
            "在空间运算前确认对象 bounds、单位和参考框架可比较。",
        ],
        "forbidden_actions": [
            "把缺失 CRS 的对象直接假定为目标 CRS。",
            "只改 CRS 标签而不执行必要的坐标转换。",
        ],
        "validation_checks": [
            "检查参与运算对象的 CRS 和坐标域一致或可比较。",
            "检查空间叠加、交集、距离或裁剪结果是否符合预期空间关系。",
        ],
        "success_criteria": [
            "统一参考框架后，空间关系和地图位置与任务预期一致。",
        ],
    },
    "A3. Unit Misinterpretation": {
        "repair_goal": "恢复距离、面积、长度、分辨率或密度等空间度量的单位语义。",
        "repair_principle": "度量计算必须在单位适合的 CRS 或明确换算后执行，并在输出中保持单位说明一致。",
        "recommended_actions": [
            "识别任务要求的度量单位和每个空间对象当前坐标单位。",
            "对米、公里、面积等度量使用合适投影或明确单位换算。",
            "在输出字段、图例和说明中同步记录度量单位。",
        ],
        "forbidden_actions": [
            "把 degree 空间中的数值直接解释为 meter 或 kilometer。",
            "混用面积、长度、密度单位而不做换算或说明。",
        ],
        "validation_checks": [
            "检查度量结果量级是否符合任务区域和单位。",
            "用参考计算或独立工具复核关键距离、面积或密度。",
        ],
        "success_criteria": [
            "输出数值可用任务声明的单位解释，且量级合理。",
        ],
    },
    "B1. Dataset Integrity Violation": {
        "repair_goal": "恢复 GIS 数据集的文件组件、元数据、属性结构和 schema 语义完整性。",
        "repair_principle": "把 GIS 数据作为带空间对象、属性和元数据约束的数据模型处理，而不是普通平面文件。",
        "recommended_actions": [
            "保留和传递 GIS 数据必需组件、空间元数据和属性 schema。",
            "按数据字典或嵌套结构读取字段，不把层级属性当作平铺字段。",
            "在输出前检查几何、属性、CRS 和关键字段是否完整。",
        ],
        "forbidden_actions": [
            "只复制或输出空间数据的一部分组件。",
            "在找不到字段时静默回退为 0、空值或默认类别。",
        ],
        "validation_checks": [
            "检查输出数据可被 GIS 软件或库重新读取。",
            "检查关键属性、几何和元数据是否仍可解释。",
        ],
        "success_criteria": [
            "输出数据保持任务所需的空间对象、属性和元数据语义。",
        ],
    },
    "B2. Raster Alignment Failure": {
        "repair_goal": "恢复栅格和相关空间对象之间的采样框架一致性。",
        "repair_principle": "栅格组合、比较、代数和区域统计前必须对齐空间采样框架。",
        "recommended_actions": [
            "核验参与运算数据的格网、空间变换、分辨率、空间范围和 band 语义。",
            "必要时执行重投影、重采样、裁剪、重网格化或窗口对齐。",
            "在栅格-矢量分析中确认矢量区域与栅格采样框架可共同解释。",
        ],
        "forbidden_actions": [
            "把 shape 相同但空间变换不同的数组当作同一位置像元。",
            "对未对齐栅格直接执行逐像元代数或变化检测。",
        ],
        "validation_checks": [
            "检查 transform、resolution、extent 和 band 语义是否匹配。",
            "检查叠加预览或空间模式是否存在系统错位。",
        ],
        "success_criteria": [
            "逐像元或区域统计结果在共同空间采样框架下可解释。",
        ],
    },
    "B3. Missing Data Misinterpretation": {
        "repair_goal": "恢复有效观测与 NoData、mask、背景或缺失状态之间的语义边界。",
        "repair_principle": "无效状态不得作为有效观测进入统计、分级、聚合或地图表达。",
        "recommended_actions": [
            "读取并传播 NoData、mask、缺失类别和不可观测区域语义。",
            "在统计和制图前显式排除或单独处理无效状态。",
            "区分真实 0 值与缺失值、背景值或屏蔽值。",
        ],
        "forbidden_actions": [
            "把 NoData 或背景值当作真实观测参与均值、总量或分类。",
            "把有效负类或真实 0 值错误声明为缺失。",
        ],
        "validation_checks": [
            "检查有效/无效像元或记录数量。",
            "检查统计结果是否被无效值主导或改变。",
        ],
        "success_criteria": [
            "输出统计和地图只基于任务定义的有效观测，缺失状态被正确标识或排除。",
        ],
    },
    "C1. Topological Predicate Confusion": {
        "repair_goal": "恢复自然语言空间关系与 GIS 拓扑/几何关系模型的一致性。",
        "repair_principle": "按任务关系语义选择等价空间谓词，不能用更宽或更窄的关系替代。",
        "recommended_actions": [
            "把任务中的关系词转换为明确的空间关系模型。",
            "检查边界接触、包含、穿越、重叠和相离等边界案例。",
            "用参考样例或可视化复核结果集合的包含/排除语义。",
        ],
        "forbidden_actions": [
            "用任意相交关系替代严格包含、穿越或邻接关系。",
            "忽略边界接触和内部包含之间的语义差异。",
        ],
        "validation_checks": [
            "检查结果集合是否符合任务关系边界。",
            "对少量边界对象人工或脚本验证空间关系。",
        ],
        "success_criteria": [
            "输出对象集合与任务要求的空间关系语义一致。",
        ],
    },
    "C2. Invalid Geometry Handling": {
        "repair_goal": "恢复几何对象参与空间运算所需的有效性前提。",
        "repair_principle": "空间运算前应检查、修复、过滤或隔离无效几何，避免无效结构污染结果。",
        "recommended_actions": [
            "检查输入和关键中间几何的有效性。",
            "对可修复几何执行等价修复，对不可修复几何记录并隔离。",
            "修复后重新执行空间叠加、裁剪、缓冲或聚合。",
        ],
        "forbidden_actions": [
            "忽略无效几何警告后继续解释输出。",
            "在不了解影响的情况下删除所有异常几何。",
        ],
        "validation_checks": [
            "检查修复后几何有效性和要素数量。",
            "检查输出是否仍有自交、空几何、碎片化或异常拓扑。",
        ],
        "success_criteria": [
            "空间运算能稳定完成，输出几何结构可解释。",
        ],
    },
    "C3. Network Connectivity Misinterpretation": {
        "repair_goal": "恢复路径、可达性、流向或网络距离所需的连通关系模型。",
        "repair_principle": "网络问题必须由节点、边、方向、阻抗和可达关系定义，不能由视觉接近或普通几何相交替代。",
        "recommended_actions": [
            "构建或读取明确的网络图结构。",
            "把起终点或设施位置关联到可通行网络元素。",
            "保留方向、阻抗、连通组件和路径约束。",
        ],
        "forbidden_actions": [
            "把欧氏距离直接当作网络距离。",
            "把线在地图上看起来接近或相交当作可通行连通。",
        ],
        "validation_checks": [
            "检查路径是否遵守网络连通、方向和阻抗。",
            "检查不可达对象是否被错误纳入可达范围。",
        ],
        "success_criteria": [
            "输出路径、距离或服务范围在网络图语义下成立。",
        ],
    },
    "D1. Aggregation Scope Confusion": {
        "repair_goal": "恢复任务指定的局部、分组、分区、时间片或条件范围。",
        "repair_principle": "分析结果必须在任务声明的范围边界内计算和解释。",
        "recommended_actions": [
            "识别任务要求的空间范围、分组字段、时间片或条件子集。",
            "在筛选、聚合和输出阶段保留这些范围边界。",
            "输出结果粒度应与任务要求一致。",
        ],
        "forbidden_actions": [
            "把每组或每区问题简化为单一全局统计。",
            "在聚合前丢失分组或局部上下文。",
        ],
        "validation_checks": [
            "检查输出记录数、分组覆盖和范围边界。",
            "抽查局部结果是否与对应范围内的数据一致。",
        ],
        "success_criteria": [
            "结果粒度和结论范围与任务定义一致。",
        ],
    },
    "D2. Spatial Allocation Error": {
        "repair_goal": "恢复变量在不同空间支持之间转移时的空间单元、变量类型和权重语义。",
        "repair_principle": "点、像元、面域、行政区或路段之间转移变量时，必须使用与变量类型相容的空间分配规则。",
        "recommended_actions": [
            "识别变量原始空间支持和目标空间支持。",
            "区分总量、比例、密度和类别变量的分配方式。",
            "使用面积权重、人口权重、面域统计或其他任务合理的转移规则。",
        ],
        "forbidden_actions": [
            "用单一点值代表整个面域。",
            "把总量、比例和密度用同一种复制、求和或平均规则处理。",
            "用无关代理变量替代目标变量。",
        ],
        "validation_checks": [
            "检查输出变量是否仍代表任务声称的空间单元。",
            "检查分配权重或面域统计是否符合变量类型。",
            "与参考统计或独立重算结果比较关键排名和空间模式。",
        ],
        "success_criteria": [
            "目标空间单元上的变量含义与任务要求一致，关键统计或空间模式可复核。",
        ],
    },
    "D3. Spatial Statistical Misinterpretation": {
        "repair_goal": "恢复空间统计指标、派生变量、阈值、显著性和局部/全局解释的一致性。",
        "repair_principle": "统计结论必须由正确变量定义、分母、阈值和解释前提支撑。",
        "recommended_actions": [
            "明确统计指标、分母、阈值、时间差分和显著性定义。",
            "按任务定义构造派生变量和筛选条件。",
            "区分局部统计、全局统计、原始计数、比例和率。",
        ],
        "forbidden_actions": [
            "把原始计数标注为百分比或率。",
            "跳过任务要求的阈值或显著性判断。",
            "用全局统计结论替代局部空间解释。",
        ],
        "validation_checks": [
            "检查公式、分母、阈值和单位说明。",
            "检查统计变量和地图/表格标签是否一致。",
        ],
        "success_criteria": [
            "输出结论可由任务定义的统计变量和阈值复现。",
        ],
    },
    "E1. Classification Scheme Misuse": {
        "repair_goal": "恢复专题地图数值分级与数据分布、任务比较目的和类别语义的一致性。",
        "repair_principle": "分类方案应服务于任务解释目标，并与变量分布和类别数量要求相容。",
        "recommended_actions": [
            "确认任务是否要求特定分类方法、类别数量或阈值。",
            "根据数据分布和比较目的选择合适分级方案。",
            "记录类别区间和每类覆盖情况。",
        ],
        "forbidden_actions": [
            "忽略任务指定类别数量或阈值。",
            "使用会掩盖主要空间差异的分级方案。",
        ],
        "validation_checks": [
            "检查分类区间、类别数量和每类样本分布。",
            "检查地图是否支持任务要求的空间比较。",
        ],
        "success_criteria": [
            "读者能通过分级结果正确比较任务关心的空间差异。",
        ],
    },
    "E2. Symbolization Error": {
        "repair_goal": "恢复视觉变量与数据类型、类别身份、顺序、强度或数量语义的一致性。",
        "repair_principle": "地图符号应让读者获得与数据语义一致的视觉解释。",
        "recommended_actions": [
            "识别变量是名义、序数、连续、强度、方向还是数量。",
            "选择与数据语义相容的颜色、大小、形状、线型或透明度。",
            "确保类别可区分，顺序和强度表达不产生误导。",
        ],
        "forbidden_actions": [
            "用连续梯度暗示无序类别有大小关系。",
            "用难以区分或重复的视觉变量表达不同类别。",
        ],
        "validation_checks": [
            "检查图例和视觉编码是否与数据类型一致。",
            "检查读者是否能区分类别、顺序或强度。",
        ],
        "success_criteria": [
            "地图视觉解释与数据语义和任务目的一致。",
        ],
    },
    "E3. Map Composition Defect": {
        "repair_goal": "恢复读者理解地图主题所需的完整解释链。",
        "repair_principle": "地图交付物必须包含解释主题、空间上下文和符号含义所需的构成要素。",
        "recommended_actions": [
            "确认任务要求的地图输出、主题内容、空间上下文和解释要素。",
            "补齐必要图层、图例、标签、比例尺、标题、布局或交付文件。",
            "确保地图构成要素与任务主题一致且可读。",
        ],
        "forbidden_actions": [
            "只输出数据表或中间图层而缺少任务要求的地图交付物。",
            "遗漏理解主题所必需的上下文或解释要素。",
        ],
        "validation_checks": [
            "检查最终交付物是否包含任务要求的地图和解释要素。",
            "检查读者能否从地图直接理解主题对象、符号含义和空间上下文。",
        ],
        "success_criteria": [
            "最终地图能独立支持任务要求的空间理解和主题解释。",
        ],
    },
}


NEIGHBOR_LABELS: dict[str, list[str]] = {
    "A1. Coordinate Axis Misinterpretation": ["A2. CRS Inconsistency", "A3. Unit Misinterpretation"],
    "A2. CRS Inconsistency": ["A1. Coordinate Axis Misinterpretation", "A3. Unit Misinterpretation", "B1. Dataset Integrity Violation"],
    "A3. Unit Misinterpretation": ["A2. CRS Inconsistency", "D2. Spatial Allocation Error"],
    "B1. Dataset Integrity Violation": ["A2. CRS Inconsistency", "C2. Invalid Geometry Handling", "D3. Spatial Statistical Misinterpretation"],
    "B2. Raster Alignment Failure": ["A2. CRS Inconsistency", "B3. Missing Data Misinterpretation", "D2. Spatial Allocation Error"],
    "B3. Missing Data Misinterpretation": ["B1. Dataset Integrity Violation", "D3. Spatial Statistical Misinterpretation", "E1. Classification Scheme Misuse"],
    "C1. Topological Predicate Confusion": ["C2. Invalid Geometry Handling", "C3. Network Connectivity Misinterpretation", "D1. Aggregation Scope Confusion"],
    "C2. Invalid Geometry Handling": ["B1. Dataset Integrity Violation", "C1. Topological Predicate Confusion", "A2. CRS Inconsistency"],
    "C3. Network Connectivity Misinterpretation": ["C1. Topological Predicate Confusion", "A3. Unit Misinterpretation", "D1. Aggregation Scope Confusion"],
    "D1. Aggregation Scope Confusion": ["C1. Topological Predicate Confusion", "D2. Spatial Allocation Error", "D3. Spatial Statistical Misinterpretation"],
    "D2. Spatial Allocation Error": ["D1. Aggregation Scope Confusion", "D3. Spatial Statistical Misinterpretation", "A3. Unit Misinterpretation"],
    "D3. Spatial Statistical Misinterpretation": ["B1. Dataset Integrity Violation", "D2. Spatial Allocation Error", "E1. Classification Scheme Misuse", "E2. Symbolization Error"],
    "E1. Classification Scheme Misuse": ["B3. Missing Data Misinterpretation", "D3. Spatial Statistical Misinterpretation", "E2. Symbolization Error"],
    "E2. Symbolization Error": ["D3. Spatial Statistical Misinterpretation", "E1. Classification Scheme Misuse", "E3. Map Composition Defect"],
    "E3. Map Composition Defect": ["D1. Aggregation Scope Confusion", "D2. Spatial Allocation Error", "D3. Spatial Statistical Misinterpretation", "E2. Symbolization Error"],
}


SECTION_PATTERNS = {
    "task_intent": r"##\s*1[.．、]\s*任务目标",
    "workflow": r"##\s*2[.．、]\s*任务执行工作流",
    "error_location": r"##\s*3[.．、]\s*错误发生位置",
    "mechanism": r"##\s*4[.．、]\s*错误机制与结果影响",
    "evidence": r"##\s*5[.．、]\s*具体错误证据",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def compact_text(text: str, max_chars: int = 700) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[: max_chars - 1].rstrip() + "…" if len(text) > max_chars else text


def section(markdown: str, pattern: str) -> str:
    match = re.search(pattern, markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+", markdown[start:])
    end = start + next_heading.start() if next_heading else len(markdown)
    return compact_text(markdown[start:end])


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def annotation_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in ROOT.glob("[A-E]_*/*/*/annotation.json"):
        data = load_json(path)
        index[data["sample_id"]] = path
    return index


def evidence_readme_path(sample_dir: Path, annotation: dict[str, Any]) -> Path | None:
    evidence_name = annotation.get("evidence_readme") or "README.md"
    return first_existing([
        sample_dir / "evidence" / evidence_name,
        sample_dir / "evidence" / "README.md",
        sample_dir / evidence_name,
    ])


def evidence_types(sample_dir: Path, annotation: dict[str, Any]) -> list[str]:
    types: set[str] = set()
    if annotation.get("evidence_metrics"):
        types.add("data")
    if annotation.get("result_previews") or annotation.get("reference_preview_file"):
        types.add("visual")
    if (sample_dir / "execution_result" / "workflow").exists():
        types.add("workflow")
    if (sample_dir / "run_log").exists():
        types.add("log")
    workflow_dir = sample_dir / "execution_result" / "workflow"
    if any((workflow_dir / name).exists() for name in ["code.py", "generated_code.py", "model_response.txt", "generated_solution.json"]):
        types.add("code")
    return sorted(types)


def summarize_metrics(metrics: Any, max_items: int = 10) -> str:
    if not isinstance(metrics, dict) or not metrics:
        return ""
    parts: list[str] = []
    for key, value in metrics.items():
        if len(parts) >= max_items:
            break
        if isinstance(value, (str, int, float, bool)) or value is None:
            parts.append(f"{key}={value}")
        elif isinstance(value, list):
            parts.append(f"{key}[{len(value)}]")
        elif isinstance(value, dict):
            parts.append(f"{key}{{{len(value)}}}")
    return "; ".join(parts)


def preview_assets(sample_dir: Path, annotation: dict[str, Any]) -> dict[str, Any]:
    result_previews: list[str] = []
    for preview in annotation.get("result_previews", []):
        preview_file = preview.get("preview_file")
        if not preview_file:
            continue
        candidates = [
            sample_dir / "execution_result" / preview_file,
            sample_dir / preview_file,
        ]
        existing = first_existing(candidates)
        result_previews.append(rel(existing if existing else candidates[0]))

    reference_preview = ""
    if annotation.get("reference_preview_file"):
        candidates = [
            sample_dir / "evidence" / annotation["reference_preview_file"],
            sample_dir / annotation["reference_preview_file"],
        ]
        existing = first_existing(candidates)
        reference_preview = rel(existing if existing else candidates[0])

    readme_path = evidence_readme_path(sample_dir, annotation)
    return {
        "evidence_readme": rel(readme_path) if readme_path else "",
        "result_previews": result_previews,
        "reference_preview": reference_preview,
    }


def retrieval_tags(label: str, annotation: dict[str, Any], evidence_kinds: list[str]) -> list[str]:
    tags = set(LABEL_TAGS.get(label, []))
    for secondary in annotation.get("secondary_labels", []):
        tags.update(LABEL_TAGS.get(secondary, []))
    tags.update(kind for kind in evidence_kinds)
    tags.add(annotation.get("sample_origin", "unknown"))
    return sorted(tags)


def rule_neighbor_hint(rule_cards: dict[str, Any], label: str) -> str:
    for rule in rule_cards.get("rules", []):
        if rule.get("label") != label:
            continue
        axes = rule.get("diagnostic_axes", [])
        for axis in axes:
            if axis.startswith("neighbor_disambiguation:"):
                return axis.split(":", 1)[1].strip()
    neighbors = ", ".join(NEIGHBOR_LABELS.get(label, []))
    return f"重点与相邻类别区分：{neighbors}" if neighbors else "需要根据标注指南与相邻类别做互斥判断。"


def build_record(manifest_entry: dict[str, Any], annotation_path: Path, rule_cards: dict[str, Any]) -> dict[str, Any]:
    annotation = load_json(annotation_path)
    sample_dir = annotation_path.parent
    readme_path = evidence_readme_path(sample_dir, annotation)
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path else ""
    label = annotation["primary_label"]
    repair = REPAIR_TEMPLATES[label]
    kinds = evidence_types(sample_dir, annotation)

    task_intent = section(readme_text, SECTION_PATTERNS["task_intent"]) or "详见原样本任务描述与 evidence README。"
    workflow = section(readme_text, SECTION_PATTERNS["workflow"])
    error_location = section(readme_text, SECTION_PATTERNS["error_location"])
    mechanism = section(readme_text, SECTION_PATTERNS["mechanism"]) or annotation.get("error_summary", "")
    evidence = section(readme_text, SECTION_PATTERNS["evidence"]) or annotation.get("error_summary", "")
    metrics_summary = summarize_metrics(annotation.get("evidence_metrics"))
    neighbor_hint = rule_neighbor_hint(rule_cards, label)

    retrieval_bits = [
        label,
        "secondary=" + ", ".join(annotation.get("secondary_labels", [])),
        "task=" + task_intent,
        "error=" + annotation.get("error_summary", ""),
        "mechanism=" + mechanism,
        "evidence=" + evidence,
        "repair_principle=" + repair["repair_principle"],
    ]
    retrieval_text = compact_text(" | ".join(bit for bit in retrieval_bits if bit), 1400)

    return {
        "schema_version": "0.1.0",
        "case_status": "verified",
        "sample_id": annotation["sample_id"],
        "sample_path": rel(sample_dir),
        "source": annotation.get("source", manifest_entry.get("source", "")),
        "sample_origin": annotation.get("sample_origin", manifest_entry.get("sample_origin", "")),
        "primary_label": label,
        "secondary_labels": annotation.get("secondary_labels", []),
        "task_intent": task_intent,
        "error_signature": annotation.get("error_summary", ""),
        "root_cause": mechanism,
        "error_location": error_location,
        "why_this_label": f"主标签为 {label}，因为该案例的核心错误机制是：{mechanism}",
        "why_not_neighbor_labels": neighbor_hint,
        "retrieval_tags": retrieval_tags(label, annotation, kinds),
        "retrieval_text": retrieval_text,
        "evidence": {
            "minimal_evidence": evidence,
            "evidence_types": kinds,
            "key_metrics_summary": metrics_summary,
            "workflow_summary": workflow,
            "assets": preview_assets(sample_dir, annotation),
        },
        "repair_playbook": repair,
    }


def validate_records(records: list[dict[str, Any]]) -> None:
    labels = {record["primary_label"] for record in records}
    manifest_labels = {entry["primary_label"] for entry in load_json(MANIFEST_PATH)}
    if len(records) != len(load_json(MANIFEST_PATH)):
        raise RuntimeError("Case KB record count does not match manifest count.")
    if labels != manifest_labels:
        missing = sorted(manifest_labels - labels)
        extra = sorted(labels - manifest_labels)
        raise RuntimeError(f"Label coverage mismatch. missing={missing}, extra={extra}")
    for record in records:
        assets = record["evidence"]["assets"]
        required_paths = [record["sample_path"]]
        if assets.get("evidence_readme"):
            required_paths.append(assets["evidence_readme"])
        if assets.get("reference_preview"):
            required_paths.append(assets["reference_preview"])
        required_paths.extend(assets.get("result_previews", []))
        for rel_path in required_paths:
            if rel_path and not (ROOT / rel_path).exists():
                raise RuntimeError(f"Missing path for {record['sample_id']}: {rel_path}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n")


def build_index(records_by_category: dict[str, list[dict[str, Any]]], total_cases: int) -> dict[str, Any]:
    category_index = {}
    for category, info in CATEGORY_OUTPUTS.items():
        records = records_by_category.get(category, [])
        category_index[category] = {
            "name": info["name"],
            "description": info["description"],
            "path": rel(info["path"]),
            "count": len(records),
            "labels": sorted({record["primary_label"] for record in records}),
        }
    return {
        "schema_version": "0.1.0",
        "source_of_truth": "sample directories and manifest.json",
        "generated_by": "tools/build_case_kb.py",
        "rule_cards": rel(RULE_CARDS_PATH),
        "annotation_guide": "GIS_WORKFLOW_ERROR_ANNOTATION_GUIDE.md",
        "all_cases": rel(CASE_KB_PATH),
        "candidate_cases": rel(CANDIDATE_KB_PATH),
        "total_cases": total_cases,
        "by_category": category_index,
        "retrieval_policy": [
            "Use rule cards and the annotation guide to generate candidate labels first.",
            "Filter by the candidate label's A-E major category before searching retrieval_text.",
            "Fallback to all_cases.jsonl only when the major category is uncertain.",
            "Do not include candidates.jsonl in verified retrieval unless unverified feedback is explicitly allowed.",
        ],
    }


def main() -> None:
    manifest = load_json(MANIFEST_PATH)
    annotations = annotation_index()
    rule_cards = load_json(RULE_CARDS_PATH) if RULE_CARDS_PATH.exists() else {"rules": []}
    records = []
    for entry in manifest:
        sample_id = entry["sample_id"]
        if sample_id not in annotations:
            raise RuntimeError(f"Missing annotation for {sample_id}")
        records.append(build_record(entry, annotations[sample_id], rule_cards))

    validate_records(records)
    records_by_category = {category: [] for category in CATEGORY_OUTPUTS}
    for record in records:
        category = record["primary_label"][0]
        if category not in records_by_category:
            raise RuntimeError(f"Unknown major category for {record['sample_id']}: {record['primary_label']}")
        records_by_category[category].append(record)

    write_jsonl(CASE_KB_PATH, records)
    for category, category_records in records_by_category.items():
        write_jsonl(CATEGORY_OUTPUTS[category]["path"], category_records)

    if not CANDIDATE_KB_PATH.exists():
        CANDIDATE_KB_PATH.parent.mkdir(parents=True, exist_ok=True)
        CANDIDATE_KB_PATH.write_text("", encoding="utf-8")
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(build_index(records_by_category, len(records)), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"wrote {len(records)} verified cases to {rel(CASE_KB_PATH)}")
    for category, category_records in records_by_category.items():
        print(f"wrote {len(category_records)} {category} cases to {rel(CATEGORY_OUTPUTS[category]['path'])}")
    print(f"candidate pool: {rel(CANDIDATE_KB_PATH)}")
    print(f"index: {rel(INDEX_PATH)}")


if __name__ == "__main__":
    main()
