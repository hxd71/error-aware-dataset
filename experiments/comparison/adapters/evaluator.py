from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from experiments.comparison.adapters.benchmark_loader import CURATED_INVALID_BENCHMARK_TASKS
from experiments.comparison.host_runtime.executors import _find_rasterio_proj_data
from experiments.comparison.host_runtime.models import (
    AgentKind,
    AgentVisibleReport,
    BenchmarkTask,
    EvaluationResult,
    ScoringReport,
)


class EvaluatorAdapter:
    """Interface for Task 3's future GIS verifier."""

    evaluator_name = "abstract"
    evaluator_version = "0.0.0"

    def evaluate(
        self,
        task: BenchmarkTask,
        agent_kind: AgentKind,
        attempt_index: int,
        output_path: Path,
        repair_mode: str,
    ) -> EvaluationResult:
        raise NotImplementedError


class MockEvaluator(EvaluatorAdapter):
    """Deterministic evaluator used only to validate the comparison framework."""

    evaluator_name = "mock_gis_evaluator"
    evaluator_version = "0.1.0"

    def evaluate(
        self,
        task: BenchmarkTask,
        agent_kind: AgentKind,
        attempt_index: int,
        output_path: Path,
        repair_mode: str,
    ) -> EvaluationResult:
        behavior = task.mock_behavior
        initial_status = behavior.get("initial_status", "FAIL")
        status = "PASS" if initial_status == "PASS" and attempt_index == 0 else "FAIL"
        execution_log_path = output_path.parent / "execution.log"
        generation_failed = (
            execution_log_path.exists()
            and execution_log_path.read_text(encoding="utf-8", errors="ignore").startswith(
                "Code generation failed before execution"
            )
        )
        if generation_failed:
            status = "FAIL"
        if attempt_index > 0:
            if agent_kind == "self_debug_multi_agent" and behavior.get("self_debug_can_fix", False):
                status = "PASS"
            if agent_kind == "error_aware_multi_agent" and behavior.get("error_aware_can_fix", False):
                status = "PASS"
            if generation_failed:
                status = "FAIL"

        visible = AgentVisibleReport(
            status=status,
            failure_kind="" if status == "PASS" else ("code_generation_error" if generation_failed else behavior.get("failure_kind", "silent_logic_error")),
            failure_reasons=[] if status == "PASS" else (["Code generation failed before execution."] if generation_failed else list(behavior.get("failure_reasons", []))),
            metrics_diff={} if status == "PASS" else dict(behavior.get("metrics_diff", {})),
            requires_visual_check=bool(task.requires_visual_check and status == "FAIL"),
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status=status,
            gold_labels=list(task.scoring.get("gold_labels", [])),
            leakage_risk=bool(task.scoring.get("leakage_risk", False)),
            notes=str(task.scoring.get("notes", "")),
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)


class CuratedGeoAgentEvaluatorAdapter(EvaluatorAdapter):
    """Adapter for the 140-task Curated GeoAgent benchmark evaluators."""

    evaluator_name = "curated_geoagent_task_evaluator"
    evaluator_version = "0.1.0"

    def __init__(self, python_executable: str | None = None, timeout_seconds: int = 300) -> None:
        self.python_executable = (
            python_executable
            or os.environ.get("CURATED_GEOAGENT_PYTHON")
            or sys.executable
        )
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        task: BenchmarkTask,
        agent_kind: AgentKind,
        attempt_index: int,
        output_path: Path,
        repair_mode: str,
    ) -> EvaluationResult:
        scoring_config = task.scoring
        mode = str(scoring_config.get("evaluation_mode") or "")
        manual_required = bool(scoring_config.get("manual_review_required", False))
        evaluator_rel = scoring_config.get("evaluator")
        dataset_root = Path(str(scoring_config.get("dataset_root", "")))

        if manual_required:
            return self._manual_result(task, output_path, scoring_config)

        if bool(scoring_config.get("invalid_benchmark_task", False)) or task.task_id in CURATED_INVALID_BENCHMARK_TASKS:
            reason = str(
                scoring_config.get("invalid_reason")
                or CURATED_INVALID_BENCHMARK_TASKS.get(task.task_id)
                or "invalid_benchmark_task"
            )
            return self._invalid_benchmark_result(task, output_path, scoring_config, reason)

        if not evaluator_rel:
            return self._configuration_error(
                task,
                output_path,
                scoring_config,
                "No evaluator is configured for this non-manual task.",
            )

        evaluator_path = (dataset_root / str(evaluator_rel)).resolve(strict=False)
        if not evaluator_path.is_file():
            return self._configuration_error(
                task,
                output_path,
                scoring_config,
                f"Evaluator script not found: {evaluator_rel}",
            )

        completed = self._run_evaluator(evaluator_path, dataset_root, output_path)
        raw_report = completed["report"]
        if completed["run_error"]:
            raw_report = {
                "case_id": task.task_id,
                "verdict": "error",
                "score": 0.0,
                "checks": [],
                "metrics": {},
                "warnings": [],
                "error": completed["run_error"],
            }

        return self._build_result(
            task=task,
            output_path=output_path,
            scoring_config=scoring_config,
            evaluator_path=evaluator_path,
            raw_report=raw_report,
            manual_required=manual_required,
            mode=mode,
            completed=completed,
        )

    def _run_evaluator(self, evaluator_path: Path, dataset_root: Path, output_path: Path) -> dict[str, Any]:
        try:
            env = os.environ.copy()
            shim_path = Path(__file__).with_name("evaluator_shims")
            existing_pythonpath = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                str(shim_path)
                if not existing_pythonpath
                else str(shim_path) + os.pathsep + existing_pythonpath
            )
            proj_data = _find_rasterio_proj_data(self.python_executable)
            if proj_data is not None:
                env.pop("PROJ_LIB", None)
                env["PROJ_DATA"] = str(proj_data)
                env["PROJ_NETWORK"] = "OFF"
            completed = subprocess.run(
                [
                    self.python_executable,
                    str(evaluator_path),
                    "--candidate-dir",
                    str(output_path.resolve(strict=False)),
                ],
                cwd=str(dataset_root),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=self.timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "report": {},
                "run_error": f"Evaluator timed out after {self.timeout_seconds} seconds.",
            }
        except Exception as exc:  # pragma: no cover - defensive guard for environment failures.
            return {
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "report": {},
                "run_error": f"Evaluator invocation failed: {exc}",
            }

        report, parse_error = _parse_json_object(completed.stdout)
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "report": report,
            "run_error": parse_error,
        }

    def _build_result(
        self,
        *,
        task: BenchmarkTask,
        output_path: Path,
        scoring_config: dict[str, Any],
        evaluator_path: Path,
        raw_report: dict[str, Any],
        manual_required: bool,
        mode: str,
        completed: dict[str, Any],
    ) -> EvaluationResult:
        verdict = str(raw_report.get("verdict", "error")).lower()
        auto_pass = verdict == "pass"
        status = "PASS" if auto_pass and not manual_required else "FAIL"
        failed_checks = _failed_checks(raw_report)
        visible = AgentVisibleReport(
            status=status,
            failure_kind="" if status == "PASS" else _failure_kind(raw_report, failed_checks, manual_required, auto_pass),
            failure_reasons=[] if status == "PASS" else _visible_failure_reasons(raw_report, failed_checks, manual_required, auto_pass),
            metrics_diff={} if status == "PASS" else _visible_metrics(raw_report, failed_checks, manual_required),
            requires_visual_check=manual_required,
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status=status,
            leakage_risk=bool(scoring_config.get("leakage_risk", False)),
            notes=_scoring_notes(mode, manual_required, raw_report),
            details={
                "benchmark_format": scoring_config.get("benchmark_format"),
                "evaluation_mode": mode,
                "manual_review_required": manual_required,
                "manual_rubric": scoring_config.get("manual_rubric"),
                "evaluator": scoring_config.get("evaluator"),
                "evaluator_path": evaluator_path.as_posix(),
                "returncode": completed.get("returncode"),
                "stderr": completed.get("stderr", ""),
                "raw_report": raw_report,
            },
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)

    @staticmethod
    def _manual_result(
        task: BenchmarkTask,
        output_path: Path,
        scoring_config: dict[str, Any],
    ) -> EvaluationResult:
        visible = AgentVisibleReport(
            status="FAIL",
            failure_kind="manual_review_required",
            failure_reasons=["Manual review is required; automated checks alone cannot score this task."],
            metrics_diff={"manual_review_required": True},
            requires_visual_check=True,
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status="FAIL",
            notes="manual_review_required",
            details={
                "benchmark_format": scoring_config.get("benchmark_format"),
                "evaluation_mode": scoring_config.get("evaluation_mode"),
                "manual_review_required": True,
                "manual_rubric": scoring_config.get("manual_rubric"),
                "evaluator": scoring_config.get("evaluator"),
                "raw_report": None,
            },
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)

    @staticmethod
    def _configuration_error(
        task: BenchmarkTask,
        output_path: Path,
        scoring_config: dict[str, Any],
        message: str,
    ) -> EvaluationResult:
        visible = AgentVisibleReport(
            status="FAIL",
            failure_kind="evaluator_configuration_error",
            failure_reasons=[message],
            metrics_diff={},
            requires_visual_check=bool(scoring_config.get("manual_review_required", False)),
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status="FAIL",
            notes="evaluator_configuration_error",
            details={
                "benchmark_format": scoring_config.get("benchmark_format"),
                "evaluation_mode": scoring_config.get("evaluation_mode"),
                "manual_review_required": scoring_config.get("manual_review_required", False),
                "evaluator": scoring_config.get("evaluator"),
                "error": message,
            },
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)

    @staticmethod
    def _invalid_benchmark_result(
        task: BenchmarkTask,
        output_path: Path,
        scoring_config: dict[str, Any],
        reason: str,
    ) -> EvaluationResult:
        visible = AgentVisibleReport(
            status="FAIL",
            failure_kind="evaluator_dataset_issue",
            failure_reasons=[
                "This benchmark task is excluded from formal automatic scoring because its evaluator or source dataset is invalid."
            ],
            metrics_diff={
                "invalid_benchmark_task": True,
                "invalid_reason": reason,
            },
            requires_visual_check=False,
            output_path=output_path.as_posix(),
        )
        scoring = ScoringReport(
            status="FAIL",
            notes="invalid_benchmark_task",
            details={
                "benchmark_format": scoring_config.get("benchmark_format"),
                "evaluation_mode": scoring_config.get("evaluation_mode"),
                "manual_review_required": scoring_config.get("manual_review_required", False),
                "evaluator": scoring_config.get("evaluator"),
                "invalid_benchmark_task": True,
                "invalid_reason": reason,
                "raw_report": None,
            },
        )
        return EvaluationResult(agent_visible_report=visible, scoring_report=scoring)


def _parse_json_object(text: str) -> tuple[dict[str, Any], str]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return {}, "Evaluator did not emit a JSON object."
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        return {}, f"Evaluator emitted invalid JSON: {exc}"
    if not isinstance(parsed, dict):
        return {}, "Evaluator JSON payload is not an object."
    return parsed, ""


def _failed_checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        return []
    return [check for check in checks if isinstance(check, dict) and not bool(check.get("passed", False))]


def _failure_kind(
    report: dict[str, Any],
    failed_checks: list[dict[str, Any]],
    manual_required: bool,
    auto_pass: bool,
) -> str:
    if manual_required and auto_pass:
        return "manual_review_required"
    if report.get("error"):
        return "traceback_error"
    names = " ".join(str(check.get("name", "")) for check in failed_checks).lower()
    if any(token in names for token in ["artifact", "exists", "output"]):
        return "missing_output"
    if any(token in names for token in ["schema", "field", "column", "format", "readable", "type"]):
        return "format_or_schema_error"
    if any(token in names for token in ["iou", "distance", "length", "area", "numeric", "stats", "count", "mask", "nodata", "crs", "geometry"]):
        return "metric_mismatch"
    return "silent_logic_error"


def _visible_failure_reasons(
    report: dict[str, Any],
    failed_checks: list[dict[str, Any]],
    manual_required: bool,
    auto_pass: bool,
) -> list[str]:
    if manual_required and auto_pass:
        return ["Automated checks passed, but the task still requires manual review before scoring."]
    if report.get("error"):
        return ["Evaluator execution failed; see offline scoring_report.details for private diagnostics."]
    if not failed_checks:
        return ["The evaluator marked the output as failed without exposing task-safe check details."]
    return [f"Failed check: {check.get('name', 'unnamed_check')}" for check in failed_checks[:8]]


def _visible_metrics(
    report: dict[str, Any],
    failed_checks: list[dict[str, Any]],
    manual_required: bool,
) -> dict[str, Any]:
    checks = report.get("checks", [])
    check_count = len(checks) if isinstance(checks, list) else 0
    failed_names = [str(check.get("name", "unnamed_check")) for check in failed_checks[:8]]
    return {
        "score": report.get("score"),
        "check_count": check_count,
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_names,
        "failed_check_hints": [_safe_check_hint(name) for name in failed_names],
        "diagnostic_hints": _derived_agent_diagnostics(failed_checks),
        "failed_check_details": [_sanitize_check_for_agent(check) for check in failed_checks[:5]],
        "manual_review_required": manual_required,
    }


PRIVATE_VISIBLE_KEY = re.compile(
    r"(gold|reference|ground[_-]?truth|\bgt\b|answer|expected|rubric|dataset[_-]?root|evaluator|source[_-]?id|private)",
    flags=re.IGNORECASE,
)
PRIVATE_VISIBLE_VALUE = re.compile(
    r"([A-Za-z]:\\|/|reference|ground[_-]?truth|\bgt\b|gold|answer[_-]?key)",
    flags=re.IGNORECASE,
)


def _sanitize_check_for_agent(check: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in check.items():
        key_text = str(key)
        if PRIVATE_VISIBLE_KEY.search(key_text):
            continue
        if key_text == "passed":
            continue
        sanitized[key_text] = _sanitize_value_for_agent(value, depth=0)
        if len(sanitized) >= 8:
            break
    return sanitized


def _sanitize_value_for_agent(value: Any, *, depth: int) -> Any:
    if depth >= 3:
        return "[truncated]"
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if PRIVATE_VISIBLE_KEY.search(key_text):
                continue
            result[key_text] = _sanitize_value_for_agent(child, depth=depth + 1)
            if len(result) >= 8:
                break
        return result
    if isinstance(value, list):
        return [_sanitize_value_for_agent(item, depth=depth + 1) for item in value[:8]]
    if isinstance(value, str):
        if PRIVATE_VISIBLE_VALUE.search(value):
            return "[redacted_private_value]"
        return value[:500]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:300]


def _safe_check_hint(check_name: str) -> dict[str, str]:
    name = check_name.lower()
    hints = [
        (
            r"source_index_multiset|point_coordinate_multiset|line_vertices|coordinate_multiset",
            "Line vertex extraction contract failed: preserve every stored line coordinate as a Point, keep duplicate closing/coincident vertices, and preserve the source index field.",
        ),
        (
            r"road_length_attributes|length_m|protected_region_road_lengths",
            "Line-polygon allocation contract failed: compute clipped road segment lengths inside each polygon, group by the polygon identifier, and preserve every polygon feature.",
        ),
        (
            r"source_identifier_fields|source_identifier_set|merged_geometries|county_attributes",
            "Polygon difference/merge contract failed: remove overlap with the comparison layer, preserve source feature identities and attributes, and write a valid merged polygon layer.",
        ),
        (
            r"voronoi_polygons|building_voronoi|\bsource_id\b",
            "Bounded Voronoi contract failed: produce one finite clipped polygon per input centroid and bind the source identity field consistently.",
        ),
        (
            r"transform|pixel|grid|extent|bounds|window|alignment",
            "Raster grid/affine transform contract failed: preserve pixel size, origin, extent, and window-to-map alignment.",
        ),
        (
            r"nodata|mask|valid_pixel|background",
            "Missing-data contract failed: valid pixels, NoData value, and mask/background semantics must match the task output intent.",
        ),
        (
            r"contours_by_elevation",
            "Contour geometry contract failed: after schema and LineString health pass, the remaining issue is per-elevation length/coverage consistency; preserve the deterministic contour engine, DEM preprocessing, valid mask, row/column-to-map coordinate convention, and output CRS together.",
        ),
        (
            r"hillshade_agreement",
            "Hillshade contract failed: preserve the DEM profile/mask and compute illumination with correct azimuth/altitude convention, row direction, and x/y pixel spacing.",
        ),
        (
            r"zonal_statistics",
            "Zonal statistics contract failed: use polygon pixel-center inclusion on the raster grid, exclude NoData/masked pixels, and bind each statistic to the source polygon.",
        ),
        (
            r"landscan_statistics_numeric_fields",
            "LandScan population statistics contract failed: bind source feature identity and write px_count/pop_sum/pop_mean/pop_min/pop_max as numeric fields from the same valid-pixel set.",
        ),
        (
            r"crs|epsg|projection",
            "Spatial reference contract failed: output CRS metadata and coordinate domain must be compatible with the requested result.",
        ),
        (
            r"contour|elevation|line_geometry_health",
            "Raster-derived vector contract failed: contours must preserve elevation levels, coordinate transform, valid line geometry, and required attributes.",
        ),
        (
            r"hillshade|shade|illumination",
            "DEM rendering contract failed: hillshade should preserve DEM grid/profile semantics and use a stable illumination transform.",
        ),
        (
            r"connector|nearest|distance|hausdorff|dist_m|iqr|q1|q3",
            "Spatial allocation contract failed: each source object must be assigned to the intended target geometry under the task distance/filter semantics.",
        ),
        (
            r"schema|field|column|attribute|id_set|feature_count|geometry_type",
            "Spatial data representation contract failed: output features, fields, geometry type, and source identity must remain interpretable.",
        ),
    ]
    for pattern, hint in hints:
        if re.search(pattern, name):
            return {"check": check_name, "semantic_hint": hint}
    return {"check": check_name, "semantic_hint": "Evaluator exposed a task-safe failed check; inspect task intent and output semantics before repairing."}


def _derived_agent_diagnostics(failed_checks: list[dict[str, Any]]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for check in failed_checks[:8]:
        name = str(check.get("name", "unnamed_check"))
        if re.search(r"hillshade_agreement", name, flags=re.IGNORECASE):
            correlation = _find_numeric_value(check, "pixel_correlation")
            if correlation is not None and correlation <= -0.8:
                diagnostics.append(
                    {
                        "check": name,
                        "diagnostic": "strong_negative_hillshade_correlation",
                        "repair_hint": (
                            "The output is strongly negatively correlated with the task-intended hillshade pattern; "
                            "treat this as likely illumination/aspect/row-direction reversal before changing unrelated metadata."
                        ),
                    }
                )
        if re.search(r"contours_by_elevation", name, flags=re.IGNORECASE):
            diagnostics.append(
                {
                    "check": name,
                    "diagnostic": "contour_per_elevation_geometry_mismatch",
                    "repair_hint": (
                        "If schema, CRS, level set, and line health pass, repair the deterministic contour construction path: "
                        "DEM preprocessing, mask semantics, contour engine, and row/column-to-map coordinate conversion."
                    ),
                }
            )
        if re.search(r"zonal_statistics|landscan_statistics_numeric_fields", name, flags=re.IGNORECASE):
            diagnostics.append(
                {
                    "check": name,
                    "diagnostic": "raster_polygon_valid_pixel_set_mismatch",
                    "repair_hint": (
                        "Bind every statistic and count to the same valid pixel mask using pixel-center inclusion, integer windows, "
                        "and explicit NoData/mask exclusion."
                    ),
                }
            )
    return diagnostics


def _find_numeric_value(value: Any, wanted_key: str) -> float | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) == wanted_key and isinstance(child, (int, float)):
                return float(child)
            found = _find_numeric_value(child, wanted_key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_numeric_value(child, wanted_key)
            if found is not None:
                return found
    return None


def _scoring_notes(mode: str, manual_required: bool, report: dict[str, Any]) -> str:
    if report.get("error"):
        return "evaluator_error"
    if manual_required:
        return "manual_review_pending" if report.get("verdict") == "pass" else "automatic_checks_failed_with_manual_review_pending"
    return f"automatic_verdict_{str(report.get('verdict', 'unknown')).lower()}_mode_{mode}"
