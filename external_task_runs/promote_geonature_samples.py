import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATASET_ROOT = ROOT.parent
DATA_ROOT = ROOT / "data" / "geonature"
RUNS_ROOT = ROOT / "runs"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sanitize_text(text: str) -> str:
    replacements = {
        r"<LOCAL_REPO_ROOT>\external_task_runs\data\geonature": "data_source",
        r"<LOCAL_REPO_ROOT>": "<WORKSPACE>",
        r"<LOCAL_PYTHON_ENV>": "<PYTHON_ENV>",
        "<LOCAL_REPO_ROOT>/external_task_runs/data/geonature": "data_source",
        "<LOCAL_REPO_ROOT>": "<WORKSPACE>",
        "https://api.deepseek.com/v1": "<REDACTED>",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def sanitize_code(sample_id: str, code: str) -> str:
    code = sanitize_text(code)
    if sample_id == "geonature_forest_cover_rank_bigearthnet_b1":
        code = code.replace('data_path = r"data_source\\bigearthnet_portugal_stats.json"', 'data_path = r"data_source\\bigearthnet_portugal_stats.json"')
    elif sample_id == "geonature_co2_candidate_pool_d3":
        code = code.replace('DATA_DIR = Path(r"data_source")', 'DATA_DIR = Path("data_source")')
    elif sample_id == "geobenchx_murcia_50km_buffer_c2":
        code = code.replace('path = "data_source/spain_provinces.geojson"', 'path = "data_source/spain_provinces.geojson"')
    return code


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_text_sanitized(src: Path, dst: Path, sample_id: str | None = None, code: bool = False) -> None:
    text = read_text(src)
    text = sanitize_code(sample_id or "", text) if code else sanitize_text(text)
    write_text(dst, text)


def checksum_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(sample_dir: Path) -> None:
    lines = []
    for path in sorted(sample_dir.rglob("*")):
        if path.is_file() and path.name != "checksums.sha256":
            rel = path.relative_to(sample_dir).as_posix()
            lines.append(f"{checksum_file(path)}  {rel}")
    write_text(sample_dir / "checksums.sha256", "\n".join(lines) + "\n")


def clean_sample_dir(sample_dir: Path) -> None:
    resolved_root = DATASET_ROOT.resolve()
    resolved_sample = sample_dir.resolve()
    if not resolved_sample.is_relative_to(resolved_root):
        raise RuntimeError(f"Refusing to clean path outside dataset root: {resolved_sample}")
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
    sample_dir.mkdir(parents=True)


def make_config(sample: dict) -> str:
    return f"""[experiment]
source = {sample["source"]}
experiment = external_geonature_direct_request
backend = standalone_openai_compatible_runner
framework = {sample["framework"]}
model = deepseek-v4-pro
provider = DeepSeek
reasoning = direct request; thinking flag not separately exposed
api_key = <REDACTED>
base_url = <REDACTED>
"""


def make_provenance(sample: dict) -> dict:
    return {
        "source": sample["source"],
        "source_project": sample["framework"],
        "paper_case_id": sample["paper_case_id"],
        "snapshot": "sanitized external run package",
        "note": "密钥、服务端点和本机绝对路径已隐去；原始复现运行保存在 external_task_runs/runs。",
    }


def make_task_md(sample: dict) -> str:
    data_files = "\n".join(f"- `{name}`" for name in sample["data_files"])
    outputs = "\n".join(f"- `{name}`" for name in sample["required_outputs"])
    return f"""# {sample["source"]}

- 任务编号：{sample["task_id"]}
- 论文/项目任务编号：{sample["paper_case_id"]}
- LLM 配置：deepseek-v4-pro
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：{sample["framework"]}
- 难度：{sample["difficulty"]}
- 空间方法：{sample["method_family"]}

## 任务描述

{sample["task"]}

## 本地输入数据

{data_files}

## 任务要求输出

{outputs}
"""


def image_link(path: str, alt: str) -> str:
    return f"![{alt}]({path})"


def make_evidence_readme(sample: dict, audit: dict) -> str:
    preview_section = sample["preview_section"]
    reference_section = sample["reference_section"]
    metrics = json.dumps(sample["evidence_metrics"](audit), ensure_ascii=False, indent=2)
    return f"""# GIS 错误证据：{sample["source"]}

- 主标签：{sample["primary_label"]}
- 次标签：{", ".join(sample["secondary_labels"]) if sample["secondary_labels"] else "无"}
- LLM 配置：deepseek-v4-pro（DeepSeek）
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：{sample["framework"]}
- 难度：{sample["difficulty"]}

## 1. 任务目标

{sample["task_goal"]}

## 2. 任务执行工作流

{sample["workflow_text"]}

## 3. 错误发生位置

{sample["error_location"]}

## 4. 错误机制与结果影响

{sample["error_mechanism"]}

## 5. 具体错误证据

```json
{metrics}
```

## 6. 任务执行结果预览

{preview_section}

## 7. 解决错误后 GIS 任务应有的结果预览

{reference_section}

## 8. 可视化判读说明

本案例的关键证据是生成代码、运行日志、错误输出表和参考结果之间的差异。图片只作为空间分析或分类统计结果的可视化辅助，最终判定以第 5 节列出的数值与代码证据为准。
"""


def run_record(sample: dict, audit: dict) -> dict:
    metadata = json.loads((sample["run_dir"] / "metadata.json").read_text(encoding="utf-8"))
    return {
        "source_run": sample["run_dir"].name,
        "status": metadata.get("status"),
        "execution_returncode": metadata.get("execution_returncode"),
        "missing_required_outputs": metadata.get("missing_required_outputs", []),
        "task_id": metadata.get("task_id"),
        "model": metadata.get("model"),
        "method_family": metadata.get("method_family"),
        "difficulty": metadata.get("difficulty"),
        "audit_summary": audit,
    }


def promote_sample(sample: dict) -> dict:
    sample_dir = DATASET_ROOT / sample["category_dir"] / sample["sample_id"]
    clean_sample_dir(sample_dir)
    audit = json.loads((sample["run_dir"] / "audit_summary.json").read_text(encoding="utf-8"))

    for data_file in sample["data_files"]:
        copy_file(DATA_ROOT / data_file, sample_dir / "data_source" / data_file)

    copy_text_sanitized(sample["run_dir"] / "generated_code.py", sample_dir / "execution_result" / "workflow" / "generated_code.py", sample["sample_id"], code=True)
    copy_text_sanitized(sample["run_dir"] / "model_response.txt", sample_dir / "execution_result" / "workflow" / "model_response.txt")
    copy_text_sanitized(sample["run_dir"] / "prompt.txt", sample_dir / "execution_result" / "workflow" / "prompt.txt")
    copy_text_sanitized(sample["run_dir"] / "run.log", sample_dir / "run_log" / "run.log")

    for artifact in sample["artifacts"]:
        copy_file(sample["run_dir"] / artifact, sample_dir / "execution_result" / "artifacts" / artifact)
    for preview in sample["previews"]:
        copy_file(sample["run_dir"] / preview, sample_dir / "execution_result" / "previews" / preview)
    for reference_src, reference_dst in sample["references"]:
        copy_file(sample["run_dir"] / reference_src, sample_dir / "evidence" / reference_dst)

    write_json(sample_dir / "execution_result" / "run_record.json", run_record(sample, audit))
    write_text(sample_dir / "llm_config" / "config.ini", make_config(sample))
    write_json(sample_dir / "llm_config" / "provenance.json", make_provenance(sample))
    write_text(sample_dir / "task.md", make_task_md(sample))
    write_text(sample_dir / "evidence" / "README.md", make_evidence_readme(sample, audit))
    write_json(sample_dir / "evidence" / "reference_metrics.json", sample["evidence_metrics"](audit))

    annotation = {
        "sample_id": sample["sample_id"],
        "source": sample["source"],
        "task_id": sample["task_id"],
        "sample_origin": "observed_run",
        "llm_configuration": {
            "primary_model": "deepseek-v4-pro",
            "provider": "DeepSeek",
            "reasoning": "direct request；thinking 开关未单列记录",
            "framework": sample["framework"],
        },
        "primary_label": sample["primary_label"],
        "secondary_labels": sample["secondary_labels"],
        "error_summary": sample["error_summary"],
        "result_previews": sample["result_previews"],
        "reference_preview_file": "reference.png",
        "evidence_readme": "README.md",
        "reference_basis": sample["reference_basis"],
        "evidence_metrics": sample["evidence_metrics"](audit),
    }
    write_json(sample_dir / "annotation.json", annotation)
    write_checksums(sample_dir)
    return annotation


def update_manifest(annotations: list[dict]) -> None:
    manifest_json = DATASET_ROOT / "manifest.json"
    rows = json.loads(manifest_json.read_text(encoding="utf-8"))
    by_id = {row["sample_id"]: row for row in rows}
    for annotation in annotations:
        by_id[annotation["sample_id"]] = {
            "sample_id": annotation["sample_id"],
            "source": annotation["source"],
            "task_id": annotation["task_id"],
            "sample_origin": annotation["sample_origin"],
            "primary_label": annotation["primary_label"],
            "secondary_labels": annotation["secondary_labels"],
            "llm_model": annotation["llm_configuration"]["primary_model"],
            "provider": annotation["llm_configuration"]["provider"],
            "reasoning": annotation["llm_configuration"]["reasoning"],
            "error_summary": annotation["error_summary"],
        }
    updated = list(by_id.values())
    write_json(manifest_json, updated)

    manifest_csv = DATASET_ROOT / "manifest.csv"
    fieldnames = [
        "sample_id",
        "source",
        "task_id",
        "sample_origin",
        "primary_label",
        "secondary_labels",
        "llm_model",
        "provider",
        "reasoning",
        "error_summary",
    ]
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in updated:
            serializable = row.copy()
            serializable["secondary_labels"] = "; ".join(row.get("secondary_labels", []))
            writer.writerow(serializable)


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected text not found: {old}")
    return text.replace(old, new, 1)


def update_docs() -> None:
    manifest = json.loads((DATASET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    total = len(manifest)
    observed = sum(1 for row in manifest if row["sample_origin"] == "observed_run")
    research = sum(1 for row in manifest if row["sample_origin"] == "research_supplement")

    readme_path = DATASET_ROOT / "README.md"
    readme = read_text(readme_path)
    readme = replace_once(readme, "本版包含 **62** 个 GIS 错误样本", f"本版包含 **{total}** 个 GIS 错误样本")
    readme = replace_once(
        readme,
        "LLM-Geo 外部论文复现运行 3 次，其中 2 次进入主样本；2 个 taxonomy 补齐样本来自论文研究与 GIS 专业经验。",
        "LLM-Geo、GeoNatureAgent 与 GeoBenchX 定向外部论文复现运行 10 次，其中 5 次进入主样本；2 个 taxonomy 补齐样本来自论文研究与 GIS 专业经验。",
    )
    write_text(readme_path, readme)

    run_audit_path = DATASET_ROOT / "RUN_AUDIT.md"
    audit = read_text(run_audit_path)
    audit = replace_once(
        audit,
        "- 外部论文复现记录：3（LLM-Geo direct request），其中 2 条经 GIS 审计进入主样本，见 `external_task_runs/runs/targeted_low_count_audit_20260709_1630.json`。",
        "- 外部论文复现记录：10（LLM-Geo 3 条，GeoNatureAgent/GeoBenchX 7 条），其中 5 条经 GIS 审计进入主样本；GeoNature/GeoBenchX 审计见 `external_task_runs/geonature_audit_summary.json`。",
    )
    audit = replace_once(audit, "- observed_run 样本：60", f"- observed_run 样本：{observed}")
    audit = replace_once(audit, "- research_supplement 样本：2", f"- research_supplement 样本：{research}")
    audit = replace_once(
        audit,
        "| LLM-Geo Axis_order_SC_hospitals | C2. Invalid Geometry Handling | direct request；thinking 开关未单列记录 |",
        "| LLM-Geo Axis_order_SC_hospitals | C2. Invalid Geometry Handling | direct request；thinking 开关未单列记录 |\n| GeoBenchX/GeoNature Murcia 50km Buffer | C2. Invalid Geometry Handling | direct request；thinking 开关未单列记录 |",
    )
    audit = replace_once(
        audit,
        "| GeoAgent Task 119 | D3. Spatial Statistical Misinterpretation | thinking 开关未单列记录 |",
        "| GeoAgent Task 119 | D3. Spatial Statistical Misinterpretation | thinking 开关未单列记录 |\n| GeoNatureAgent CO2 Candidate Pool Comparison | D3. Spatial Statistical Misinterpretation | direct request；thinking 开关未单列记录 |",
    )
    audit = replace_once(
        audit,
        "| GeoAgent Task 83 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |",
        "| GeoAgent Task 83 | B1. Dataset Integrity Violation | thinking 开关未单列记录 |\n| GeoNatureAgent BigEarthNet Forest Cover Rank | B1. Dataset Integrity Violation | direct request；thinking 开关未单列记录 |",
    )
    write_text(run_audit_path, audit)

    coverage_path = DATASET_ROOT / "configuration_coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["geonature-deepseek-v4-pro-direct"] = 3
    write_json(coverage_path, coverage)

    external_path = ROOT / "README.md"
    external = read_text(external_path)
    if "## GeoNatureAgent / GeoBenchX Runs" not in external:
        external += """

## GeoNatureAgent / GeoBenchX Runs

`geonature_runner.py` adapts selected GeoNatureAgent Benchmark and GeoBenchX-style tasks using local JSON/GeoJSON data copied into `external_task_runs/data/geonature`.

Promoted GIS-error cases:

| Run | Outcome | Dataset sample |
| --- | --- | --- |
| `20260709_171038_gn_v5_62_forest_cover_rank_bigearthnet_deepseek-v4-pro` | Completed with all forest cover values incorrectly written as zero. | `B_Spatial_Data_Errors\\B1_Dataset_Integrity_Violation\\geonature_forest_cover_rank_bigearthnet_b1` |
| `20260709_171112_gn_v5_21_compare_co2_candidate_pool_deepseek-v4-pro` | Completed with zero candidate-pool values and an incorrect Equal decision. | `D_Spatial_Analysis_Errors\\D3_Spatial_Statistical_Misinterpretation\\geonature_co2_candidate_pool_d3` |
| `20260709_171537_gbx_port_murcia_50km_buffer_intersections_deepseek-v4-pro` | Failed on degenerate rings in the province GeoJSON before buffering. | `C_Spatial_Reasoning_Errors\\C2_Invalid_Geometry_Handling\\geobenchx_murcia_50km_buffer_c2` |

Excluded from the main GIS taxonomy:

- `gn_v5_31_habitat_beja_lulc`: schema/read failure; retained only as an auxiliary run.
- `gn_v5_44_andalucia_average_co2`: Windows UTF-8 decoding failure.
- `gn_v5_49_threshold_co2_high`: nested-schema lookup failure without a GIS result artifact.
- `gn_v5_50_dual_indicator_high_priority`: API chunked-encoding interruption.
"""
    write_text(external_path, external)


def sample_specs() -> list[dict]:
    forest_run = RUNS_ROOT / "20260709_171038_gn_v5_62_forest_cover_rank_bigearthnet_deepseek-v4-pro"
    co2_run = RUNS_ROOT / "20260709_171112_gn_v5_21_compare_co2_candidate_pool_deepseek-v4-pro"
    buffer_run = RUNS_ROOT / "20260709_171537_gbx_port_murcia_50km_buffer_intersections_deepseek-v4-pro"

    return [
        {
            "sample_id": "geonature_forest_cover_rank_bigearthnet_b1",
            "category_dir": "B_Spatial_Data_Errors/B1_Dataset_Integrity_Violation",
            "source": "GeoNatureAgent BigEarthNet Forest Cover Rank",
            "framework": "GeoNatureAgent Benchmark",
            "paper_case_id": "V5_62_list_layers_habitat_years",
            "task_id": "gn_v5_62_forest_cover_rank_bigearthnet",
            "difficulty": "hard",
            "method_family": "categorical LULC aggregation and ranking",
            "task": "Create a chart ranking Beja, Faro, Lisboa, and Portalegre by their total forest cover (coniferous + broadleaf) using the BigEarthNet data.",
            "task_goal": "按 BigEarthNet 土地覆盖分类统计结构，将 Coniferous Forest 与 Broadleaf Forest 合并为森林覆盖率，并对四个葡萄牙 district 排名和制图。",
            "primary_label": "B1. Dataset Integrity Violation",
            "secondary_labels": [],
            "reference_basis": "依据 BigEarthNet LULC breakdown 数据结构中 class 1 Coniferous Forest 与 class 2 Broadleaf Forest 的百分比独立计算",
            "error_summary": "生成代码没有进入 BigEarthNet 的 `breakdown` 分类统计结构读取 class 1/2，而是把 district 顶层字典当作平铺类别字段，导致四个地区森林覆盖率全部为 0、排名全部为 1，破坏了 LULC 分类属性语义与空间单元排名结果。",
            "workflow_text": "1. 读取 BigEarthNet Portugal district 统计 JSON。\n2. 代码尝试在 district 顶层直接查找 `1`、`2`、`Coniferous Forest`、`Broadleaf Forest`。\n3. 未读取 `breakdown` 列表中的类别标签和百分比。\n4. 将缺失字段回退为 0 后生成 CSV、JSON 和柱状图。",
            "error_location": "错误发生在 `execution_result/workflow/generated_code.py` 的森林覆盖提取逻辑。BigEarthNet LULC 分类信息位于 `breakdown` 列表，每个类别有 `value`、`label`、`percentage`；生成代码却把顶层 JSON 当作平铺类别字段。",
            "error_mechanism": "这是空间数据结构与属性语义误读：BigEarthNet 的 LULC 统计不是平铺字段，而是 `breakdown` 中带 `value`、`label`、`percentage` 的分类记录。森林覆盖应由 class 1 Coniferous Forest 与 class 2 Broadleaf Forest 的百分比相加；错误运行虽然生成了图表，但图表表达的是全零值，掩盖了 Portalegre、Lisboa、Faro、Beja 的真实差异。",
            "preview_section": image_link("../execution_result/previews/forest_cover_rank_chart.png", "错误运行森林覆盖排名图"),
            "reference_section": image_link("reference.png", "修正后森林覆盖排名参考图"),
            "run_dir": forest_run,
            "data_files": ["bigearthnet_portugal_stats.json"],
            "required_outputs": ["forest_cover_rank.csv", "forest_cover_rank.json", "forest_cover_rank_chart.png"],
            "artifacts": ["forest_cover_rank.csv", "forest_cover_rank.json"],
            "previews": ["forest_cover_rank_chart.png"],
            "references": [
                (Path("reference/forest_cover_rank_reference.png"), Path("reference.png")),
                (Path("reference/forest_cover_rank_reference.csv"), Path("forest_cover_rank_reference.csv")),
                (Path("reference/forest_cover_rank_reference.json"), Path("forest_cover_rank_reference.json")),
            ],
            "result_previews": [
                {
                    "source_artifact": "previews/forest_cover_rank_chart.png",
                    "stage": "最终成果",
                    "preview_file": "previews/forest_cover_rank_chart.png",
                    "description": "错误运行生成的森林覆盖排名柱状图，四个 district 均为 0。"
                }
            ],
            "evidence_metrics": lambda audit: {
                "observed_zero_forest_rows": audit["observed_zero_forest_rows"],
                "all_observed_values_zero": audit["all_observed_values_zero"],
                "expected_top_district": audit["expected_top_district"],
                "expected_top_forest_cover_pct": audit["expected_top_forest_cover_pct"],
                "reference_records": audit["reference_records"],
                "observed_records": audit["observed_records"],
            },
        },
        {
            "sample_id": "geonature_co2_candidate_pool_d3",
            "category_dir": "D_Spatial_Analysis_Errors/D3_Spatial_Statistical_Misinterpretation",
            "source": "GeoNatureAgent CO2 Candidate Pool Comparison",
            "framework": "GeoNatureAgent Benchmark",
            "paper_case_id": "V5_21_comparison_close_values",
            "task_id": "gn_v5_21_compare_co2_candidate_pool",
            "difficulty": "medium",
            "method_family": "close-value comparison and indicator interpretation",
            "task": "Compare CO2 geological storage suitability between Murcia and Cordoba. Which province is better suited?",
            "task_goal": "按 GeoNatureAgent 图层说明，用 conditional_pct + eligible_pct 构成 CO2 地质封存候选池，对 Murcia 与 Córdoba 做接近值比较。",
            "primary_label": "D3. Spatial Statistical Misinterpretation",
            "secondary_labels": [],
            "reference_basis": "依据 province_rankings.json 中 provinces -> province -> co2 的 not_eligible_pct、conditional_pct、eligible_pct 独立计算",
            "error_summary": "生成代码没有进入 `provinces -> <province> -> co2` 指标层，所有 CO2 适宜性百分比回退为 0，并给出 Equal 决策；参考值显示 Murcia 候选池为 85.3%，Córdoba 为 89.0%，正确结论应为 Córdoba 更适合。",
            "workflow_text": "1. 读取 province_rankings.json 与 layers_registry.yaml。\n2. 任务要求候选池为 class 1 Conditional + class 2 Eligible。\n3. 生成代码只在顶层或省级字典的平铺字段中查找面积/类别值。\n4. 找不到字段后返回 0，并输出零值 CSV、JSON 和堆叠柱状图。",
            "error_location": "错误发生在 `extract_province_stats()` 对 province 统计结构的解释。实际数据为 `provinces -> Murcia/Córdoba -> co2 -> *_pct`，生成代码未进入 `co2` 子对象，也没有使用任务明确给出的 candidate_pool 定义。",
            "error_mechanism": "这是空间指标统计解释错误：CO2 适宜性是省域百分比指标，比较目标不是原始面积字段，也不是单一类别，而是 conditional 与 eligible 的组合候选池。错误代码用零值代替真实指标，导致接近值比较和结论完全失真。",
            "preview_section": image_link("../execution_result/previews/murcia_cordoba_co2_chart.png", "错误运行 CO2 对比图"),
            "reference_section": image_link("reference.png", "修正后 CO2 候选池参考图"),
            "run_dir": co2_run,
            "data_files": ["province_rankings.json", "layers_registry.yaml"],
            "required_outputs": ["murcia_cordoba_co2_comparison.csv", "murcia_cordoba_co2_decision.json", "murcia_cordoba_co2_chart.png"],
            "artifacts": ["murcia_cordoba_co2_comparison.csv", "murcia_cordoba_co2_decision.json"],
            "previews": ["murcia_cordoba_co2_chart.png"],
            "references": [
                (Path("reference/murcia_cordoba_co2_reference.png"), Path("reference.png")),
                (Path("reference/murcia_cordoba_co2_reference.csv"), Path("murcia_cordoba_co2_reference.csv")),
                (Path("reference/murcia_cordoba_co2_reference_decision.json"), Path("murcia_cordoba_co2_reference_decision.json")),
            ],
            "result_previews": [
                {
                    "source_artifact": "previews/murcia_cordoba_co2_chart.png",
                    "stage": "最终成果",
                    "preview_file": "previews/murcia_cordoba_co2_chart.png",
                    "description": "错误运行生成的 CO2 适宜性图，Murcia 与 Cordoba 均为 0。"
                }
            ],
            "evidence_metrics": lambda audit: {
                "observed_candidate_pool_values": audit["observed_candidate_pool_values"],
                "all_observed_candidate_values_zero": audit["all_observed_candidate_values_zero"],
                "expected_better_province": audit["expected_better_province"],
                "reference_decision": audit["reference_decision"],
                "observed_records": audit["observed_records"],
            },
        },
        {
            "sample_id": "geobenchx_murcia_50km_buffer_c2",
            "category_dir": "C_Spatial_Reasoning_Errors/C2_Invalid_Geometry_Handling",
            "source": "GeoBenchX/GeoNature Murcia 50km Buffer",
            "framework": "GeoBenchX tools ported in GeoNatureAgent Benchmark",
            "paper_case_id": "GeoBenchX-style spatial relationship task",
            "task_id": "gbx_port_murcia_50km_buffer_intersections",
            "difficulty": "medium",
            "method_family": "metric buffering and topological predicate selection",
            "task": "Create a 50 km buffer around the province of Murcia and list all Spanish provinces whose geometry intersects that buffer. Save the buffer and selected provinces.",
            "task_goal": "在米制投影 CRS 中对 Murcia 省界建立 50 km buffer，并用 intersects 谓词筛选所有与 buffer 相交的西班牙省份。",
            "primary_label": "C2. Invalid Geometry Handling",
            "secondary_labels": [],
            "reference_basis": "依据清除退化 ring 后的 Spain province GeoJSON、EPSG:25830 米制缓冲和 intersects 谓词独立计算",
            "error_summary": "生成代码直接用 GeoPandas 读取包含退化 ring 的 Spain province GeoJSON，未清理少于 4 个坐标的线性环，读入阶段即触发 `ValueError: A linearring requires at least 4 coordinates`，导致 50 km buffer 与相交省份结果均未生成。",
            "workflow_text": "1. 读取 Spain province GeoJSON。\n2. 定位 Murcia 省界。\n3. 投影到 EPSG:25830 后执行 50,000 m buffer。\n4. 用 intersects 筛选相交省份并输出 GeoJSON、CSV 和地图。\n5. 实际运行在第 1 步因退化 ring 中断。",
            "error_location": "错误发生在 `gpd.read_file(path)` 读入 GeoJSON 阶段。输入 `spain_provinces.geojson` 含多个少于 4 个坐标的退化 ring，生成代码没有执行 ring 清洗、`make_valid()` 或等价防御处理。",
            "error_mechanism": "这是典型无效几何处理错误：真实行政边界数据常包含小岛、孔洞或退化环，拓扑构造前必须清洗或修复。代码虽选择了正确的米制投影和 intersects 谓词，但没有通过几何有效性门槛，空间分析结果完全无法交付。",
            "preview_section": "本次错误运行在读入 GeoJSON 时中断，没有生成 `murcia_50km_buffer.geojson`、`murcia_50km_intersecting_provinces.csv` 或地图。失败日志见 `../run_log/run.log`。",
            "reference_section": image_link("reference.png", "修正后 Murcia 50km buffer 相交省份参考图"),
            "run_dir": buffer_run,
            "data_files": ["spain_provinces.geojson"],
            "required_outputs": ["murcia_50km_buffer.geojson", "murcia_50km_intersecting_provinces.csv", "murcia_50km_intersections_map.png"],
            "artifacts": [],
            "previews": [],
            "references": [
                (Path("reference/murcia_50km_intersections_reference.png"), Path("reference.png")),
                (Path("reference/murcia_50km_intersecting_provinces_reference.csv"), Path("murcia_50km_intersecting_provinces_reference.csv")),
                (Path("reference/murcia_50km_intersecting_provinces_reference.json"), Path("murcia_50km_intersecting_provinces_reference.json")),
                (Path("reference/murcia_50km_buffer_reference.geojson"), Path("murcia_50km_buffer_reference.geojson")),
                (Path("reference/murcia_50km_selected_provinces_reference.geojson"), Path("murcia_50km_selected_provinces_reference.geojson")),
            ],
            "result_previews": [],
            "evidence_metrics": lambda audit: {
                "total_features": audit["total_features"],
                "total_rings": audit["total_rings"],
                "dropped_degenerate_rings": audit["dropped_degenerate_rings"],
                "features_with_dropped_rings": audit["features_with_dropped_rings"],
                "observed_error": audit["observed_error"],
                "buffer_distance_m": audit["buffer_distance_m"],
                "projected_crs": audit["projected_crs"],
                "intersecting_province_count": audit["intersecting_province_count"],
                "intersecting_provinces": audit["intersecting_provinces"],
            },
        },
    ]


def main() -> int:
    annotations = [promote_sample(sample) for sample in sample_specs()]
    update_manifest(annotations)
    update_docs()
    print(json.dumps({"promoted": [item["sample_id"] for item in annotations]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
