import csv
import hashlib
import json
import math
import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd
import rasterio

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DATASET_ROOT = ROOT.parent
REPO_ROOT = Path(__file__).resolve().parents[3] / "GeoBenchX"
TUNING_SET = REPO_ROOT / "benchmark_set" / "evaluator_tuning_set.json"
DATA_ROOT = ROOT / "data" / "geobenchx" / "Data" / "Data"
RUNS_ROOT = ROOT / "runs"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sanitize_text(text: str) -> str:
    google_drive_geo = "G:" + "/My Drive/Geo Agent/Tasks data/Data/GeoData"
    google_drive_geo_win = "G:" + "\\My Drive\\Geo Agent\\Tasks data\\Data\\GeoData"
    replacements = {
        str(DATA_ROOT): "data_source",
        str(DATASET_ROOT): "<WORKSPACE>",
        str(REPO_ROOT): "<GEOBENCHX_REPO>",
        google_drive_geo: "data_source/GeoData",
        google_drive_geo_win: "data_source\\GeoData",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def sanitize_obj(obj: object) -> object:
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, list):
        return [sanitize_obj(item) for item in obj]
    if isinstance(obj, dict):
        return {key: sanitize_obj(value) for key, value in obj.items()}
    return obj


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


def clean_dir(path: Path) -> None:
    resolved_root = DATASET_ROOT.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise RuntimeError(f"Refusing to clean path outside dataset root: {resolved_path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_text_sanitized(src: Path, dst: Path) -> None:
    write_text(dst, sanitize_text(read_text(src)))


def selected_tasks() -> dict[str, dict]:
    data = json.loads(TUNING_SET.read_text(encoding="utf-8"))
    return {task["task_ID"]: task for task in data["tasks"]}


def first_reference(task: dict) -> dict:
    for solution in task["reference_solutions"]:
        steps = solution.get("steps", [])
        if steps and steps[0].get("function_name") != "reject_task":
            return solution
    return task["reference_solutions"][0]


def workflow_names(steps: list[dict]) -> list[str]:
    return [step.get("function_name", "") for step in steps]


def write_trace_files(run_dir: Path, task: dict, spec: dict, audit: dict) -> None:
    reference_solution = first_reference(task)
    generated_solution = task["generated_solution"]
    prompt = {
        "source": "GeoBenchX evaluator tuning set",
        "model": "claude-3-5-haiku-20241022",
        "temperature": 0,
        "task_ID": task["task_ID"],
        "task_text": task["task_text"],
        "task_labels": task["task_labels"],
        "note": "The original benchmark stores the generated tool-call solution and human evaluation, not a full chat transcript. This package materializes that trace and re-audits it against local GeoBenchX data.",
    }
    write_json(run_dir / "prompt.json", prompt)
    write_text(
        run_dir / "prompt.txt",
        "\n".join(
            [
                "GeoBenchX task trace materialization",
                f"Task ID: {task['task_ID']}",
                f"Task: {task['task_text']}",
                f"Labels: {', '.join(task['task_labels'])}",
                "Expected output: GeoBenchX tool-call sequence solving the task.",
            ]
        )
        + "\n",
    )
    write_json(run_dir / "reference_solution.json", sanitize_obj(reference_solution))
    write_json(run_dir / "generated_solution.json", sanitize_obj(generated_solution))
    write_text(run_dir / "model_response.txt", json.dumps(sanitize_obj(generated_solution), ensure_ascii=False, indent=2) + "\n")
    write_text(run_dir / "human_evaluation.txt", task.get("match_reasoning_Human", "") + "\n")

    rows = []
    ref_steps = reference_solution.get("steps", [])
    gen_steps = generated_solution.get("steps", [])
    for i in range(max(len(ref_steps), len(gen_steps))):
        rows.append(
            {
                "step_index": i + 1,
                "reference_function": ref_steps[i]["function_name"] if i < len(ref_steps) else "",
                "generated_function": gen_steps[i]["function_name"] if i < len(gen_steps) else "",
                "reference_arguments": json.dumps(sanitize_obj(ref_steps[i].get("arguments", {})), ensure_ascii=False) if i < len(ref_steps) else "",
                "generated_arguments": json.dumps(sanitize_obj(gen_steps[i].get("arguments", {})), ensure_ascii=False) if i < len(gen_steps) else "",
            }
        )
    with (run_dir / "workflow_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(run_dir / "workflow_comparison.json", rows)

    metadata = {
        "status": "audited_trace",
        "execution_returncode": 0,
        "task_id": spec["task_id"],
        "source_task_id": task["task_ID"],
        "model": "claude-3-5-haiku-20241022",
        "provider": "Anthropic",
        "method_family": spec["method_family"],
        "difficulty": spec["difficulty"],
        "human_score": task.get("match_score_Human"),
        "human_reasoning": task.get("match_reasoning_Human", ""),
        "missing_required_outputs": [],
    }
    write_json(run_dir / "metadata.json", metadata)
    write_json(run_dir / "audit_summary.json", audit)
    write_text(
        run_dir / "run.log",
        sanitize_text(
            "\n".join(
                [
                    "[run] GeoBenchX evaluator tuning trace materialized.",
                    f"[task] {task['task_ID']} - {task['task_text']}",
                    f"[reference_functions] {workflow_names(ref_steps)}",
                    f"[generated_functions] {workflow_names(gen_steps)}",
                    f"[human_score] {task.get('match_score_Human')}",
                    f"[audit] {json.dumps(audit, ensure_ascii=False)}",
                ]
            )
            + "\n"
        ),
    )


def plot_points(gdf: gpd.GeoDataFrame, column: str, title: str, path: Path, cmap: str) -> None:
    plot_gdf = gdf.to_crs("EPSG:4326") if gdf.crs else gdf
    fig, ax = plt.subplots(figsize=(9, 5.4))
    values = pd.to_numeric(plot_gdf[column], errors="coerce")
    finite = values.replace([math.inf, -math.inf], pd.NA).notna()
    plot_gdf.loc[finite].plot(
        ax=ax,
        column=column,
        cmap=cmap,
        markersize=8,
        alpha=0.75,
        legend=True,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linewidth=0.2, alpha=0.4)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_world(gdf: gpd.GeoDataFrame, column: str, title: str, path: Path, cmap: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    gdf.plot(ax=ax, color="#efefef", edgecolor="#cccccc", linewidth=0.2)
    gdf.dropna(subset=[column]).plot(
        ax=ax,
        column=column,
        cmap=cmap,
        legend=True,
        edgecolor="#666666",
        linewidth=0.15,
        missing_kwds={"color": "#f7f7f7"},
    )
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_earthquake_population_trace(run_dir: Path, task: dict, spec: dict) -> dict:
    geodata = DATA_ROOT / "GeoData"
    quake_path = geodata / "earthquakes_30_days_Feb142025.shp"
    raster_path = geodata / "usa_ppp_2020_1km_Aggregated_UNadj.tif"

    earthquakes = gpd.read_file(quake_path)
    with rasterio.open(raster_path) as src:
        sample_gdf = earthquakes.to_crs(src.crs) if earthquakes.crs and src.crs and earthquakes.crs != src.crs else earthquakes
        coords = [(geom.x, geom.y) if geom is not None and not geom.is_empty else (math.nan, math.nan) for geom in sample_gdf.geometry]
        samples = []
        for value in src.sample(coords):
            v = float(value[0])
            if src.nodata is not None and v == src.nodata:
                v = math.nan
            samples.append(v)
        raster_crs = src.crs.to_string() if src.crs else None
        nodata = src.nodata

    audited = earthquakes.copy()
    audited["earthquake_population"] = samples
    mag_col = "mag" if "mag" in audited.columns else next(col for col in audited.columns if col.lower() == "mag")
    significant = audited[pd.to_numeric(audited[mag_col], errors="coerce") >= 4.0].copy()

    audited_csv = run_dir / "earthquake_population_reference_samples.csv"
    export_cols = [col for col in ["id", "place", "time", mag_col, "earthquake_population"] if col in audited.columns]
    audited[export_cols + ["geometry"]].to_file(run_dir / "earthquake_population_reference_points.geojson", driver="GeoJSON")
    audited.drop(columns="geometry")[export_cols].to_csv(audited_csv, index=False)
    significant.drop(columns="geometry", errors="ignore").to_csv(run_dir / "generated_significant_earthquakes.csv", index=False)

    plot_points(
        audited,
        "earthquake_population",
        "Reference: population sampled at earthquake locations",
        run_dir / "reference" / "earthquake_population_heatmap_reference.png",
        "viridis",
    )
    plot_points(
        significant,
        mag_col,
        "Generated: earthquake magnitude mapped instead of population",
        run_dir / "generated_earthquake_magnitude_map.png",
        "magma",
    )

    reference_steps = first_reference(task)["steps"]
    generated_steps = task["generated_solution"]["steps"]
    ref_names = workflow_names(reference_steps)
    gen_names = workflow_names(generated_steps)
    audit = {
        "task_type": "raster-to-point value extraction for heatmap",
        "earthquake_count": int(len(audited)),
        "generated_filtered_count_mag_ge_4": int(len(significant)),
        "population_sample_non_null_count": int(pd.Series(samples).notna().sum()),
        "population_sample_positive_count": int((pd.Series(samples).fillna(0) > 0).sum()),
        "population_sample_max": float(pd.Series(samples).max(skipna=True)),
        "raster_crs": raster_crs,
        "raster_nodata": nodata,
        "reference_value_column": "earthquake_population",
        "generated_value_column": mag_col,
        "missing_reference_steps": [name for name in ref_names if name not in gen_names],
        "extra_generated_steps": [name for name in gen_names if name not in ref_names],
        "human_score": task.get("match_score_Human"),
        "human_reasoning": task.get("match_reasoning_Human"),
    }
    write_trace_files(run_dir, task, spec, audit)
    return audit


def read_world_bank_csv(zip_path: Path, csv_name: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(csv_name) as f:
            return pd.read_csv(f, skiprows=4)


def run_rural_percentage_trace(run_dir: Path, task: dict, spec: dict) -> dict:
    stat = DATA_ROOT / "StatData"
    geodata = DATA_ROOT / "GeoData"
    rural_zip = stat / "API_SP.RUR.TOTL_DS2_en_csv_v2_6835.zip"
    total_zip = stat / "API_SP.POP.TOTL_DS2_en_csv_v2_56.zip"
    countries_path = geodata / "WB_countries_Admin0_10m.shp"

    rural = read_world_bank_csv(rural_zip, "API_SP.RUR.TOTL_DS2_en_csv_v2_6835.csv")
    total = read_world_bank_csv(total_zip, "API_SP.POP.TOTL_DS2_en_csv_v2_56.csv")
    countries = gpd.read_file(countries_path)

    for df in (rural, total):
        df["2023"] = pd.to_numeric(df["2023"], errors="coerce")
    rural_pct = rural[["Country Name", "Country Code", "2023"]].rename(columns={"2023": "rural_population_2023"})
    total_pct = total[["Country Code", "2023"]].rename(columns={"2023": "total_population_2023"})
    pct = rural_pct.merge(total_pct, on="Country Code", how="inner")
    pct["rural_percentage"] = pct["rural_population_2023"] / pct["total_population_2023"] * 100

    reference = countries.merge(pct, left_on="WB_A3", right_on="Country Code", how="left")
    generated = countries.merge(rural_pct, left_on="WB_A3", right_on="Country Code", how="left")

    pct.to_csv(run_dir / "rural_percentage_reference_table.csv", index=False)
    rural_pct.to_csv(run_dir / "generated_raw_rural_population_table.csv", index=False)

    plot_world(
        reference,
        "rural_percentage",
        "Reference: rural population as percentage of total population",
        run_dir / "reference" / "rural_percentage_reference_map.png",
        "YlGn",
    )
    plot_world(
        generated,
        "rural_population_2023",
        "Generated: raw rural population count mislabeled as percentage",
        run_dir / "generated_raw_rural_population_map.png",
        "YlOrBr",
    )

    reference_country_records = reference.dropna(subset=["rural_percentage"]).copy()
    generated_country_records = generated.dropna(subset=["rural_population_2023"]).copy()
    if "NAME_EN" in reference_country_records.columns:
        reference_country_records["mapped_country_name"] = reference_country_records["NAME_EN"]
    else:
        reference_country_records["mapped_country_name"] = reference_country_records["Country Name"]
    if "NAME_EN" in generated_country_records.columns:
        generated_country_records["mapped_country_name"] = generated_country_records["NAME_EN"]
    else:
        generated_country_records["mapped_country_name"] = generated_country_records["Country Name"]

    top_ref = (
        reference_country_records
        .sort_values("rural_percentage", ascending=False)
        .head(8)[["mapped_country_name", "rural_percentage"]]
        .to_dict(orient="records")
    )
    top_gen = (
        generated_country_records
        .sort_values("rural_population_2023", ascending=False)
        .head(8)[["mapped_country_name", "rural_population_2023"]]
        .to_dict(orient="records")
    )
    reference_steps = first_reference(task)["steps"]
    generated_steps = task["generated_solution"]["steps"]
    ref_names = workflow_names(reference_steps)
    gen_names = workflow_names(generated_steps)
    audit = {
        "task_type": "choropleth mapping of an intensive percentage variable",
        "reference_mapping_key": "rural_percentage",
        "generated_mapping_key": "2023",
        "generated_dataset": "Rural population",
        "missing_reference_steps": [name for name in ref_names if name not in gen_names],
        "omitted_total_population_dataset": "load_data: Population, total" not in [
            f"{step.get('function_name')}: {step.get('arguments', {}).get('dataset', '')}" for step in generated_steps
        ],
        "observed_legend_text": task["generated_solution"]["steps"][-1]["arguments"].get("legendtext"),
        "mapped_country_count_reference": int(len(reference_country_records)),
        "mapped_country_count_generated": int(len(generated_country_records)),
        "raw_rural_population_2023_max": float(generated_country_records["rural_population_2023"].max(skipna=True)),
        "rural_percentage_max": float(reference_country_records["rural_percentage"].max(skipna=True)),
        "reference_top_rural_percentage": top_ref,
        "generated_top_raw_rural_population": top_gen,
        "human_score": task.get("match_score_Human"),
        "human_reasoning": task.get("match_reasoning_Human"),
    }
    write_trace_files(run_dir, task, spec, audit)
    return audit


def materialize_runs(specs: list[dict]) -> list[dict]:
    tasks = selected_tasks()
    promoted = []
    for spec in specs:
        task = tasks[spec["source_task_id"]]
        run_dir = RUNS_ROOT / spec["run_id"]
        clean_dir(run_dir)
        if spec["sample_id"] == "geobenchx_earthquake_population_heatmap_d2":
            audit = run_earthquake_population_trace(run_dir, task, spec)
        elif spec["sample_id"] == "geobenchx_rural_population_percentage_d3":
            audit = run_rural_percentage_trace(run_dir, task, spec)
        else:
            raise ValueError(spec["sample_id"])
        spec["run_dir"] = run_dir
        spec["audit"] = audit
        promoted.append(spec)
    return promoted


def make_config(spec: dict) -> str:
    return f"""[experiment]
source = {spec["source"]}
experiment = geobenchx_evaluator_tuning_trace_audit
backend = published_tool_call_trace_with_local_data_audit
framework = GeoBenchX
model = claude-3-5-haiku-20241022
provider = Anthropic
temperature = 0
api_key = <REDACTED>
base_url = <REDACTED>
"""


def make_task_md(spec: dict) -> str:
    data_files = "\n".join(f"- `{name}`" for name in spec["data_files"])
    outputs = "\n".join(f"- `{name}`" for name in spec["required_outputs"])
    return f"""# {spec["source"]}

- 任务编号：{spec["task_id"]}
- GeoBenchX 任务编号：{spec["source_task_id"]}
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX published trace）
- 来源项目：GeoBenchX
- 难度：{spec["difficulty"]}
- 空间方法：{spec["method_family"]}

## 任务描述

{spec["task"]}

## 本地输入数据

{data_files}

## 任务要求输出

{outputs}
"""


def make_evidence_readme(spec: dict) -> str:
    metrics = json.dumps(spec["evidence_metrics"](spec["audit"]), ensure_ascii=False, indent=2)
    return f"""# GIS 错误证据：{spec["source"]}

- 主标签：{spec["primary_label"]}
- 次标签：{", ".join(spec["secondary_labels"]) if spec["secondary_labels"] else "无"}
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX evaluator tuning set published trace）
- 来源项目：GeoBenchX
- 难度：{spec["difficulty"]}

## 1. 任务目标

{spec["task_goal"]}

## 2. 任务执行工作流

{spec["workflow_text"]}

## 3. 错误发生位置

{spec["error_location"]}

## 4. 错误机制与结果影响

{spec["error_mechanism"]}

## 5. 具体错误证据

```json
{metrics}
```

## 6. 任务执行结果预览

{spec["preview_section"]}

## 7. 解决错误后 GIS 任务应有的结果预览

{spec["reference_section"]}

## 8. 可视化判读说明

本案例的核心证据是 GeoBenchX 发布的人审工具调用轨迹、生成方案与参考方案的步骤差异，以及本地数据审计重新计算出的参考指标/错误指标。预览图用于展示错误工作流与参考工作流表达的主题变量不同，最终判定以第 5 节的指标和 `execution_result/workflow/` 下的工具调用 JSON 为准。
"""


def image_link(path: str, alt: str) -> str:
    return f"![{alt}]({path})"


def copy_required_data(spec: dict, sample_dir: Path) -> None:
    for rel in spec["data_files"]:
        copy_file(DATA_ROOT / rel, sample_dir / "data_source" / rel)


def promote_sample(spec: dict) -> dict:
    sample_dir = DATASET_ROOT / spec["category_dir"] / spec["sample_id"]
    clean_dir(sample_dir)
    copy_required_data(spec, sample_dir)

    run_dir = spec["run_dir"]
    for name in [
        "prompt.txt",
        "prompt.json",
        "model_response.txt",
        "generated_solution.json",
        "reference_solution.json",
        "workflow_comparison.csv",
        "workflow_comparison.json",
        "human_evaluation.txt",
    ]:
        copy_text_sanitized(run_dir / name, sample_dir / "execution_result" / "workflow" / name)
    copy_text_sanitized(run_dir / "run.log", sample_dir / "run_log" / "run.log")

    for artifact in spec["artifacts"]:
        src = run_dir / artifact
        if src.suffix.lower() in {".json", ".txt", ".csv", ".geojson"}:
            copy_text_sanitized(src, sample_dir / "execution_result" / "artifacts" / artifact)
        else:
            copy_file(src, sample_dir / "execution_result" / "artifacts" / artifact)
    for preview in spec["previews"]:
        copy_file(run_dir / preview, sample_dir / "execution_result" / "previews" / Path(preview).name)
    for reference_src, reference_dst in spec["references"]:
        copy_file(run_dir / reference_src, sample_dir / "evidence" / reference_dst)

    write_json(sample_dir / "execution_result" / "run_record.json", sanitize_obj({
        "source_run": run_dir.name,
        "status": "audited_trace",
        "execution_returncode": 0,
        "task_id": spec["task_id"],
        "source_task_id": spec["source_task_id"],
        "model": "claude-3-5-haiku-20241022",
        "method_family": spec["method_family"],
        "difficulty": spec["difficulty"],
        "audit_summary": spec["audit"],
    }))
    write_text(sample_dir / "llm_config" / "config.ini", make_config(spec))
    write_json(sample_dir / "llm_config" / "provenance.json", {
        "source": spec["source"],
        "source_project": "GeoBenchX",
        "paper_case_id": spec["source_task_id"],
        "snapshot": "published GeoBenchX evaluator tuning trace with local data audit",
        "note": "密钥、服务端点和本机绝对路径已隐去；原始材料来自 GeoBenchX benchmark_set/evaluator_tuning_set.json。",
    })
    write_text(sample_dir / "task.md", make_task_md(spec))
    write_text(sample_dir / "evidence" / "README.md", make_evidence_readme(spec))
    write_json(sample_dir / "evidence" / "reference_metrics.json", spec["evidence_metrics"](spec["audit"]))

    annotation = {
        "sample_id": spec["sample_id"],
        "source": spec["source"],
        "task_id": spec["task_id"],
        "sample_origin": "observed_run",
        "llm_configuration": {
            "primary_model": "claude-3-5-haiku-20241022",
            "provider": "Anthropic",
            "reasoning": "GeoBenchX published tool-call trace; temperature 0",
            "framework": "GeoBenchX",
        },
        "primary_label": spec["primary_label"],
        "secondary_labels": spec["secondary_labels"],
        "error_summary": spec["error_summary"],
        "result_previews": spec["result_previews"],
        "reference_preview_file": "reference.png",
        "evidence_readme": "README.md",
        "reference_basis": spec["reference_basis"],
        "evidence_metrics": spec["evidence_metrics"](spec["audit"]),
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
    readme = readme.replace("本版包含 **65** 个 GIS 错误样本", f"本版包含 **{total}** 个 GIS 错误样本")
    readme = readme.replace("本版包含 **67** 个 GIS 错误样本", f"本版包含 **{total}** 个 GIS 错误样本")
    readme = readme.replace(
        "LLM-Geo、GeoNatureAgent 与 GeoBenchX 定向外部论文复现运行 10 次，其中 5 次进入主样本；2 个 taxonomy 补齐样本来自论文研究与 GIS 专业经验。",
        "LLM-Geo、GeoNatureAgent 与 GeoBenchX 定向外部论文复现/任务轨迹审计 12 次，其中 7 次进入主样本；2 个 taxonomy 补齐样本来自论文研究与 GIS 专业经验。",
    )
    write_text(readme_path, readme)

    run_audit_path = DATASET_ROOT / "RUN_AUDIT.md"
    audit = read_text(run_audit_path)
    audit = audit.replace(
        "- 外部论文复现记录：10（LLM-Geo 3 条，GeoNatureAgent/GeoBenchX 7 条），其中 5 条经 GIS 审计进入主样本；GeoNature/GeoBenchX 审计见 `external_task_runs/geonature_audit_summary.json`。",
        "- 外部论文复现记录：12（LLM-Geo 3 条，GeoNatureAgent/GeoBenchX 7 条，GeoBenchX 官方调参集任务轨迹 2 条），其中 7 条经 GIS 审计进入主样本；GeoNature/GeoBenchX 审计见 `external_task_runs/geonature_audit_summary.json` 与 GeoBenchX 样本运行目录。",
    )
    audit = audit.replace("- observed_run 样本：63", f"- observed_run 样本：{observed}")
    audit = audit.replace("- observed_run 样本：65", f"- observed_run 样本：{observed}")
    audit = audit.replace("- research_supplement 样本：2", f"- research_supplement 样本：{research}")
    if "GeoBenchX Earthquake Population Heatmap" not in audit:
        audit = replace_once(
            audit,
            "| GeoAgent Task 75 | D2. Spatial Allocation Error | thinking 已开启 |",
            "| GeoAgent Task 75 | D2. Spatial Allocation Error | thinking 已开启 |\n| GeoBenchX Earthquake Population Heatmap | D2. Spatial Allocation Error | published tool-call trace; temperature 0 |",
        )
    if "GeoBenchX Rural Population Percentages" not in audit:
        audit = replace_once(
            audit,
            "| GeoNatureAgent CO2 Candidate Pool Comparison | D3. Spatial Statistical Misinterpretation | direct request；thinking 开关未单列记录 |",
            "| GeoNatureAgent CO2 Candidate Pool Comparison | D3. Spatial Statistical Misinterpretation | direct request；thinking 开关未单列记录 |\n| GeoBenchX Rural Population Percentages | D3. Spatial Statistical Misinterpretation | published tool-call trace; temperature 0 |",
        )
    write_text(run_audit_path, audit)

    coverage_path = DATASET_ROOT / "configuration_coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["geobenchx-claude-3-5-haiku-tool-trace"] = 2
    write_json(coverage_path, coverage)

    external_path = ROOT / "README.md"
    external = read_text(external_path)
    local_repo_root = REPO_ROOT.parent
    local_paths = {
        str(local_repo_root / "LLM-Geo"): r"<LOCAL_REPO_ROOT>\LLM-Geo",
        str(local_repo_root / "LLM-Find"): r"<LOCAL_REPO_ROOT>\LLM-Find",
        str(local_repo_root / "Change-Agent"): r"<LOCAL_REPO_ROOT>\Change-Agent",
        str(local_repo_root / "CartoAgent"): r"<LOCAL_REPO_ROOT>\CartoAgent",
        str(local_repo_root / "GeoReasoner"): r"<LOCAL_REPO_ROOT>\GeoReasoner",
        str(local_repo_root / "GeoBenchX"): r"<LOCAL_REPO_ROOT>\GeoBenchX",
        str(local_repo_root / "MapReader"): r"<LOCAL_REPO_ROOT>\MapReader",
        str(DATASET_ROOT.parent / ".venv"): r"<PYTHON_ENV>",
    }
    for local_path, placeholder in local_paths.items():
        external = external.replace(local_path, placeholder)
    external = external.replace(
        "| MapReader | `<LOCAL_REPO_ROOT>\\MapReader` | Clone timed out before checkout. | Retry later if map-analysis tasks are needed. |",
        "| MapReader | `<LOCAL_REPO_ROOT>\\MapReader` | Full clone with sample historical map images and metadata; no LLM-agent task trace found yet. | Candidate only if a clear map-reading/georeference task can be audited. |",
    )
    if "| GeoBenchX |" not in external:
        external = external.replace(
            "| GeoReasoner | `<LOCAL_REPO_ROOT>\\GeoReasoner` | Has code; stage 1 data on HuggingFace, street-view data restricted. | Not first batch. |",
            "| GeoReasoner | `<LOCAL_REPO_ROOT>\\GeoReasoner` | Has code; stage 1 data on HuggingFace, street-view data restricted. | Not first batch. |\n| GeoBenchX | `<LOCAL_REPO_ROOT>\\GeoBenchX` | Has 202 benchmark tasks, 50 evaluator-tuning generated traces, and official data archive now downloaded under `external_task_runs/data/geobenchx`. | Strong source for audited tool-call GIS method errors. |",
        )
    if "## GeoBenchX Evaluator Tuning Trace Audits" not in external:
        external += """

## GeoBenchX Evaluator Tuning Trace Audits

The official GeoBenchX data archive (`Data.zip`, 484M) was downloaded and
extracted to `external_task_runs/data/geobenchx`. Two human-scored generated
tool-call traces from `benchmark_set/evaluator_tuning_set.json` were
materialized and audited against local data.

Promoted GIS-error cases:

| Run | Outcome | Dataset sample |
| --- | --- | --- |
| `20260709_geobenchx_task_367674_earthquake_population_heatmap` | Generated workflow mapped earthquake magnitude and skipped raster-to-point population extraction. | `D_Spatial_Analysis_Errors\\D2_Spatial_Allocation_Error\\geobenchx_earthquake_population_heatmap_d2` |
| `20260709_geobenchx_task_748943_rural_population_percentage` | Generated workflow mapped raw rural population counts while labeling them as percentages. | `D_Spatial_Analysis_Errors\\D3_Spatial_Statistical_Misinterpretation\\geobenchx_rural_population_percentage_d3` |

Excluded despite being present in GeoBenchX tuning data:

- one-year map year mismatches: weak or partial temporal selection errors, not typical GIS taxonomy cases.
- unsolvable-task rejection failures: useful for agent calibration but not GIS domain-result errors.
- regional-definition mismatches: often geographic knowledge ambiguity rather than spatial method failure.
"""
    write_text(external_path, external)


def sample_specs() -> list[dict]:
    return [
        {
            "sample_id": "geobenchx_earthquake_population_heatmap_d2",
            "run_id": "20260709_geobenchx_task_367674_earthquake_population_heatmap",
            "category_dir": "D_Spatial_Analysis_Errors/D2_Spatial_Allocation_Error",
            "source": "GeoBenchX Earthquake Population Heatmap",
            "source_task_id": "TASK_250309_135125_367674",
            "task_id": "geobenchx_task_367674",
            "difficulty": "hard",
            "method_family": "raster-to-point extraction and weighted heatmap visualization",
            "task": "Make a heatmap showing population concentration in earthquake-affected zones.",
            "task_goal": "用地震点位叠加 1 km 人口栅格，先把人口值提取到地震位置，再按人口值生成受地震影响区域的人口集中热力图。",
            "primary_label": "D2. Spatial Allocation Error",
            "secondary_labels": [],
            "reference_basis": "依据 GeoBenchX 参考工具链 `get_values_from_raster_with_geometries` 和本地 USA 1km 人口栅格重新提取地震点位人口值",
            "error_summary": "模型跳过 raster-to-point 人口值提取步骤，改用地震震级 `mag` 作为热力图权重，还额外筛选 mag>=4；结果表达的是地震强度/事件分布，而不是地震影响区域的人口集中程度。",
            "workflow_text": "1. 读取地震点数据。\n2. 参考流程读取 USA 1km 人口栅格并用 `get_values_from_raster_with_geometries` 将人口值分配到地震点。\n3. 错误流程只读取栅格路径但没有抽样/分配人口值。\n4. 错误流程直接按 `mag` 字段绘制热力图。",
            "error_location": "错误发生在 GeoBenchX 生成工具调用序列的第 3-4 步：缺少 `get_values_from_raster_with_geometries`，且 `make_heatmap` 的 `value_column` 从参考的 `earthquake_population` 变成了 `mag`。",
            "error_mechanism": "这是典型的空间分配/栅格值提取错误。任务目标是把人口栅格的空间属性分配到地震点位，再用人口值表达受影响人口集中度；模型没有完成 raster-vector 数据融合，导致最终地图变量从人口暴露变成了地震震级。",
            "preview_section": image_link("../execution_result/previews/generated_earthquake_magnitude_map.png", "错误运行：按地震震级绘制的点值图"),
            "reference_section": image_link("reference.png", "参考结果：按地震点位人口值绘制的图"),
            "data_files": [
                "GeoData/earthquakes_30_days_Feb142025.cpg",
                "GeoData/earthquakes_30_days_Feb142025.dbf",
                "GeoData/earthquakes_30_days_Feb142025.prj",
                "GeoData/earthquakes_30_days_Feb142025.qmd",
                "GeoData/earthquakes_30_days_Feb142025.shp",
                "GeoData/earthquakes_30_days_Feb142025.shx",
                "GeoData/usa_ppp_2020_1km_Aggregated_UNadj.tif",
            ],
            "required_outputs": [
                "earthquake_population_reference_samples.csv",
                "generated_earthquake_magnitude_map.png",
                "earthquake_population_heatmap_reference.png",
            ],
            "artifacts": [
                "earthquake_population_reference_samples.csv",
                "earthquake_population_reference_points.geojson",
                "generated_significant_earthquakes.csv",
            ],
            "previews": ["generated_earthquake_magnitude_map.png"],
            "references": [
                (Path("reference/earthquake_population_heatmap_reference.png"), Path("reference.png")),
                (Path("earthquake_population_reference_samples.csv"), Path("earthquake_population_reference_samples.csv")),
                (Path("earthquake_population_reference_points.geojson"), Path("earthquake_population_reference_points.geojson")),
            ],
            "result_previews": [
                {
                    "source_artifact": "previews/generated_earthquake_magnitude_map.png",
                    "stage": "最终成果变量",
                    "preview_file": "previews/generated_earthquake_magnitude_map.png",
                    "description": "错误流程用地震震级作为热力图变量，未表达人口集中程度。"
                }
            ],
            "evidence_metrics": lambda audit: {
                "earthquake_count": audit["earthquake_count"],
                "generated_filtered_count_mag_ge_4": audit["generated_filtered_count_mag_ge_4"],
                "population_sample_non_null_count": audit["population_sample_non_null_count"],
                "population_sample_positive_count": audit["population_sample_positive_count"],
                "reference_value_column": audit["reference_value_column"],
                "generated_value_column": audit["generated_value_column"],
                "missing_reference_steps": audit["missing_reference_steps"],
                "extra_generated_steps": audit["extra_generated_steps"],
                "human_score": audit["human_score"],
                "human_reasoning": audit["human_reasoning"],
            },
        },
        {
            "sample_id": "geobenchx_rural_population_percentage_d3",
            "run_id": "20260709_geobenchx_task_748943_rural_population_percentage",
            "category_dir": "D_Spatial_Analysis_Errors/D3_Spatial_Statistical_Misinterpretation",
            "source": "GeoBenchX Rural Population Percentages",
            "source_task_id": "TASK_250309_135125_748943",
            "task_id": "geobenchx_task_748943",
            "difficulty": "medium",
            "method_family": "statistical variable derivation and choropleth mapping",
            "task": "Show rural population percentages worldwide.",
            "task_goal": "先用农村人口除以总人口并乘以 100 得到每个国家的农村人口百分比，再将该百分比连接到国家边界并制作世界分级设色图。",
            "primary_label": "D3. Spatial Statistical Misinterpretation",
            "secondary_labels": [],
            "reference_basis": "依据 GeoBenchX 参考工具链，使用 World Bank `Rural population` 与 `Population, total` 的 2023 列计算 `rural_percentage = rural / total * 100`",
            "error_summary": "模型只读取并映射 `Rural population` 的 2023 原始人数，却把图例写成 `Rural Population (%)`；它没有读取总人口，也没有计算比例，导致分级设色图表达的是规模效应而不是农村人口百分比。",
            "workflow_text": "1. 参考流程读取农村人口和总人口两个统计表。\n2. 参考流程计算 `rural_population / total_population * 100`。\n3. 错误流程只读取农村人口表并直接与国家边界合并。\n4. 错误流程用 `2023` 原始人口数做 choropleth，却在图例中标注为百分比。",
            "error_location": "错误发生在生成工具调用序列的统计变量构造阶段：缺少 `Population, total` 数据、`calculate_columns` 和 `scale_column_by_value`，并在 `make_choropleth_map` 中使用 `mappingkey=2023`。",
            "error_mechanism": "这是典型的空间统计变量语义误解：百分比是强度/比例变量，不能用农村人口总量替代。错误结果会把人口大国突出显示为“百分比高”，与真实农村人口占比完全不同，同时图例误标加重误导。",
            "preview_section": image_link("../execution_result/previews/generated_raw_rural_population_map.png", "错误运行：原始农村人口数量图"),
            "reference_section": image_link("reference.png", "参考结果：农村人口百分比图"),
            "data_files": [
                "StatData/API_SP.RUR.TOTL_DS2_en_csv_v2_6835.zip",
                "StatData/API_SP.POP.TOTL_DS2_en_csv_v2_56.zip",
                "GeoData/WB_countries_Admin0_10m.cpg",
                "GeoData/WB_countries_Admin0_10m.dbf",
                "GeoData/WB_countries_Admin0_10m.prj",
                "GeoData/WB_countries_Admin0_10m.shp",
                "GeoData/WB_countries_Admin0_10m.shp.xml",
                "GeoData/WB_countries_Admin0_10m.shx",
            ],
            "required_outputs": [
                "rural_percentage_reference_table.csv",
                "generated_raw_rural_population_table.csv",
                "rural_percentage_reference_map.png",
                "generated_raw_rural_population_map.png",
            ],
            "artifacts": [
                "rural_percentage_reference_table.csv",
                "generated_raw_rural_population_table.csv",
            ],
            "previews": ["generated_raw_rural_population_map.png"],
            "references": [
                (Path("reference/rural_percentage_reference_map.png"), Path("reference.png")),
                (Path("rural_percentage_reference_table.csv"), Path("rural_percentage_reference_table.csv")),
            ],
            "result_previews": [
                {
                    "source_artifact": "previews/generated_raw_rural_population_map.png",
                    "stage": "最终专题图变量",
                    "preview_file": "previews/generated_raw_rural_population_map.png",
                    "description": "错误流程按原始农村人口总量绘图，却将图例标成百分比。"
                }
            ],
            "evidence_metrics": lambda audit: {
                "reference_mapping_key": audit["reference_mapping_key"],
                "generated_mapping_key": audit["generated_mapping_key"],
                "missing_reference_steps": audit["missing_reference_steps"],
                "omitted_total_population_dataset": audit["omitted_total_population_dataset"],
                "observed_legend_text": audit["observed_legend_text"],
                "raw_rural_population_2023_max": audit["raw_rural_population_2023_max"],
                "rural_percentage_max": audit["rural_percentage_max"],
                "reference_top_rural_percentage": audit["reference_top_rural_percentage"],
                "generated_top_raw_rural_population": audit["generated_top_raw_rural_population"],
                "human_score": audit["human_score"],
                "human_reasoning": audit["human_reasoning"],
            },
        },
    ]


def main() -> int:
    if not TUNING_SET.exists():
        raise FileNotFoundError(TUNING_SET)
    if not DATA_ROOT.exists():
        raise FileNotFoundError(DATA_ROOT)
    specs = materialize_runs(sample_specs())
    annotations = [promote_sample(spec) for spec in specs]
    update_manifest(annotations)
    update_docs()
    print(json.dumps({"promoted": [item["sample_id"] for item in annotations]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
