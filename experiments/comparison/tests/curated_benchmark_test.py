from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.comparison.adapters.benchmark_loader import (
    CURATED_INVALID_BENCHMARK_TASKS,
    load_benchmark_tasks,
    split_invalid_benchmark_tasks,
    split_manual_review_tasks,
)
from experiments.comparison.adapters.evaluator import CuratedGeoAgentEvaluatorAdapter
from experiments.comparison.host_runtime.executors import _ensure_required_stdlib_imports, _validate_llm_code
from experiments.comparison.host_runtime.multi_agent import _read_step_report
from experiments.comparison.host_runtime.models import BenchmarkTask
from experiments.comparison.plugins.error_aware.plugin import ErrorAwarePlugin


CURATED_CASES_PATH = Path(
    r"F:\29145008\curated_geoagent_dataset (2)\curated_geoagent_dataset"
    r"\curated_geoagent_dataset\cases.json"
)

MANUAL_REVIEW_TASKS = [
    "curated_geoagent_002",
    "curated_geoagent_010",
    "curated_geoagent_011",
    "curated_geoagent_012",
    "curated_geoagent_013",
    "curated_geoagent_054",
    "curated_geoagent_057",
    "curated_geoagent_058",
    "curated_geoagent_074",
    "curated_geoagent_075",
    "curated_geoagent_076",
    "curated_geoagent_093",
    "curated_geoagent_127",
    "curated_geoagent_135",
]

PRIVATE_AGENT_VIEW_KEYS = {
    "benchmark_format",
    "dataset_root",
    "evaluation",
    "evaluation_mode",
    "evaluator",
    "manual_rubric",
    "missing_paths",
    "asset_resolution_status",
    "scoring",
    "gold_labels",
    "ground_truth",
    "reference_output",
    "reference_outputs",
    "expected_error",
    "error_mechanism",
    "primary_label",
    "secondary_labels",
    "source_id",
}


def main() -> None:
    if not CURATED_CASES_PATH.is_file():
        print(f"skip: CuratedGeoAgent cases.json not found at {CURATED_CASES_PATH}")
        return

    tasks = load_benchmark_tasks(CURATED_CASES_PATH)
    assert len(tasks) == 140
    assert tasks[0].task_id == "curated_geoagent_001"
    assert tasks[0].complexity == "basic"
    assert tasks[0].input_paths and all(Path(path).is_absolute() for path in tasks[0].input_paths)
    assert "residential_roads.shp" in tasks[0].expected_outputs

    manual_ids = [task.task_id for task in tasks if task.requires_visual_check]
    assert manual_ids == MANUAL_REVIEW_TASKS
    auto_tasks, manual_review_tasks = split_manual_review_tasks(tasks)
    assert len(auto_tasks) == 126
    assert len(manual_review_tasks) == 14
    valid_auto_tasks, invalid_benchmark_tasks = split_invalid_benchmark_tasks(auto_tasks)
    assert len(valid_auto_tasks) == 121
    assert {task.task_id for task in invalid_benchmark_tasks} == set(CURATED_INVALID_BENCHMARK_TASKS)
    assert [task.task_id for task in manual_review_tasks] == MANUAL_REVIEW_TASKS
    assert {task.scoring["evaluation_mode"] for task in auto_tasks} == {"constraint", "gt"}
    assert {task.scoring["evaluation_mode"] for task in manual_review_tasks} == {"hybrid", "manual"}

    for task in tasks:
        agent_view = task.agent_view()
        _assert_no_private_keys(agent_view)
        text = json.dumps(agent_view, ensure_ascii=False).lower()
        assert "evaluate.py" not in text
        assert "manual_rubric" not in text
        assert "standard answer" not in text
        assert "answer_key" not in text
        assert "reference_output" not in text
        assert "sample_id" not in text
        assert not re.search(r"\b[a-e][1-3]\b", text)

    assert tasks[0].scoring["benchmark_format"] == "curated_geoagent"
    assert tasks[0].scoring["evaluator"] == "evaluation/task_001/evaluate.py"
    assert tasks[0].scoring["evaluation_mode"] == "gt"

    manual_task = next(task for task in tasks if task.task_id == "curated_geoagent_002")
    manual_result = CuratedGeoAgentEvaluatorAdapter().evaluate(
        task=manual_task,
        agent_kind="self_debug_multi_agent",
        attempt_index=0,
        output_path=REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_manual_probe",
        repair_mode="none",
    )
    assert manual_result.agent_visible_report.status == "FAIL"
    assert manual_result.agent_visible_report.failure_kind == "manual_review_required"
    assert manual_result.scoring_report.details["manual_review_required"] is True
    assert "manual_rubric" not in json.dumps(manual_result.agent_visible_report.__dict__, ensure_ascii=False)

    hybrid_task = next(task for task in tasks if task.task_id == "curated_geoagent_057")
    hybrid_result = CuratedGeoAgentEvaluatorAdapter().evaluate(
        task=hybrid_task,
        agent_kind="error_aware_multi_agent",
        attempt_index=0,
        output_path=REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_hybrid_probe",
        repair_mode="none",
    )
    assert hybrid_result.agent_visible_report.status == "FAIL"
    assert hybrid_result.agent_visible_report.failure_kind == "manual_review_required"
    assert hybrid_result.scoring_report.details["evaluation_mode"] == "hybrid"

    _assert_fake_evaluator_keeps_private_details_off_agent_visible_report()
    _assert_error_aware_nearest_connector_signal_prefers_d2()
    _assert_error_aware_raster_signal_prefers_b2_b3()
    _assert_error_aware_does_not_prioritize_a2_from_prompt_only()
    _assert_error_aware_targeted_playbooks_are_available()
    _assert_error_aware_uses_reported_failed_step_for_branch()
    _assert_error_aware_overrides_generic_reported_step_for_task_specific_signal()
    _assert_error_aware_line_vertex_and_protected_road_playbooks_are_available()
    _assert_error_aware_ignores_placeholder_suspected_issue()
    _assert_list_root_workflow_steps_are_normalized()
    _assert_error_aware_contour_signal_overrides_line_vertex_step()
    _assert_error_aware_polygon_difference_not_confused_with_voronoi()
    _assert_evaluator_shapely_normalize_compatibility()
    _assert_invalid_curated_task_is_flagged_not_scored()
    _assert_executor_adds_missing_os_import()
    _assert_executor_rejects_relative_output_dir()
    _assert_executor_rejects_unsupported_gis_api()
    _assert_error_aware_hillshade_negative_correlation_condition()
    _assert_error_aware_zonal_landscan_mask_contracts()
    _assert_error_aware_new_kernel_mappings_are_available()
    _assert_error_aware_branch_routing_regressions_are_fixed()
    print("curated benchmark ok: 140 tasks load, agent view is private-field clean, evaluator split holds")


def _assert_no_private_keys(value: object) -> None:
    if isinstance(value, dict):
        forbidden = PRIVATE_AGENT_VIEW_KEYS & set(value)
        assert not forbidden, f"private keys leaked to agent view: {sorted(forbidden)}"
        for child in value.values():
            _assert_no_private_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_private_keys(child)


def _assert_fake_evaluator_keeps_private_details_off_agent_visible_report() -> None:
    dataset_root = REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_fake_dataset"
    evaluator_path = dataset_root / "evaluation" / "task_999" / "evaluate.py"
    output_path = dataset_root / "candidate_outputs"
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_text(
        "\n".join(
            [
                "import json",
                "print(json.dumps({",
                "  'case_id': 'curated_geoagent_999',",
                "  'verdict': 'fail',",
                "  'score': 0.25,",
                "  'checks': [",
                "    {'name': 'artifact_exists', 'passed': True},",
                "    {'name': 'geometry_metric', 'passed': False, 'gold_value': 42, 'reference_path': 'secret_gt.shp', 'actual': {'crs': 'EPSG:3857', 'feature_count': 3}}",
                "    ,{'name': 'point_coordinate_multiset', 'passed': False, 'gold_value': 'secret', 'actual': {'feature_count': 2}}",
                "  ],",
                "  'metrics': {'private_reference_path': 'secret_gt.shp'},",
                "  'warnings': []",
                "}))",
                "",
            ]
        ),
        encoding="utf-8",
    )
    task = BenchmarkTask(
        task_id="curated_geoagent_999",
        prompt="Synthetic adapter split test.",
        input_paths=[],
        expected_outputs=[],
        complexity="basic",
        scoring={
            "benchmark_format": "curated_geoagent",
            "dataset_root": dataset_root.as_posix(),
            "evaluation_mode": "gt",
            "evaluator": "evaluation/task_999/evaluate.py",
            "manual_review_required": False,
        },
    )
    result = CuratedGeoAgentEvaluatorAdapter().evaluate(
        task=task,
        agent_kind="error_aware_multi_agent",
        attempt_index=0,
        output_path=output_path,
        repair_mode="none",
    )
    visible_text = json.dumps(result.agent_visible_report.__dict__, ensure_ascii=False).lower()
    scoring_text = json.dumps(result.scoring_report.__dict__, ensure_ascii=False).lower()
    assert result.agent_visible_report.status == "FAIL"
    assert result.agent_visible_report.failure_kind in {"missing_output", "metric_mismatch"}
    assert "secret_gt" not in visible_text
    assert "gold_value" not in visible_text
    assert "reference_path" not in visible_text
    assert "failed_check_details" in visible_text
    assert "epsg:3857" in visible_text
    assert "line vertex extraction contract" in visible_text
    assert "secret_gt" in scoring_text
    assert "gold_value" in scoring_text


def _assert_error_aware_nearest_connector_signal_prefers_d2() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_nearest_connector_probe",
            "prompt": (
                "Create a shortest connector from each source point to the nearest target line, "
                "preserve source order, compute distance, and apply an IQR outlier filter."
            ),
            "input_paths": [],
            "expected_outputs": ["nearest_connectors.shp"],
        },
        generated_code="candidate_idxs = list(sindex.intersection(point.bounds))",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: connector_geometry_feature_count"],
            "metrics_diff": {
                "failed_checks": [
                    "connector_geometry_feature_count",
                    "connector_geometry_total_length",
                    "connector_geometry_hausdorff_global",
                ]
            },
            "requires_visual_check": False,
        },
    )
    assert diagnosis["classification_basis"]["primary_candidate"] == "D2. Spatial Allocation Error"
    assert "B1. Dataset Integrity Violation" != diagnosis["candidate_labels"][0]
    advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
    assert "最近" in advice_text
    assert "包围盒候选" in advice_text


def _assert_error_aware_raster_signal_prefers_b2_b3() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_raster_semantic_probe",
            "prompt": "Clip a DEM raster, preserve georeferencing, NoData, and create derived contour/hillshade outputs.",
            "input_paths": [],
            "expected_outputs": ["clipped_dem.tif"],
        },
        generated_code="profile.update(transform=from_origin(0, 0, 1, 1)); data = np.nan_to_num(data, nan=0)",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: transform", "Failed check: nodata_mask"],
            "metrics_diff": {
                "failed_checks": ["transform", "nodata_mask"],
                "failed_check_hints": [
                    {"check": "transform", "semantic_hint": "Raster grid/affine transform contract failed."},
                    {"check": "nodata_mask", "semantic_hint": "Missing-data contract failed."},
                ],
                "failed_check_details": [{"name": "transform"}, {"name": "nodata_mask"}],
            },
            "requires_visual_check": False,
        },
    )
    labels = diagnosis["candidate_labels"]
    assert labels[0] in {"B2. Raster Alignment Failure", "B3. Missing Data Misinterpretation"}
    assert "B2. Raster Alignment Failure" in labels
    assert "B3. Missing Data Misinterpretation" in labels
    assert diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] in {
        "raster_processing",
        "raster_contour_generation",
    }
    advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
    assert "transform" in advice_text
    assert "NoData" in advice_text
    assert "from_origin" in advice_text


def _assert_error_aware_does_not_prioritize_a2_from_prompt_only() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_crs_prompt_only_probe",
            "prompt": "Clip features and output the result in the source CRS EPSG:4326.",
            "input_paths": [],
            "expected_outputs": ["features.shp"],
        },
        generated_code="result = gdf.head(1)",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "format_or_schema_error",
            "failure_reasons": ["Failed check: feature_count"],
            "metrics_diff": {"failed_checks": ["feature_count"]},
            "requires_visual_check": False,
        },
    )
    assert diagnosis["classification_basis"]["primary_candidate"] != "A2. CRS Inconsistency"


def _assert_error_aware_targeted_playbooks_are_available() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    probes = [
        (
            {
                "task_id": "synthetic_dem_clip_probe",
                "prompt": "Clip the DEM to a polygon boundary, crop to the minimum covering extent, and set pixels outside the union to NoData.",
                "input_paths": [],
                "expected_outputs": ["pa_dem_clipped.tif"],
            },
            ["raster_shape", "nodata_mask", "dem_values"],
            "B2. Raster Alignment Failure",
            ["rasterio.mask.mask", "geometry_mask", "NoData"],
        ),
        (
            {
                "task_id": "synthetic_dem_slope_sampling_probe",
                "prompt": (
                    "Calculate DEM slope in degrees from x/y central finite differences using raster pixel sizes. "
                    "Sample each building centroid by nearest raster cell."
                ),
                "input_paths": [],
                "expected_outputs": ["building_centroid_slope.shp"],
            },
            ["centroid_slope_values"],
            "B2. Raster Alignment Failure",
            ["坡度", "pixel size", "row/col"],
        ),
        (
            {
                "task_id": "synthetic_hillshade_geographic_probe",
                "prompt": (
                    "Generate hillshade from a geographic DEM using azimuth 315 and altitude 45, "
                    "converting pixel spacing to metres at the raster centre latitude."
                ),
                "input_paths": [],
                "expected_outputs": ["hillshade.tif"],
            },
            ["hillshade_agreement"],
            "B2. Raster Alignment Failure",
            ["hillshade", "row 增大代表向南", "azimuth", "uint8"],
        ),
        (
            {
                "task_id": "synthetic_nearest_matching_probe",
                "prompt": (
                    "For each ground truth location, find the nearest estimated location within 3 meters "
                    "and report matched count and mean location error."
                ),
                "input_paths": [],
                "expected_outputs": ["trunk_location_matches.shp", "location_error_summary.txt"],
            },
            ["matched_ground_truth_geometry_key_set"],
            "D2. Spatial Allocation Error",
            ["ground-truth", "阈值", "mean error"],
        ),
        (
            {
                "task_id": "synthetic_road_overlay_probe",
                "prompt": (
                    "Clip road features by province polygons and bind prov_id, prov_name, pinyin, "
                    "prov_code, and seg_len_m to every road segment."
                ),
                "input_paths": [],
                "expected_outputs": ["province_road_overlay.shp"],
            },
            ["artifact_province_road_overlay_shp_exists", "road_records_and_counts"],
            "C1. Topological Predicate Confusion",
            ["省界裁剪", "prov_id", "seg_len_m"],
        ),
        (
            {
                "task_id": "synthetic_bounded_voronoi_probe",
                "prompt": "Create one bounded Voronoi polygon for each input point using the convex hull as clipping boundary.",
                "input_paths": [],
                "expected_outputs": ["voronoi_polygons.shp"],
            },
            ["voronoi_polygons_global", "voronoi_polygons_by_feature"],
            "C1. Topological Predicate Confusion",
            ["Voronoi", "裁剪", "cell.intersection", "输入点"],
        ),
        (
            {
                "task_id": "synthetic_contour_probe",
                "prompt": "Reproject a DEM, treat value 0 as NoData, and generate positive-elevation contour lines every 50 meters.",
                "input_paths": [],
                "expected_outputs": ["puerto_contours_50m.shp"],
            },
            ["contours_by_elevation"],
            "B2. Raster Alignment Failure",
            ["NoData", "半像元", "zero-length", "row/col", "elevation", "按 elevation 分组"],
        ),
        (
            {
                "task_id": "synthetic_zonal_stats_probe",
                "prompt": "Provide pixel statistics inside each polygon using pixel-center inclusion and write stat_min/stat_max/stat_mean/stat_std/stat_sum.",
                "input_paths": [],
                "expected_outputs": ["tract_population_statistics.shp"],
            },
            ["zonal_statistics"],
            "D2. Spatial Allocation Error",
            ["pixel-center", "all_touched=False", "Window", "lon/lat", "ddof=0", "stat_sum"],
        ),
        (
            {
                "task_id": "synthetic_landscan_stats_probe",
                "prompt": "Summarize LandScan population pixels for each polygon and write s_fid, px_count, pop_sum, pop_mean, pop_min, and pop_max.",
                "input_paths": [],
                "expected_outputs": ["laramie_landscan_stats.shp"],
            },
            ["landscan_statistics_numeric_fields"],
            "D2. Spatial Allocation Error",
            ["LandScan", "s_fid", "px_count", "pop_sum", "数值字段"],
        ),
        (
            {
                "task_id": "synthetic_raster_reproject_probe",
                "prompt": "Reproject the DEM to EPSG:6569 with 30 meter cell size using nearest-neighbor resampling.",
                "input_paths": [],
                "expected_outputs": ["reprojected_dem.tif"],
            },
            ["crs", "pixel_size", "spatial_extent"],
            "B2. Raster Alignment Failure",
            ["calculate_default_transform", "30", "nearest-neighbor"],
        ),
        (
            {
                "task_id": "synthetic_statefp_filter_probe",
                "prompt": "Keep contiguous United States counties by excluding STATEFP codes 02, 15, 60, 66, 69, 72, and 78.",
                "input_paths": [],
                "expected_outputs": ["contiguous_us_counties.shp"],
            },
            ["feature_count", "key_set"],
            "B1. Dataset Integrity Violation",
            ["STATEFP", "前导零", "原始属性"],
        ),
        (
            {
                "task_id": "synthetic_polygon_difference_probe",
                "prompt": "Remove the part of generated_polygon that overlaps with PACounties and merge the two Shapefiles.",
                "input_paths": [],
                "expected_outputs": ["counties_with_residual_polygon.shp"],
            },
            ["geometry_by_feature", "feature_count"],
            "C1. Topological Predicate Confusion",
            ["difference", "overlap", "merge"],
        ),
    ]
    for task_view, failed_checks, expected_primary, expected_terms in probes:
        diagnosis = plugin.diagnose_and_advise(
            task_view=task_view,
            generated_code="",
            execution_log="returncode=0",
            agent_visible_report={
                "status": "FAIL",
                "failure_kind": "metric_mismatch",
                "failure_reasons": [f"Failed check: {name}" for name in failed_checks],
                "metrics_diff": {"failed_checks": failed_checks},
                "requires_visual_check": False,
            },
        )
        assert diagnosis["classification_basis"]["primary_candidate"] == expected_primary
        advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
        for term in expected_terms:
            assert term in advice_text


def _assert_error_aware_uses_reported_failed_step_for_branch() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_step_branch_probe",
            "prompt": "Sample a raster at building centroids and write a Shapefile.",
            "input_paths": [],
            "expected_outputs": ["samples.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: centroid_slope_values"],
            "metrics_diff": {"failed_checks": ["centroid_slope_values"]},
            "requires_visual_check": False,
        },
        step_report={
            "schema_version": "0.1.0",
            "status": "reported",
            "steps": [
                {"step_id": "read_inputs", "name": "read inputs", "status": "completed"},
                {
                    "step_id": "sample_raster",
                    "name": "sample raster at centroids",
                    "status": "failed",
                    "suspected_issue": "sampled with wrong row/col transform",
                },
            ],
        },
    )
    branch = diagnosis["step_branch_plan"]
    assert branch["mode"] == "step_branch_repair"
    assert branch["suspected_failed_step"]["step_id"] == "sample_raster"
    assert branch["locked_prior_steps"][0]["step_id"] == "read_inputs"


def _assert_error_aware_overrides_generic_reported_step_for_task_specific_signal() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_protected_road_length_bad_step_probe",
            "prompt": "Compute road lengths inside each protected region. The protected region identifier is fid.",
            "input_paths": [],
            "expected_outputs": ["protected_region_road_lengths.shp"],
        },
        generated_code="intersection.groupby('fid')['length_m'].sum()",
        execution_log="KeyError: 'fid'",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "missing_output",
            "failure_reasons": ["Failed check: artifact_protected_region_road_lengths_shp_exists"],
            "metrics_diff": {"failed_checks": ["artifact_protected_region_road_lengths_shp_exists"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "failed",
            "steps": [
                {"step_id": "read_inputs", "name": "read inputs", "status": "completed"},
                {
                    "step_id": "normalize_crs_or_grid",
                    "name": "ensure CRS",
                    "status": "failed",
                    "suspected_issue": "'fid'",
                },
            ],
        },
    )
    branch_step = diagnosis["step_branch_plan"]["suspected_failed_step"]
    assert branch_step["step_id"] == "overlay_length_aggregation"
    assert branch_step["source"] == "inferred_from_failure_signal_over_reported_step"


def _assert_error_aware_line_vertex_and_protected_road_playbooks_are_available() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    line_diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_line_vertex_probe",
            "prompt": (
                "Convert every stored coordinate of each input LineString into a Point, including the repeated "
                "closing coordinate. Preserve the source index attribute and do not deduplicate coincident vertices."
            ),
            "input_paths": [],
            "expected_outputs": ["line_vertices.shp"],
        },
        generated_code="out = gdf.geometry.boundary.drop_duplicates()",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "silent_logic_error",
            "failure_reasons": ["Failed check: source_index_multiset", "Failed check: point_coordinate_multiset"],
            "metrics_diff": {"failed_checks": ["source_index_multiset", "point_coordinate_multiset"]},
            "requires_visual_check": False,
        },
    )
    assert line_diagnosis["classification_basis"]["primary_candidate"] == "B1. Dataset Integrity Violation"
    assert line_diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] == "geometry_vertex_extraction"
    line_advice = json.dumps(line_diagnosis["repair_advice"], ensure_ascii=False)
    assert "坐标多重集" in line_advice
    assert "闭合线" in line_advice
    assert "index 字段" in line_advice

    road_diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_protected_road_length_probe",
            "prompt": (
                "Compute road lengths inside each protected region in EPSG:32646 metres. Preserve every protected "
                "region feature, group clipped road lengths by fid, and add length_m."
            ),
            "input_paths": [],
            "expected_outputs": ["protected_region_road_lengths.shp"],
        },
        generated_code="joined = gpd.sjoin(roads, regions); joined['length_m'] = joined.geometry.length",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "format_or_schema_error",
            "failure_reasons": ["Failed check: road_length_attributes_numeric_fields"],
            "metrics_diff": {"failed_checks": ["road_length_attributes_numeric_fields"]},
            "requires_visual_check": False,
        },
    )
    assert road_diagnosis["classification_basis"]["primary_candidate"] == "D2. Spatial Allocation Error"
    assert road_diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] == "overlay_length_aggregation"
    road_advice = json.dumps(road_diagnosis["repair_advice"], ensure_ascii=False)
    assert "polygon 区域为主表" in road_advice
    assert "稳定聚合键" in road_advice
    assert "fid_1/fid_2" in road_advice
    assert "line-polygon intersection" in road_advice
    assert "LineString/MultiLineString" in road_advice
    assert "GeometryCollection" in road_advice
    assert "直接 .length" in road_advice
    assert "length_m" in road_advice


def _assert_error_aware_ignores_placeholder_suspected_issue() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_placeholder_step_issue_probe",
            "prompt": "Convert LineString coordinates to vertex Points and preserve index.",
            "input_paths": [],
            "expected_outputs": ["line_vertices.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "silent_logic_error",
            "failure_reasons": ["Failed check: point_coordinate_multiset"],
            "metrics_diff": {"failed_checks": ["point_coordinate_multiset"]},
            "requires_visual_check": False,
        },
        step_report={
            "schema_version": "0.1.0",
            "status": "reported",
            "steps": [
                {"step_id": "read_inputs", "name": "read inputs", "status": "success", "suspected_issue": None},
                {"step_id": "write_outputs", "name": "write outputs", "status": "success", "suspected_issue": "None"},
            ],
        },
    )
    assert diagnosis["step_branch_plan"]["suspected_failed_step"]["source"] == "inferred_from_failure_signal"
    assert diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] == "geometry_vertex_extraction"


def _assert_list_root_workflow_steps_are_normalized() -> None:
    output_dir = REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_step_report_probe"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "workflow_steps.json").write_text(
        json.dumps(
            [
                {
                    "step_id": "read_inputs",
                    "name": "read inputs",
                    "status": "completed",
                    "outputs": ["inputs"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = _read_step_report(output_dir)
    assert report["status"] == "reported"
    assert report["steps"][0]["step_id"] == "read_inputs"


def _assert_error_aware_contour_signal_overrides_line_vertex_step() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_contour_probe",
            "prompt": (
                "Reproject a DEM, treat 0 as NoData, and generate positive contour lines at a 50-meter interval. "
                "Write valid LineString geometries with id and elevation fields."
            ),
            "input_paths": [],
            "expected_outputs": ["puerto_contours_50m.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "silent_logic_error",
            "failure_reasons": ["Failed check: contours_by_elevation"],
            "metrics_diff": {"failed_checks": ["contours_by_elevation"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {"step_id": "read_inputs", "name": "read DEM", "status": "completed"},
                {
                    "step_id": "geometry_vertex_extraction",
                    "name": "generate LineString contours",
                    "status": "failed",
                    "suspected_issue": "contour lengths do not match by elevation",
                },
            ],
        },
    )
    assert diagnosis["classification_basis"]["primary_candidate"] == "B2. Raster Alignment Failure"
    branch_step = diagnosis["step_branch_plan"]["suspected_failed_step"]
    assert branch_step["step_id"] == "raster_contour_generation"
    assert branch_step["source"] == "inferred_from_failure_signal_over_reported_step"


def _assert_error_aware_polygon_difference_not_confused_with_voronoi() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_polygon_difference_source_identifier_probe",
            "prompt": (
                "Remove the part of generated_polygon that overlaps with PACounties, then merge the residual polygon "
                "with the counties into counties_with_residual_polygon.shp."
            ),
            "input_paths": [],
            "expected_outputs": ["counties_with_residual_polygon.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": [
                "Failed check: source_identifier_set",
                "Failed check: merged_geometries",
                "Failed check: county_attributes",
            ],
            "metrics_diff": {
                "failed_checks": ["source_identifier_set", "merged_geometries", "county_attributes"]
            },
            "requires_visual_check": False,
        },
    )
    assert diagnosis["classification_basis"]["primary_candidate"] == "C1. Topological Predicate Confusion"
    assert diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] == "polygon_difference_merge"
    advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
    assert "difference" in advice_text
    assert "Voronoi" not in advice_text


def _assert_evaluator_shapely_normalize_compatibility() -> None:
    python_executable = Path(r"F:\29145008\GeoAgent\.venv\Scripts\python.exe")
    if not python_executable.is_file():
        return
    dataset_root = REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_shapely_compat_dataset"
    evaluator_path = dataset_root / "evaluation" / "task_998" / "evaluate.py"
    output_path = dataset_root / "candidate_outputs"
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_text(
        "\n".join(
            [
                "import argparse",
                "import json",
                "import shapely",
                "from shapely.geometry import LineString",
                "",
                "def main():",
                "    parser = argparse.ArgumentParser()",
                "    parser.add_argument('--candidate-dir')",
                "    parser.parse_args()",
                "    ok = bool(shapely.equals_exact(LineString([(0, 0), (1, 1)]), LineString([(0, 0), (1, 1)]), tolerance=1e-9, normalize=True))",
                "    print(json.dumps({'case_id': 'curated_geoagent_998', 'verdict': 'pass' if ok else 'fail', 'score': 1.0 if ok else 0.0, 'checks': [{'name': 'normalize_compat', 'passed': ok}], 'metrics': {}, 'warnings': []}))",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main())",
            ]
        ),
        encoding="utf-8",
    )
    task = BenchmarkTask(
        task_id="curated_geoagent_998",
        prompt="Fake evaluator compatibility probe.",
        input_paths=[],
        expected_outputs=[],
        complexity="basic",
        requires_visual_check=False,
        metadata={},
        scoring={
            "benchmark_format": "curated_geoagent",
            "evaluation_mode": "gt",
            "manual_review_required": False,
            "dataset_root": dataset_root.as_posix(),
            "evaluator": "evaluation/task_998/evaluate.py",
        },
    )
    result = CuratedGeoAgentEvaluatorAdapter(python_executable=str(python_executable)).evaluate(
        task=task,
        agent_kind="baseline_multi_agent",
        attempt_index=0,
        output_path=output_path,
        repair_mode="none",
    )
    assert result.agent_visible_report.status == "PASS"


def _assert_invalid_curated_task_is_flagged_not_scored() -> None:
    tasks = load_benchmark_tasks(CURATED_CASES_PATH)
    invalid_task = next(task for task in tasks if task.task_id == "curated_geoagent_043")
    result = CuratedGeoAgentEvaluatorAdapter().evaluate(
        task=invalid_task,
        agent_kind="baseline_multi_agent",
        attempt_index=0,
        output_path=REPO_ROOT / "experiments" / "comparison" / "runs" / "curated_invalid_probe",
        repair_mode="none",
    )
    visible = result.agent_visible_report.__dict__
    scoring = result.scoring_report.__dict__
    assert visible["status"] == "FAIL"
    assert visible["failure_kind"] == "evaluator_dataset_issue"
    assert visible["metrics_diff"]["invalid_benchmark_task"] is True
    assert scoring["notes"] == "invalid_benchmark_task"
    assert scoring["details"]["invalid_benchmark_task"] is True


def _assert_executor_adds_missing_os_import() -> None:
    code = _ensure_required_stdlib_imports(
        "from __future__ import annotations\nfrom pathlib import Path\noutput_dir = Path(os.environ['OUTPUT_DIR'])\n"
    )
    assert "from __future__ import annotations\nimport os\n" in code
    compile(code, "<generated>", "exec")


def _assert_executor_rejects_relative_output_dir() -> None:
    unsafe_scripts = [
        "from pathlib import Path\nPath('output').mkdir(exist_ok=True)\n",
        "open('outputs/workflow_steps.json', 'w').write('{}')\n",
        "import os\nos.makedirs('output')\n",
    ]
    for script in unsafe_scripts:
        try:
            _validate_llm_code(script)
        except RuntimeError as exc:
            assert "relative_output" in str(exc)
        else:
            raise AssertionError("relative output path was not rejected")


def _assert_executor_rejects_unsupported_gis_api() -> None:
    _validate_llm_code("from rasterio.windows import transform as window_transform\nout = window_transform(window, src.transform)\n")
    _validate_llm_code("from rasterio.sample import sample_gen\nvalues = sample_gen(src, coords)\n")
    unsafe_scripts = [
        "import matplotlib._contour\n",
        "from rasterio.windows import window_transform\n",
        "from rasterio.sample import sample\n",
        "value = src.sample(coords, resampling='nearest')\n",
        "gdf.geometry.union_all()\n",
    ]
    for script in unsafe_scripts:
        try:
            _validate_llm_code(script)
        except RuntimeError as exc:
            assert "unsupported_api" in str(exc)
        else:
            raise AssertionError("unsupported GIS API was not rejected")


def _assert_error_aware_hillshade_negative_correlation_condition() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    diagnosis = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_hillshade_negative_correlation_probe",
            "prompt": "Generate a hillshade from a north-up DEM with azimuth and altitude parameters.",
            "input_paths": [],
            "expected_outputs": ["hillshade.tif"],
        },
        generated_code="hillshade = 255 - hillshade",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "silent_logic_error",
            "failure_reasons": ["Failed check: hillshade_agreement"],
            "metrics_diff": {
                "failed_checks": ["hillshade_agreement"],
                "diagnostic_hints": [
                    {
                        "check": "hillshade_agreement",
                        "diagnostic": "strong_negative_hillshade_correlation",
                    }
                ],
                "failed_check_details": [
                    {
                        "name": "hillshade_agreement",
                        "details": {"pixel_correlation": -0.94, "mean_absolute_error": 41.5},
                    }
                ],
            },
            "requires_visual_check": False,
        },
    )
    assert diagnosis["classification_basis"]["primary_candidate"] == "B2. Raster Alignment Failure"
    advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
    assert "强负相关" in advice_text
    assert "方向约定" in advice_text


def _assert_error_aware_zonal_landscan_mask_contracts() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    probes = [
        (
            "synthetic_zonal_mask_contract_probe",
            "Compute zonal statistics using pixel-center inclusion, integer raster windows, and NoData exclusion.",
            ["zonal_statistics"],
            ["同一个 valid_values", "round_offsets", "all_touched=False"],
        ),
        (
            "synthetic_landscan_mask_contract_probe",
            "Summarize LandScan population pixels and write s_fid, px_count, pop_sum, pop_mean, pop_min, pop_max.",
            ["landscan_statistics_numeric_fields"],
            ["px_count 必须等于", "同一 valid_values", "LandScan NoData"],
        ),
    ]
    for task_id, prompt, failed_checks, expected_terms in probes:
        diagnosis = plugin.diagnose_and_advise(
            task_view={
                "task_id": task_id,
                "prompt": prompt,
                "input_paths": [],
                "expected_outputs": ["stats.shp"],
            },
            generated_code="",
            execution_log="returncode=0",
            agent_visible_report={
                "status": "FAIL",
                "failure_kind": "metric_mismatch",
                "failure_reasons": [f"Failed check: {name}" for name in failed_checks],
                "metrics_diff": {
                    "failed_checks": failed_checks,
                    "diagnostic_hints": [
                        {
                            "check": failed_checks[0],
                            "diagnostic": "raster_polygon_valid_pixel_set_mismatch",
                        }
                    ],
                },
                "requires_visual_check": False,
            },
        )
        advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
        for term in expected_terms:
            assert term in advice_text


def _assert_error_aware_new_kernel_mappings_are_available() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    probes = [
        (
            {
                "task_id": "synthetic_distance_matrix_probe",
                "prompt": "Build a pairwise distance matrix between facilities with row and column labels.",
                "input_paths": [],
                "expected_outputs": ["facility_distance_matrix.csv"],
            },
            ["facility_index", "matrix_labels", "symmetric_zero_diagonal", "distance_values"],
            "D3. Spatial Statistical Misinterpretation",
            "pairwise_distance_matrix",
            ["零对角线", "对称", "行列标签"],
        ),
        (
            {
                "task_id": "synthetic_ruggedness_probe",
                "prompt": "Calculate terrain ruggedness statistics from a DEM using a local neighborhood window.",
                "input_paths": [],
                "expected_outputs": ["ruggedness_statistics.shp"],
            },
            ["ruggedness_statistics"],
            "D3. Spatial Statistical Misinterpretation",
            "terrain_ruggedness_statistics",
            ["局部", "NoData", "ruggedness"],
        ),
        (
            {
                "task_id": "synthetic_population_allocation_probe",
                "prompt": "Allocate block group population to affected polygons and preserve numeric population fields.",
                "input_paths": [],
                "expected_outputs": ["affected_blockgroups_population.shp"],
            },
            ["population_summary", "block_group_field_binding"],
            "D2. Spatial Allocation Error",
            "population_spatial_allocation",
            ["人口", "空间支持", "population"],
        ),
        (
            {
                "task_id": "synthetic_raster_sampling_probe",
                "prompt": "Sample raster values at checkpoints using nearest valid raster cells.",
                "input_paths": [],
                "expected_outputs": ["checkpoint_samples.shp"],
            },
            ["checkpoint_id_set", "nearest_sample_values"],
            "D2. Spatial Allocation Error",
            "raster_nearest_sampling_and_matching",
            ["最近有效像元", "row/col", "NoData"],
        ),
        (
            {
                "task_id": "synthetic_suitability_probe",
                "prompt": "Create a camping suitability raster from multiple aligned criteria and boolean thresholds.",
                "input_paths": [],
                "expected_outputs": ["camping_suitability.tif"],
            },
            ["suitability_mask"],
            "D3. Spatial Statistical Misinterpretation",
            "raster_boolean_suitability_mask",
            ["布尔", "阈值", "valid-data"],
        ),
    ]
    for task_view, failed_checks, expected_primary, expected_step, expected_terms in probes:
        diagnosis = plugin.diagnose_and_advise(
            task_view=task_view,
            generated_code="",
            execution_log="returncode=0",
            agent_visible_report={
                "status": "FAIL",
                "failure_kind": "metric_mismatch",
                "failure_reasons": [f"Failed check: {name}" for name in failed_checks],
                "metrics_diff": {"failed_checks": failed_checks},
                "requires_visual_check": False,
            },
        )
        assert diagnosis["classification_basis"]["primary_candidate"] == expected_primary
        assert diagnosis["step_branch_plan"]["suspected_failed_step"]["step_id"] == expected_step
        advice_text = json.dumps(diagnosis["repair_advice"], ensure_ascii=False)
        for term in expected_terms:
            assert term in advice_text


def _assert_error_aware_branch_routing_regressions_are_fixed() -> None:
    plugin = ErrorAwarePlugin(repo_root=REPO_ROOT)
    road = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_road_overlay_branch_probe",
            "prompt": "Clip roads by province polygons and write province road overlay records with road counts.",
            "input_paths": [],
            "expected_outputs": ["province_road_overlay.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: road_records_and_counts"],
            "metrics_diff": {"failed_checks": ["road_records_and_counts"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {
                    "step_id": "normalize_spatial_reference",
                    "name": "normalize CRS",
                    "status": "failed",
                    "suspected_issue": "length mismatch",
                }
            ],
        },
    )
    assert road["step_branch_plan"]["suspected_failed_step"]["step_id"] == "road_overlay_attribute_binding"

    road_reported_buffer = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_road_overlay_buffer_report_probe",
            "prompt": "Clip road features by province polygons and verify road records and counts.",
            "input_paths": [],
            "expected_outputs": ["province_road_overlay.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: road_records_and_counts"],
            "metrics_diff": {"failed_checks": ["road_records_and_counts"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {
                    "step_id": "buffer_and_count",
                    "name": "buffer and count",
                    "status": "failed",
                    "suspected_issue": "record count mismatch",
                }
            ],
        },
    )
    assert road_reported_buffer["step_branch_plan"]["suspected_failed_step"]["step_id"] == "road_overlay_attribute_binding"

    zonal = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_zonal_population_prompt_probe",
            "prompt": "Compute population raster zonal statistics inside each polygon.",
            "input_paths": [],
            "expected_outputs": ["population_statistics.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "silent_logic_error",
            "failure_reasons": ["Failed check: zonal_statistics"],
            "metrics_diff": {"failed_checks": ["zonal_statistics"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {
                    "step_id": "raster_statistics",
                    "name": "raster stats",
                    "status": "failed",
                    "suspected_issue": "stats mismatch",
                }
            ],
        },
    )
    assert zonal["step_branch_plan"]["suspected_failed_step"]["step_id"] == "raster_zonal_statistics"

    contour = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_contour_reproject_report_probe",
            "prompt": "Reproject a DEM and generate positive contour lines every 50 meters.",
            "input_paths": [],
            "expected_outputs": ["puerto_contours_50m.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "missing_output",
            "failure_reasons": ["Failed check: artifact_puerto_contours_50m_shp_exists"],
            "metrics_diff": {"failed_checks": ["artifact_puerto_contours_50m_shp_exists"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {
                    "step_id": "reproject_raster",
                    "name": "reproject raster",
                    "status": "failed",
                    "suspected_issue": "contour output missing",
                }
            ],
        },
    )
    assert contour["step_branch_plan"]["suspected_failed_step"]["step_id"] == "raster_contour_generation"

    rectangle = plugin.diagnose_and_advise(
        task_view={
            "task_id": "synthetic_min_rectangle_branch_probe",
            "prompt": "Create minimum area rectangles for each input polygon and preserve source attributes.",
            "input_paths": [],
            "expected_outputs": ["minimum_area_rectangles.shp"],
        },
        generated_code="",
        execution_log="returncode=0",
        agent_visible_report={
            "status": "FAIL",
            "failure_kind": "metric_mismatch",
            "failure_reasons": ["Failed check: minimum_area_rectangles.shp:geometry"],
            "metrics_diff": {"failed_checks": ["minimum_area_rectangles.shp:geometry"]},
            "requires_visual_check": False,
        },
        step_report={
            "status": "reported",
            "steps": [
                {
                    "step_id": "bounded_voronoi_geometry_construction",
                    "name": "wrong fallback geometry",
                    "status": "failed",
                    "suspected_issue": "geometry mismatch",
                }
            ],
        },
    )
    assert rectangle["step_branch_plan"]["suspected_failed_step"]["step_id"] == "minimum_bounding_geometry"


if __name__ == "__main__":
    main()
