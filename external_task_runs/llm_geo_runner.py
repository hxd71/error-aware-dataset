import argparse
import contextlib
import io
import json
import os
import sys
import time
import traceback
import types
from pathlib import Path


LLM_GEO_ROOT = Path(os.environ.get("LLM_GEO_ROOT", Path(__file__).resolve().parents[3] / "LLM-Geo"))


TASKS = {
    "covid_death_rate": {
        "task_name": "COVID_death_rate",
        "task": """1) Draw a choropleth map to show the death rate (death/case) of COVID-19 among the countiguous US counties. Use the accumulated COVID-19 data of 2020.12.31 to compute the death rate. Use scheme ='quantiles' when plotting the map. Set map projection to 'Conus Albers'. Set map size to 15*10 inches.
2) Draw a scatter plot to show the correlation and trend line of the death rate with the senior resident rate, including the r-square and p-value. Set data point transparency to 50%, regression line as red. Set figure size to 15*10 inches.""",
        "data_locations": [
            "COVID-19 data case in 2020 (county-level): https://github.com/nytimes/covid-19-data/raw/master/us-counties-2020.csv. This data is for daily accumulated COVID cases and deaths for each county in the US. There are 5 columns: date (format: 2021-02-01), county, state, fips, cases, deaths.",
            "Contiguous US county boundary (ESRI shapefile): https://github.com/gladcolor/spatial_data/raw/master/contiguous_counties.zip. The county FIPS column is 'GEOID'; map projection is EPSG:4269.",
            "Census data (ACS2020): https://raw.githubusercontent.com/gladcolor/spatial_data/master/Demography/ACS2020_5year_county.csv. The needed columns are: 'FIPS', 'Total Population', 'Total Population: 65 to 74 Years', 'Total Population: 75 to 84 Years', 'Total Population: 85 Years and Over'. Drop rows with NaN cells after loading the used columns.",
        ],
    },
    "hospital_accessibility_sc": {
        "task_name": "Hospital_accessibility_SC",
        "task": "For each zipcode area in South Carolina (SC), calculate the distance from the centroid of the zipcode area to its nearest hospital, and then create a choropleth distance map of zipcode area polygons (unit: km), also show the hospital.",
        "data_locations": [
            "SC zipcode boundary shapefile: https://github.com/GIBDUSC/test/raw/master/sc_zip_boundary.zip, the map projection is WGS1984.",
            "SC hospitals: https://github.com/gladcolor/spatial_data/raw/master/South_Carolina/SC_hospitals_with_emergency_room_cleaned.csv, location columns: longitude in 'Longitude' column, latitude in 'Latitude' column.",
        ],
    },
    "axis_order_sc_hospitals": {
        "task_name": "Axis_order_SC_hospitals",
        "task": "Create a point layer for South Carolina hospitals and overlay it on the South Carolina ZIP boundary map. The hospital CSV intentionally uses confusing column names: 'lat_x' is latitude in degrees north, and 'lon_y' is longitude in degrees west/east. Use x = longitude and y = latitude when constructing point geometry. Count how many hospital points fall inside the South Carolina ZIP boundary union. Save a map named axis_order_hospitals_map.png and a GeoJSON point layer named axis_order_hospitals_points.geojson.",
        "data_locations": [
            "SC ZIP boundary shapefile: https://github.com/GIBDUSC/test/raw/master/sc_zip_boundary.zip, CRS is WGS84.",
            "SC hospital CSV with intentionally confusing coordinate columns: local file SC_hospitals_axis_confusing.csv. Column 'lat_x' is latitude; column 'lon_y' is longitude. Correct point construction is x=lon_y, y=lat_x.",
        ],
    },
    "population_equal_interval_nc": {
        "task_name": "Population_equal_interval_NC",
        "task": "Join North Carolina Census tract population attributes to tract polygons and create a choropleth map of TotalPopulation. Use exactly five equal-interval classes, not quantiles and not natural breaks. Save the map as nc_population_equal_interval_map.png and save a CSV named nc_population_equal_interval_class_counts.csv with one row per class showing the class label and number of tracts in that class.",
        "data_locations": [
            "NC tract boundary shapefile: https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/tract_37_EPSG4326.zip. The tract ID column is 'GEOID'.",
            "NC tract population CSV file: https://github.com/gladcolor/LLM-Geo/raw/master/overlay_analysis/NC_tract_population.csv. The population is stored in 'TotalPopulation'. The tract ID column is 'GEOID'.",
        ],
    },
    "invalid_polygon_repair": {
        "task_name": "Invalid_polygon_repair",
        "task": "The input GeoJSON contains one self-intersecting invalid polygon and one valid polygon. Repair invalid polygon geometries before any area calculation, then calculate area in square kilometers in a projected CRS, save a repaired GeoJSON named repaired_polygons.geojson, and save a CSV named repaired_polygon_areas.csv with polygon id, original validity, repaired validity, and area_km2. Also save a PNG map named repaired_polygons_map.png.",
        "data_locations": [
            "Input polygons GeoJSON: local file invalid_polygons.geojson. It contains fields 'poly_id' and 'description'. One polygon is a bow-tie self-intersection and must be repaired before area calculation.",
        ],
    },
}


LOCAL_DATA = {
    "covid_death_rate": {
        "required_files": [
            "us-counties-2020.csv",
            "contiguous_counties.zip",
            "ACS2020_5year_county.csv",
        ],
        "data_locations": [
            "COVID-19 data case in 2020 (county-level): {data_root}\\us-counties-2020.csv. This data is for daily accumulated COVID cases and deaths for each county in the US. There are 5 columns: date (format: 2021-02-01), county, state, fips, cases, deaths.",
            "Contiguous US county boundary (ESRI shapefile): {data_root}\\contiguous_counties.zip. The county FIPS column is 'GEOID'; map projection is EPSG:4269.",
            "Census data (ACS2020): {data_root}\\ACS2020_5year_county.csv. The needed columns are: 'FIPS', 'Total Population', 'Total Population: 65 to 74 Years', 'Total Population: 75 to 84 Years', 'Total Population: 85 Years and Over'. Drop rows with NaN cells after loading the used columns.",
        ],
    },
    "hospital_accessibility_sc": {
        "required_files": [
            "sc_zip_boundary.zip",
            "SC_hospitals_with_emergency_room_cleaned.csv",
        ],
        "data_locations": [
            "SC zipcode boundary shapefile: {data_root}\\sc_zip_boundary.zip, the map projection is WGS1984.",
            "SC hospitals: {data_root}\\SC_hospitals_with_emergency_room_cleaned.csv, location columns: longitude in 'Longitude' column, latitude in 'Latitude' column.",
        ],
    },
    "axis_order_sc_hospitals": {
        "required_files": [
            "sc_zip_boundary.zip",
            "SC_hospitals_axis_confusing.csv",
        ],
        "data_locations": [
            "SC ZIP boundary shapefile: {data_root}\\sc_zip_boundary.zip, CRS is WGS84.",
            "SC hospital CSV with intentionally confusing coordinate columns: {data_root}\\SC_hospitals_axis_confusing.csv. Column 'lat_x' is latitude; column 'lon_y' is longitude. Correct point construction is x=lon_y, y=lat_x.",
        ],
    },
    "population_equal_interval_nc": {
        "required_files": [
            "tract_37_EPSG4326.zip",
            "NC_tract_population.csv",
        ],
        "data_locations": [
            "NC tract boundary shapefile: {data_root}\\tract_37_EPSG4326.zip. The tract ID column is 'GEOID'.",
            "NC tract population CSV file: {data_root}\\NC_tract_population.csv. The population is stored in 'TotalPopulation'. The tract ID column is 'GEOID'.",
        ],
    },
    "invalid_polygon_repair": {
        "required_files": [
            "invalid_polygons.geojson",
        ],
        "data_locations": [
            "Input polygons GeoJSON: {data_root}\\invalid_polygons.geojson. It contains fields 'poly_id' and 'description'. One polygon is a bow-tie self-intersection and must be repaired before area calculation.",
        ],
    },
}


def write_temp_config(work_dir: Path, api_key: str) -> Path:
    config_path = work_dir / "config.ini"
    config_path.write_text(f"[API_Key]\nOpenAI_key = {api_key}\n", encoding="utf-8")
    return config_path


def import_llm_geo(work_dir: Path, api_key: str, base_url: str):
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ.setdefault("MPLBACKEND", "Agg")
    config_path = write_temp_config(work_dir, api_key)
    os.chdir(work_dir)
    sys.path.insert(0, str(LLM_GEO_ROOT))
    if "pyvis.network" not in sys.modules:
        pyvis_module = types.ModuleType("pyvis")
        network_module = types.ModuleType("pyvis.network")

        class Network:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def from_nx(self, *args, **kwargs):
                return None

            def show(self, *args, **kwargs):
                return None

        network_module.Network = Network
        pyvis_module.network = network_module
        sys.modules.setdefault("pyvis", pyvis_module)
        sys.modules.setdefault("pyvis.network", network_module)
    try:
        from LLM_Geo_kernel import Solution
    finally:
        with contextlib.suppress(FileNotFoundError):
            config_path.unlink()
    return Solution


def force_noninteractive_matplotlib():
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    plt.show = lambda *args, **kwargs: None


def serialize_output_files(run_dir: Path) -> list[str]:
    return [
        str(path.relative_to(run_dir))
        for path in sorted(run_dir.rglob("*"))
        if path.is_file()
    ]


def resolve_task(task_id: str, data_mode: str, local_data_root: Path) -> dict:
    task_def = dict(TASKS[task_id])
    if data_mode != "local":
        return task_def

    if task_id not in LOCAL_DATA:
        raise RuntimeError(f"No local data mapping is defined for task: {task_id}")

    task_data_dir = local_data_root / task_id
    missing = [
        name for name in LOCAL_DATA[task_id]["required_files"]
        if not (task_data_dir / name).exists()
    ]
    if missing:
        raise RuntimeError(
            "Missing local data files under "
            f"{task_data_dir}: {', '.join(missing)}"
        )

    escaped_root = str(task_data_dir).replace("\\", "\\\\")
    task_def["data_locations"] = [
        item.format(data_root=escaped_root)
        for item in LOCAL_DATA[task_id]["data_locations"]
    ]
    task_def["data_mode"] = "local"
    task_def["local_data_root"] = str(task_data_dir)
    return task_def


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    parser.add_argument("--mode", choices=["direct", "full"], default="direct")
    parser.add_argument("--model", default=os.environ.get("LLM_GEO_MODEL", "deepseek-v4-pro"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1"))
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--debug-attempts", type=int, default=2)
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent / "runs"))
    parser.add_argument("--data-mode", choices=["url", "local"], default="url")
    parser.add_argument("--local-data-root", default=str(Path(__file__).resolve().parent / "data" / "llm_geo"))
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key environment variable: {args.api_key_env}")

    task_def = resolve_task(args.task_id, args.data_mode, Path(args.local_data_root))
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"{timestamp}_{args.task_id}_{args.mode}_{args.model}"
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "source_project": "LLM-Geo",
        "source_repo": str(LLM_GEO_ROOT),
        "task_id": args.task_id,
        "task_name": task_def["task_name"],
        "mode": args.mode,
        "model": args.model,
        "base_url": args.base_url,
        "debug_attempts": args.debug_attempts,
        "review": args.review,
        "data_mode": args.data_mode,
        "local_data_root": task_def.get("local_data_root"),
        "task": task_def["task"],
        "data_locations": task_def["data_locations"],
        "started_at": timestamp,
        "status": "started",
    }
    (run_dir / "metadata_start.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    log_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
            Solution = import_llm_geo(run_dir, api_key, args.base_url)
            force_noninteractive_matplotlib()
            solution = Solution(
                task=task_def["task"],
                task_name=task_def["task_name"],
                save_dir=str(run_dir),
                data_locations=task_def["data_locations"],
                model=args.model,
                stream=True,
                verbose=True,
            )

            if args.mode == "direct":
                solution.get_direct_request_LLM_response(review=args.review)
                code = solution.direct_request_code
                (run_dir / "generated_direct_code.py").write_text(code, encoding="utf-8")
                final_code = solution.execute_complete_program(code=code, try_cnt=args.debug_attempts)
                (run_dir / "final_direct_code.py").write_text(final_code, encoding="utf-8")
            else:
                solution.get_LLM_response_for_graph()
                solution.save_solution()
                operations = solution.get_LLM_responses_for_operations(review=args.review)
                all_operation_code = "\n".join([operation["operation_code"] for operation in operations])
                (run_dir / "generated_operation_code.py").write_text(all_operation_code, encoding="utf-8")
                solution.get_LLM_assembly_response(review=args.review)
                (run_dir / "generated_assembly_code.py").write_text(solution.code_for_assembly, encoding="utf-8")
                final_code = solution.execute_complete_program(
                    code=all_operation_code + "\n" + solution.code_for_assembly,
                    try_cnt=args.debug_attempts,
                )
                (run_dir / "final_full_code.py").write_text(final_code, encoding="utf-8")
                solution.save_solution()

            metadata["status"] = "completed"
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        (run_dir / "run.log").write_text(log_buffer.getvalue(), encoding="utf-8", errors="replace")
        metadata["finished_at"] = time.strftime("%Y%m%d_%H%M%S")
        metadata["output_files"] = serialize_output_files(run_dir)
        (run_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"run_dir": str(run_dir), "status": metadata["status"]}, ensure_ascii=False))
    return 0 if metadata["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
