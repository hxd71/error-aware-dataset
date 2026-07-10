import argparse
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

import requests


DATA_ROOT = Path(__file__).resolve().parent / "data" / "geonature"


TASKS = {
    "gn_v5_31_habitat_beja_lulc": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_31_habitat_province_single",
        "category": "habitat_analysis",
        "difficulty": "easy",
        "method_family": "categorical LULC composition",
        "task": (
            "Analyze the land cover composition for the district of Beja in Portugal "
            "using the BigEarthNet LULC dataset."
        ),
        "data_files": ["bigearthnet_portugal_stats.json"],
        "outputs": [
            "beja_lulc_breakdown.csv",
            "beja_lulc_summary.json",
            "beja_lulc_chart.png",
        ],
        "notes": (
            "Use the categorical class labels and percentages exactly as provided. "
            "Do not average numeric class codes or treat land-cover class IDs as ordinal values."
        ),
    },
    "gn_v5_62_forest_cover_rank_bigearthnet": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_62_list_layers_habitat_years",
        "category": "tool_selection",
        "difficulty": "hard",
        "method_family": "categorical aggregation and ranking",
        "task": (
            "Create a chart ranking Beja, Faro, Lisboa, and Portalegre by their total "
            "forest cover (coniferous + broadleaf) using the BigEarthNet data."
        ),
        "data_files": ["bigearthnet_portugal_stats.json"],
        "outputs": [
            "forest_cover_rank.csv",
            "forest_cover_rank.json",
            "forest_cover_rank_chart.png",
        ],
        "notes": (
            "Total forest cover must be class 1 Coniferous Forest plus class 2 Broadleaf Forest. "
            "Do not include shrubland or grassland in forest cover."
        ),
    },
    "gn_v5_21_compare_co2_candidate_pool": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_21_comparison_close_values",
        "category": "comparison",
        "difficulty": "medium",
        "method_family": "close-value comparison and indicator interpretation",
        "task": (
            "Compare CO2 geological storage suitability between Murcia and Cordoba. "
            "Which province is better suited?"
        ),
        "data_files": ["province_rankings.json", "layers_registry.yaml"],
        "outputs": [
            "murcia_cordoba_co2_comparison.csv",
            "murcia_cordoba_co2_decision.json",
            "murcia_cordoba_co2_chart.png",
        ],
        "notes": (
            "GeoNatureAgent layer notes say the candidate pool is class 2 Eligible plus "
            "class 1 Conditional. Report not eligible, conditional, eligible, candidate_pool, "
            "and make the final decision using candidate_pool."
        ),
    },
    "gn_v5_44_andalucia_average_co2": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_44_province_aggregation_andalucia",
        "category": "province_aggregation",
        "difficulty": "hard",
        "method_family": "administrative aggregation",
        "task": "What is the average CO2 storage eligibility percentage across all provinces in Andalucia?",
        "data_files": ["province_rankings.json", "spain_admin_index.json"],
        "outputs": [
            "andalucia_co2_province_values.csv",
            "andalucia_co2_average.json",
            "andalucia_co2_average_chart.png",
        ],
        "notes": (
            "Use the provinces whose ccaa_name is Andalucía in spain_admin_index.json. "
            "Average eligible_pct across those provinces because only province-level percentages "
            "are available in province_rankings.json. Do not include municipalities."
        ),
    },
    "gn_v5_49_threshold_co2_high": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_49_threshold_co2_high",
        "category": "threshold",
        "difficulty": "medium",
        "method_family": "threshold filtering",
        "task": "Which provinces in Spain have more than 70% of their territory eligible for CO2 storage?",
        "data_files": ["province_rankings.json"],
        "outputs": [
            "co2_eligible_gt70.csv",
            "co2_eligible_gt70.json",
        ],
        "notes": (
            "Use eligible_pct only, and apply a strict greater-than 70% threshold. "
            "Do not use >= 70 and do not add conditional_pct."
        ),
    },
    "gn_v5_50_dual_indicator_high_priority": {
        "source_project": "GeoNatureAgent Benchmark",
        "paper_case_id": "V5_50_threshold_dual_indicator",
        "category": "threshold",
        "difficulty": "hard",
        "method_family": "cross-indicator threshold filtering",
        "task": (
            "Find provinces where mean gully erosion exceeds 65% AND CO2 eligibility exceeds 60%. "
            "These would be high-priority areas needing both reforestation and geological storage."
        ),
        "data_files": ["province_rankings.json"],
        "outputs": [
            "dual_indicator_high_priority.csv",
            "dual_indicator_high_priority.json",
            "dual_indicator_high_priority_chart.png",
        ],
        "notes": (
            "Both thresholds are strict greater-than comparisons. Use erosion.mean_pct and "
            "co2.eligible_pct; do not use max erosion or conditional CO2."
        ),
    },
    "gbx_port_murcia_50km_buffer_intersections": {
        "source_project": "GeoBenchX tools ported in GeoNatureAgent Benchmark",
        "paper_case_id": "GeoBenchX-style spatial relationship task",
        "category": "spatial_reasoning",
        "difficulty": "medium",
        "method_family": "metric buffering and topological predicate selection",
        "task": (
            "Create a 50 km buffer around the province of Murcia and list all Spanish provinces "
            "whose geometry intersects that buffer. Save the buffer and selected provinces."
        ),
        "data_files": ["spain_provinces.geojson"],
        "outputs": [
            "murcia_50km_buffer.geojson",
            "murcia_50km_intersecting_provinces.csv",
            "murcia_50km_intersections_map.png",
        ],
        "notes": (
            "Use a projected CRS with metre units before buffering. Use the intersects predicate "
            "against the 50 km buffer, not within or contains. Preserve EPSG:4326 in GeoJSON outputs."
        ),
    },
}


SYSTEM_PROMPT = """You are a GIS analyst writing reproducible Python scripts.
Return only a complete Python script. Do not include Markdown fences.
Use local data files exactly as given. Write all requested outputs into the current working directory.
Prefer pandas/geopandas/matplotlib/json/shapely. Do not call external services or download data.
Keep the code deterministic and non-interactive; use Matplotlib Agg if plotting.
"""


def data_locations(task_def: dict) -> list[str]:
    return [str(DATA_ROOT / name) for name in task_def["data_files"]]


def build_user_prompt(task_id: str, task_def: dict) -> str:
    files = "\n".join(f"- {path}" for path in data_locations(task_def))
    outputs = "\n".join(f"- {name}" for name in task_def["outputs"])
    return f"""Source project: {task_def['source_project']}
Paper case id: {task_def['paper_case_id']}
Benchmark category: {task_def['category']}
Difficulty: {task_def['difficulty']}
Spatial method family: {task_def['method_family']}

Task:
{task_def['task']}

Local data files:
{files}

Important GIS/data interpretation notes:
{task_def['notes']}

Required outputs:
{outputs}

Write a single complete Python script that performs the task and saves the requested outputs.
"""


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def call_openai_compatible(api_key: str, base_url: str, model: str, prompt: str, timeout: int) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "stream": False,
    }
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def run_code(run_dir: Path, code_path: Path, python_exe: str, timeout: int) -> dict:
    proc = subprocess.run(
        [python_exe, str(code_path)],
        cwd=str(run_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return {"returncode": proc.returncode, "output": proc.stdout}


def serialize_output_files(run_dir: Path) -> list[str]:
    return [
        str(path.relative_to(run_dir))
        for path in sorted(run_dir.rglob("*"))
        if path.is_file()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    parser.add_argument("--model", default=os.environ.get("GEONATURE_MODEL", "deepseek-v4-pro"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1"))
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent / "runs"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--request-timeout", type=int, default=120)
    parser.add_argument("--execution-timeout", type=int, default=120)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable: {args.api_key_env}")

    task_def = TASKS[args.task_id]
    missing = [name for name in task_def["data_files"] if not (DATA_ROOT / name).exists()]
    if missing:
        raise RuntimeError(f"Missing local data file(s): {', '.join(missing)}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"{timestamp}_{args.task_id}_{args.model}"
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_user_prompt(args.task_id, task_def)
    metadata = {
        "source_project": task_def["source_project"],
        "paper_case_id": task_def["paper_case_id"],
        "task_id": args.task_id,
        "category": task_def["category"],
        "difficulty": task_def["difficulty"],
        "method_family": task_def["method_family"],
        "task": task_def["task"],
        "notes": task_def["notes"],
        "data_files": task_def["data_files"],
        "data_locations": data_locations(task_def),
        "required_outputs": task_def["outputs"],
        "model": args.model,
        "base_url": args.base_url,
        "started_at": timestamp,
        "status": "started",
    }
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (run_dir / "metadata_start.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    log_lines = []
    try:
        response_text = call_openai_compatible(
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            prompt=prompt,
            timeout=args.request_timeout,
        )
        (run_dir / "model_response.txt").write_text(response_text, encoding="utf-8")
        code = extract_code(response_text)
        (run_dir / "generated_code.py").write_text(code, encoding="utf-8")
        result = run_code(run_dir, run_dir / "generated_code.py", args.python_exe, args.execution_timeout)
        log_lines.append(result["output"])
        metadata["execution_returncode"] = result["returncode"]
        metadata["status"] = "completed" if result["returncode"] == 0 else "failed"
        missing_outputs = [name for name in task_def["outputs"] if not (run_dir / name).exists()]
        metadata["missing_required_outputs"] = missing_outputs
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        (run_dir / "run.log").write_text("\n".join(log_lines), encoding="utf-8", errors="replace")
        metadata["finished_at"] = time.strftime("%Y%m%d_%H%M%S")
        metadata["output_files"] = serialize_output_files(run_dir)
        (run_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps({"run_dir": str(run_dir), "status": metadata["status"]}, ensure_ascii=False))
    return 0 if metadata["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
