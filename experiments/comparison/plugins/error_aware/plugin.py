from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


LABEL_KEYWORDS: dict[str, list[str]] = {
    "A1. Coordinate Axis Misinterpretation": ["axis", "lon", "lat", "longitude", "latitude", "row", "col", "swapped"],
    "A2. CRS Inconsistency": ["crs", "epsg", "projection", "reproject", "reference frame", "misaligned", "overlay"],
    "A3. Unit Misinterpretation": ["unit", "meter", "degree", "buffer", "distance", "area", "density", "radius"],
    "B1. Dataset Integrity Violation": ["missing file", "shapefile", "dbf", "prj", "schema", "field", "metadata", "keyerror"],
    "B2. Raster Alignment Failure": ["raster", "grid", "resolution", "extent", "pixel", "transform", "alignment"],
    "B3. Missing Data Misinterpretation": ["nodata", "mask", "missing_data", "background", "-9999", "nan"],
    "C1. Topological Predicate Confusion": ["within", "contains", "intersects", "touches", "predicate", "spatial relation"],
    "C2. Invalid Geometry Handling": ["invalid geometry", "self-intersection", "ring", "empty geometry", "validity"],
    "C3. Network Connectivity Misinterpretation": ["network", "route", "path", "reachable", "node", "edge", "connectivity"],
    "D1. Aggregation Scope Confusion": ["aggregation", "group", "scope", "global", "local", "district", "zone"],
    "D2. Spatial Allocation Error": [
        "allocate",
        "assignment",
        "connector",
        "nearest",
        "spatial support",
        "centroid",
        "area-weighted",
        "transfer",
    ],
    "D3. Spatial Statistical Misinterpretation": ["statistic", "threshold", "mean", "indicator", "denominator", "correlation"],
    "E1. Classification Scheme Misuse": ["classification", "break", "quantile", "equal interval", "class", "bin"],
    "E2. Symbolization Error": ["symbol", "color", "size", "shape", "palette", "visual encoding"],
    "E3. Map Composition Defect": ["legend", "scale", "title", "label", "layer", "composition", "context"],
}

FAILED_CHECK_LABEL_HINTS: list[tuple[str, str, int]] = [
    (r"connector_geometry|nearest|nearest_.+|dist_m|flood_ord|\biqr\b|\bq1\b|\bq3\b", "D2. Spatial Allocation Error", 8),
    (r"required_fields|schema|field|column|tag|road_id|feature_count|attribute|residential_tag_filter", "B1. Dataset Integrity Violation", 5),
    (r"nodata|mask|missing_data|valid_pixel|background|-9999|\bnan\b", "B3. Missing Data Misinterpretation", 7),
    (r"raster|pixel|transform|extent|alignment|window|profile|contour|hillshade|dem|slope|terrain|sample", "B2. Raster Alignment Failure", 7),
    (r"\bcrs\b|epsg|projection|reproject|proj\.db|crserror|pyproj", "A2. CRS Inconsistency", 5),
    (r"distance|length|area|unit|hausdorff|rmse", "A3. Unit Misinterpretation", 3),
    (r"intersect|within|contains|predicate", "C1. Topological Predicate Confusion", 4),
    (r"class|break|bin|quantile|interval", "E1. Classification Scheme Misuse", 4),
    (r"symbol|color|palette|visual", "E2. Symbolization Error", 4),
    (r"legend|scale|title|label|layer|composition|map", "E3. Map Composition Defect", 4),
]

CRS_FAILURE_PATTERN = re.compile(
    r"\bcrs\b|epsg|projection|reproject|proj\.db|crserror|pyproj|coordinate reference",
    flags=re.IGNORECASE,
)
LINE_VERTEX_PATTERN = (
    r"line_vertices|line vertex|linestring.*stored coordinate|coordinate.*linestring|linear.?ring.*coordinate|"
    r"stored coordinate|closing coordinate|closed line|"
    r"source_index_multiset|point_coordinate_multiset|coordinate_multiset|coincident vertices|"
    r"\bvertex\b|\bvertices\b|deduplicat"
)
PROTECTED_ROAD_LENGTH_PATTERN = (
    r"protected_region_road_lengths|road_length_attributes|length_m|clipped road length|"
    r"road lengths? inside|protected regions?|segment_length|groupby_sum"
)
PAIRWISE_DISTANCE_MATRIX_PATTERN = (
    r"pairwise distance|distance matrix|distance_matrix|facility_index|matrix_labels|"
    r"distance_values|symmetric_zero_diagonal|zero diagonal|symmetric matrix|facility distance"
)
TERRAIN_RUGGEDNESS_PATTERN = (
    r"terrain ruggedness|ruggedness|ruggedness_statistics|ruggedness stats|terrain roughness|"
    r"\btri\b|neighbou?rhood relief|local relief"
)
POPULATION_ALLOCATION_PATTERN = (
    r"population allocation|population transfer|block ?groups?|block_group|affected blockgroups?|"
    r"hazard.*population|building.*population|population.*building|population.*polygon|"
    r"population_summary|pop_alloc|population_by"
)
RASTER_NEAREST_SAMPLING_PATTERN = (
    r"nearest_sample_values|sample raster|raster sampling|checkpoint_id_set|"
    r"checkpoint.*sample|sampled_values?|sample values?"
)
RASTER_BOOLEAN_SUITABILITY_PATTERN = (
    r"suitability|camping|suitable|multi.?criteria|boolean mask|boolean raster|"
    r"criterion mask|criteria mask|eligible_pixels|suitability_mask"
)
MINIMUM_BOUNDING_GEOMETRY_PATTERN = (
    r"minimum rotated rectangle|min(?:imum)? area rectangle|min_area_rect|minimum bounding|"
    r"oriented envelope|minimum enclosing|convex hull area|convex_hull_area"
)
ROAD_OVERLAY_PATTERN = (
    r"province_road_overlay|road.*overlay|clip road|road segment|prov_id|prov_name|"
    r"pinyin|prov_code|seg_len_m|road_records_and_counts"
)
VORONOI_PATTERN = (
    r"voronoi|thiessen|bounded|convex hull|clip.*hull|voronoi_polygons|"
    r"building_voronoi|expanded by 100|\bsource_id\b"
)
CONTOUR_PATTERN = r"contour|contours_by_elevation|puerto_contours|elevation levels?|line_geometry_health"
HILLSHADE_PATTERN = r"hillshade|hillshade_agreement|shade|illumination|azimuth|altitude|solar angle"
ZONAL_STATS_PATTERN = (
    r"pixel statistics|zonal[_ ]statistics|px_count|pop_sum|pop_mean|pop_min|pop_max|"
    r"stat_min|stat_max|stat_mean|stat_std|stat_sum|landscan"
)
LANDSCAN_PATTERN = (
    r"landscan|landscan_statistics|laramie_landscan|s_fid|px_count|pop_sum|pop_mean|pop_min|pop_max"
)
RASTER_REPROJECT_PATTERN = (
    r"reprojected_dem|richland_dem_epsg6569|epsg:?6569|target grid|default target grid|"
    r"nearest.neighbou?r|calculate_default_transform|pixel_size|spatial_extent"
)
ATTRIBUTE_FILTER_PATTERN = r"contiguous_us_counties|statefp|exclude state|source geometries and attributes"
POLYGON_DIFFERENCE_PATTERN = (
    r"residual_polygon|generated_polygon|(?<!finite\s)\bdifferences?\b|erase|"
    r"remove.*overlap|counties_with_residual_polygon"
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_\-.]+", text.lower()))


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    query = text.lower()
    query_tokens = _tokens(query)
    hits: list[str] = []
    for keyword in keywords:
        normalized = keyword.lower()
        if " " in normalized:
            if normalized in query:
                hits.append(keyword)
        elif normalized in query_tokens:
            hits.append(keyword)
    return hits


def _safe_short_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item)[:200] for item in value[:8]]
    if value in (None, ""):
        return []
    return [str(value)[:200]]


class ErrorAwarePlugin:
    """Read-only Error-aware diagnostic and repair advisor."""

    plugin_name = "error_aware_plugin"
    plugin_version = "0.1.0"

    def __init__(self, repo_root: Path, max_cases: int = 5) -> None:
        self.repo_root = repo_root
        self.max_cases = max_cases
        self.rule_cards_path = repo_root / "knowledge_base" / "rule_cards.json"
        self.annotation_guide_path = repo_root / "GIS_WORKFLOW_ERROR_ANNOTATION_GUIDE.md"
        self.case_index_path = repo_root / "knowledge_base" / "cases" / "index.json"
        self.all_cases_path = repo_root / "knowledge_base" / "cases" / "all_cases.jsonl"
        self.rule_cards = _load_json(self.rule_cards_path)
        self.case_index = _load_json(self.case_index_path)
        # The candidate pool is deliberately not loaded in the formal experiment path.
        self._rules_by_label = {rule["label"]: rule for rule in self.rule_cards.get("rules", [])}

    def diagnose_and_advise(
        self,
        task_view: dict[str, Any],
        generated_code: str,
        execution_log: str,
        agent_visible_report: dict[str, Any],
        step_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        signal = self._collect_signal(task_view, generated_code, execution_log, agent_visible_report, step_report)
        if self._is_generic_insufficient_failure(signal):
            classification = self._classify_with_taxonomy(
                signal,
                [
                    {
                        "label": "unclassified_or_insufficient_evidence",
                        "score": 0,
                        "matched_terms": [],
                        "non_match_policy": self.rule_cards.get("no_match_output", {}),
                    }
                ],
            )
            return {
                "plugin": {"name": self.plugin_name, "version": self.plugin_version},
                "knowledge_sources": {
                    "rule_cards": self._rel(self.rule_cards_path),
                    "annotation_guide": self._rel(self.annotation_guide_path),
                    "case_index": self._rel(self.case_index_path),
                    "candidate_pool_used": False,
                },
                "signal_summary": signal["summary"],
                "candidate_labels": [],
                "classification_basis": classification,
                "step_branch_plan": self._build_step_branch_plan(classification, signal),
                "retrieved_cases": [],
                "repair_advice": self._build_repair_advice(classification, [], signal),
            }
        candidates = self._screen_rule_cards(signal)
        classification = self._classify_with_taxonomy(signal, candidates)
        cases = self._retrieve_cases(signal, classification["candidate_labels"])
        repair_advice = self._build_repair_advice(classification, cases, signal)
        return {
            "plugin": {"name": self.plugin_name, "version": self.plugin_version},
            "knowledge_sources": {
                "rule_cards": self._rel(self.rule_cards_path),
                "annotation_guide": self._rel(self.annotation_guide_path),
                "case_index": self._rel(self.case_index_path),
                "candidate_pool_used": False,
            },
            "signal_summary": signal["summary"],
            "candidate_labels": classification["candidate_labels"],
            "classification_basis": classification,
            "step_branch_plan": self._build_step_branch_plan(classification, signal),
            "retrieved_cases": cases,
            "repair_advice": repair_advice,
        }

    def _collect_signal(
        self,
        task_view: dict[str, Any],
        generated_code: str,
        execution_log: str,
        agent_visible_report: dict[str, Any],
        step_report: dict[str, Any] | None,
    ) -> dict[str, Any]:
        failure_text = " ".join(agent_visible_report.get("failure_reasons", []))
        metrics_text = json.dumps(agent_visible_report.get("metrics_diff", {}), ensure_ascii=False)
        safe_step_report = self._sanitize_step_report(step_report or {})
        step_text = json.dumps(safe_step_report, ensure_ascii=False)
        summary = " | ".join(
            part
            for part in [
                task_view.get("prompt", ""),
                agent_visible_report.get("failure_kind", ""),
                failure_text,
                metrics_text,
                step_text,
                execution_log,
            ]
            if part
        )
        return {
            "summary": summary[:2000],
            "query_text": summary,
            "failure_kind": agent_visible_report.get("failure_kind", ""),
            "failure_text": failure_text,
            "failed_checks": list(agent_visible_report.get("metrics_diff", {}).get("failed_checks", [])),
            "failed_check_hints": list(agent_visible_report.get("metrics_diff", {}).get("failed_check_hints", [])),
            "diagnostic_hints": list(agent_visible_report.get("metrics_diff", {}).get("diagnostic_hints", [])),
            "failed_check_details": list(agent_visible_report.get("metrics_diff", {}).get("failed_check_details", [])),
            "requires_visual_check": bool(agent_visible_report.get("requires_visual_check", False)),
            "generated_code_excerpt": generated_code[:2000],
            "execution_log_excerpt": execution_log[:2000],
            "step_report": safe_step_report,
        }

    def _screen_rule_cards(self, signal: dict[str, Any]) -> list[dict[str, Any]]:
        scores: dict[str, int] = {}
        matches: dict[str, list[str]] = {}
        failed_signal = " ".join(
            [
                signal.get("failure_kind", ""),
                signal.get("failure_text", ""),
                " ".join(str(item) for item in signal.get("failed_checks", [])),
                " ".join(json.dumps(item, ensure_ascii=False) for item in signal.get("failed_check_hints", [])),
                " ".join(json.dumps(item, ensure_ascii=False) for item in signal.get("diagnostic_hints", [])),
                " ".join(json.dumps(item, ensure_ascii=False) for item in signal.get("failed_check_details", [])),
            ]
        ).lower()
        failure_plus_log = " ".join([failed_signal, signal.get("execution_log_excerpt", "")]).lower()
        task_signal_text = " ".join([failed_signal, signal["query_text"].lower()])
        contour_signal = re.search(CONTOUR_PATTERN, task_signal_text)
        polygon_difference_signal = re.search(POLYGON_DIFFERENCE_PATTERN, task_signal_text)
        voronoi_signal = re.search(VORONOI_PATTERN, task_signal_text)
        crs_failure_evidence = bool(CRS_FAILURE_PATTERN.search(failure_plus_log))
        for label, keywords in LABEL_KEYWORDS.items():
            hits = _keyword_hits(signal["query_text"], keywords)
            if label == "A2. CRS Inconsistency" and hits and not crs_failure_evidence:
                hits = []
            if hits:
                scores[label] = scores.get(label, 0) + len(hits)
                matches.setdefault(label, []).extend(hits)

        for pattern, label, weight in FAILED_CHECK_LABEL_HINTS:
            if re.search(pattern, failed_signal):
                scores[label] = scores.get(label, 0) + weight
                matches.setdefault(label, []).append(f"failed_check:{pattern}")

        connector_signal = re.search(
            r"connector_geometry|nearest|nearest_.+|dist_m|flood_ord|\biqr\b|\bq1\b|\bq3\b",
            task_signal_text,
        )
        if connector_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 8)
            matches.setdefault("D2. Spatial Allocation Error", []).append("semantic_hint:nearest_connector_allocation")
            if "B1. Dataset Integrity Violation" in scores and not re.search(
                r"required_fields|schema|field|column|tag|road_id|attribute|residential_tag_filter",
                failed_signal,
            ):
                scores["B1. Dataset Integrity Violation"] = min(scores["B1. Dataset Integrity Violation"], 2)

        dem_sampling_signal = re.search(
            r"\bslope\b|finite differences|gradient|pixel sizes?|nearest raster cell|sample slope|centroid_slope|terrain_derivatives|coordinates_and_elevation",
            task_signal_text,
        )
        if dem_sampling_signal:
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 9)
            matches.setdefault("B2. Raster Alignment Failure", []).append("semantic_hint:dem_slope_sampling")
            if not crs_failure_evidence and "A2. CRS Inconsistency" in scores:
                scores["A2. CRS Inconsistency"] = min(scores["A2. CRS Inconsistency"], 2)

        nearest_match_signal = re.search(
            r"nearest estimated|ground truth|location error|matched_ground_truth|within\s+\d+(\.\d+)?\s*meters?|valid_pair_flags|checkpoint_id_set|nearest_sample_values",
            task_signal_text,
        )
        if nearest_match_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 9)
            matches.setdefault("D2. Spatial Allocation Error", []).append("semantic_hint:nearest_matching")

        pairwise_distance_signal = re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, task_signal_text)
        if pairwise_distance_signal:
            scores["D3. Spatial Statistical Misinterpretation"] = max(
                scores.get("D3. Spatial Statistical Misinterpretation", 0), 14
            )
            scores["A3. Unit Misinterpretation"] = max(scores.get("A3. Unit Misinterpretation", 0), 6)
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 4)
            matches.setdefault("D3. Spatial Statistical Misinterpretation", []).append(
                "semantic_hint:pairwise_distance_matrix"
            )
            matches.setdefault("A3. Unit Misinterpretation", []).append("neighbor_hint:distance_units")
            matches.setdefault("B1. Dataset Integrity Violation", []).append("neighbor_hint:matrix_label_schema")
            if "C1. Topological Predicate Confusion" in scores and not re.search(
                r"intersect|within|contains|predicate|overlay", failed_signal
            ):
                scores["C1. Topological Predicate Confusion"] = min(scores["C1. Topological Predicate Confusion"], 2)

        terrain_ruggedness_signal = re.search(TERRAIN_RUGGEDNESS_PATTERN, task_signal_text)
        if terrain_ruggedness_signal:
            scores["D3. Spatial Statistical Misinterpretation"] = max(
                scores.get("D3. Spatial Statistical Misinterpretation", 0), 13
            )
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 8)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 5)
            matches.setdefault("D3. Spatial Statistical Misinterpretation", []).append(
                "semantic_hint:terrain_ruggedness_statistics"
            )
            matches.setdefault("B2. Raster Alignment Failure", []).append("neighbor_hint:ruggedness_window_grid")
            matches.setdefault("B3. Missing Data Misinterpretation", []).append("neighbor_hint:ruggedness_nodata_mask")
            if "C1. Topological Predicate Confusion" in scores and not re.search(
                r"polygon difference|erase|overlay|intersect", failed_signal
            ):
                scores["C1. Topological Predicate Confusion"] = min(scores["C1. Topological Predicate Confusion"], 2)

        population_allocation_signal = re.search(POPULATION_ALLOCATION_PATTERN, task_signal_text)
        if population_allocation_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 15)
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 7)
            scores["C1. Topological Predicate Confusion"] = max(
                scores.get("C1. Topological Predicate Confusion", 0), 5
            )
            matches.setdefault("D2. Spatial Allocation Error", []).append(
                "semantic_hint:population_spatial_support_allocation"
            )
            matches.setdefault("B1. Dataset Integrity Violation", []).append("neighbor_hint:population_field_binding")
            matches.setdefault("C1. Topological Predicate Confusion", []).append("neighbor_hint:allocation_overlay")

        raster_nearest_sampling_signal = re.search(RASTER_NEAREST_SAMPLING_PATTERN, task_signal_text)
        if raster_nearest_sampling_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 14)
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 10)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 5)
            matches.setdefault("D2. Spatial Allocation Error", []).append(
                "semantic_hint:raster_nearest_sampling_and_matching"
            )
            matches.setdefault("B2. Raster Alignment Failure", []).append("neighbor_hint:sample_row_col_transform")
            matches.setdefault("B3. Missing Data Misinterpretation", []).append("neighbor_hint:sample_nodata_mask")

        suitability_signal = re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, task_signal_text)
        if suitability_signal:
            scores["D3. Spatial Statistical Misinterpretation"] = max(
                scores.get("D3. Spatial Statistical Misinterpretation", 0), 13
            )
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 8)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 8)
            matches.setdefault("D3. Spatial Statistical Misinterpretation", []).append(
                "semantic_hint:raster_boolean_suitability_mask"
            )
            matches.setdefault("B2. Raster Alignment Failure", []).append("neighbor_hint:suitability_grid_alignment")
            matches.setdefault("B3. Missing Data Misinterpretation", []).append("neighbor_hint:suitability_valid_mask")

        if contour_signal:
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 13)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 8)
            matches.setdefault("B2. Raster Alignment Failure", []).append("semantic_hint:raster_contour_generation")
            matches.setdefault("B3. Missing Data Misinterpretation", []).append("neighbor_hint:contour_nodata_mask")

        hillshade_signal = re.search(HILLSHADE_PATTERN, task_signal_text)
        if hillshade_signal:
            hillshade_score = 15 if self._has_hillshade_negative_correlation(signal) else 12
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), hillshade_score)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 6)
            scores["A3. Unit Misinterpretation"] = max(scores.get("A3. Unit Misinterpretation", 0), 4)
            matches.setdefault("B2. Raster Alignment Failure", []).append(
                "semantic_hint:hillshade_direction_pixel_spacing"
            )
            if self._has_hillshade_negative_correlation(signal):
                matches.setdefault("B2. Raster Alignment Failure", []).append(
                    "diagnostic_hint:strong_negative_hillshade_correlation"
                )
            matches.setdefault("B3. Missing Data Misinterpretation", []).append("neighbor_hint:hillshade_nodata_mask")
            matches.setdefault("A3. Unit Misinterpretation", []).append("neighbor_hint:hillshade_spacing_units")

        line_vertex_signal = None if contour_signal else re.search(LINE_VERTEX_PATTERN, task_signal_text)
        if line_vertex_signal:
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 12)
            scores["A1. Coordinate Axis Misinterpretation"] = max(
                scores.get("A1. Coordinate Axis Misinterpretation", 0), 4
            )
            scores["C1. Topological Predicate Confusion"] = max(
                scores.get("C1. Topological Predicate Confusion", 0), 3
            )
            matches.setdefault("B1. Dataset Integrity Violation", []).append("semantic_hint:line_vertex_multiset")
            matches.setdefault("A1. Coordinate Axis Misinterpretation", []).append(
                "neighbor_hint:coordinate_dimension_identity"
            )
            matches.setdefault("C1. Topological Predicate Confusion", []).append(
                "neighbor_hint:line_geometry_sequence"
            )

        road_overlay_signal = re.search(
            ROAD_OVERLAY_PATTERN,
            task_signal_text,
        )
        if road_overlay_signal:
            scores["C1. Topological Predicate Confusion"] = max(scores.get("C1. Topological Predicate Confusion", 0), 10)
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 6)
            matches.setdefault("C1. Topological Predicate Confusion", []).append("semantic_hint:road_overlay_attribute_binding")
            matches.setdefault("B1. Dataset Integrity Violation", []).append("semantic_hint:road_overlay_attribute_binding")

        protected_road_length_signal = re.search(
            PROTECTED_ROAD_LENGTH_PATTERN,
            task_signal_text,
        )
        if protected_road_length_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 12)
            scores["C1. Topological Predicate Confusion"] = max(
                scores.get("C1. Topological Predicate Confusion", 0), 8
            )
            scores["A3. Unit Misinterpretation"] = max(scores.get("A3. Unit Misinterpretation", 0), 5)
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 5)
            matches.setdefault("D2. Spatial Allocation Error", []).append(
                "semantic_hint:protected_region_road_length_allocation"
            )
            matches.setdefault("C1. Topological Predicate Confusion", []).append(
                "neighbor_hint:line_polygon_intersection"
            )
            matches.setdefault("A3. Unit Misinterpretation", []).append("neighbor_hint:length_unit")
            matches.setdefault("B1. Dataset Integrity Violation", []).append("neighbor_hint:length_field_schema")

        if voronoi_signal and not polygon_difference_signal:
            scores["C1. Topological Predicate Confusion"] = max(scores.get("C1. Topological Predicate Confusion", 0), 10)
            matches.setdefault("C1. Topological Predicate Confusion", []).append("semantic_hint:bounded_voronoi_clipping")

        minimum_bounding_signal = re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, task_signal_text)
        if minimum_bounding_signal and not voronoi_signal:
            scores["C1. Topological Predicate Confusion"] = max(scores.get("C1. Topological Predicate Confusion", 0), 10)
            scores["C2. Invalid Geometry Handling"] = max(scores.get("C2. Invalid Geometry Handling", 0), 5)
            matches.setdefault("C1. Topological Predicate Confusion", []).append(
                "semantic_hint:minimum_bounding_geometry"
            )
            matches.setdefault("C2. Invalid Geometry Handling", []).append("neighbor_hint:valid_bounding_polygon")

        zonal_stats_signal = re.search(
            ZONAL_STATS_PATTERN,
            task_signal_text,
        )
        if zonal_stats_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 16)
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 7)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 7)
            matches.setdefault("D2. Spatial Allocation Error", []).append("semantic_hint:raster_polygon_zonal_statistics")

        landscan_signal = re.search(
            LANDSCAN_PATTERN,
            task_signal_text,
        )
        if landscan_signal:
            scores["D2. Spatial Allocation Error"] = max(scores.get("D2. Spatial Allocation Error", 0), 18)
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 8)
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 7)
            scores["B3. Missing Data Misinterpretation"] = max(scores.get("B3. Missing Data Misinterpretation", 0), 7)
            matches.setdefault("D2. Spatial Allocation Error", []).append(
                "semantic_hint:landscan_population_statistics_binding"
            )
            matches.setdefault("B1. Dataset Integrity Violation", []).append("neighbor_hint:landscan_field_schema")

        raster_reproject_signal = re.search(
            RASTER_REPROJECT_PATTERN,
            task_signal_text,
        )
        if raster_reproject_signal:
            scores["B2. Raster Alignment Failure"] = max(scores.get("B2. Raster Alignment Failure", 0), 10)
            scores["A2. CRS Inconsistency"] = max(scores.get("A2. CRS Inconsistency", 0), 7)
            matches.setdefault("B2. Raster Alignment Failure", []).append("semantic_hint:raster_reprojection_grid")
            matches.setdefault("A2. CRS Inconsistency", []).append("neighbor_hint:raster_output_crs")

        attribute_filter_signal = re.search(
            ATTRIBUTE_FILTER_PATTERN,
            task_signal_text,
        )
        if attribute_filter_signal:
            scores["B1. Dataset Integrity Violation"] = max(scores.get("B1. Dataset Integrity Violation", 0), 9)
            matches.setdefault("B1. Dataset Integrity Violation", []).append("semantic_hint:attribute_filter_preserve_schema")

        if polygon_difference_signal:
            scores["C1. Topological Predicate Confusion"] = max(scores.get("C1. Topological Predicate Confusion", 0), 11)
            scores["C2. Invalid Geometry Handling"] = max(scores.get("C2. Invalid Geometry Handling", 0), 6)
            matches.setdefault("C1. Topological Predicate Confusion", []).append("semantic_hint:polygon_difference_merge")

        if "A2. CRS Inconsistency" in scores and not crs_failure_evidence:
            scores["A2. CRS Inconsistency"] = min(scores["A2. CRS Inconsistency"], 1)

        scored = [(score, label, matches.get(label, [])) for label, score in scores.items() if score > 0]
        scored.sort(key=lambda item: (-item[0], item[1]))
        if not scored:
            return [
                {
                    "label": "unclassified_or_insufficient_evidence",
                    "score": 0,
                    "matched_terms": [],
                    "non_match_policy": self.rule_cards.get("no_match_output", {}),
                }
            ]
        candidates = []
        for score, label, hits in scored[:3]:
            rule = self._rules_by_label.get(label, {})
            candidates.append(
                {
                    "label": label,
                    "score": score,
                    "matched_terms": hits,
                    "invariant": rule.get("invariant", ""),
                    "hypothesis_trigger": rule.get("hypothesis_trigger", ""),
                }
            )
        return candidates

    def _classify_with_taxonomy(self, signal: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        labels = [item["label"] for item in candidates if item["label"] != "unclassified_or_insufficient_evidence"]
        if not labels:
            return {
                "status": "unclassified_or_insufficient_evidence",
                "candidate_labels": [],
                "primary_candidate": "",
                "violated_gis_invariant": "",
                "why_not_neighboring_classes": "当前可见证据不足，不能据此判定结果正确或归入具体 GIS 子类。",
            }
        primary = labels[0]
        rule = self._rules_by_label.get(primary, {})
        neighbor_axis = ""
        for axis in rule.get("diagnostic_axes", []):
            if axis.startswith("neighbor_disambiguation:"):
                neighbor_axis = axis.split(":", 1)[1].strip()
        return {
            "status": "candidate_classified",
            "candidate_labels": labels,
            "primary_candidate": primary,
            "violated_gis_invariant": rule.get("invariant", ""),
            "why_this_candidate": rule.get("hypothesis_trigger", ""),
            "why_not_neighboring_classes": neighbor_axis or "需按标注指南继续做相邻类别互斥判断。",
            "annotation_guide_used": self._rel(self.annotation_guide_path),
        }

    def _retrieve_cases(self, signal: dict[str, Any], candidate_labels: list[str]) -> list[dict[str, Any]]:
        case_files = self._case_files_for_labels(candidate_labels)
        cases: list[dict[str, Any]] = []
        for path in case_files:
            cases.extend(_load_jsonl(path))
        if not cases:
            cases = _load_jsonl(self.all_cases_path)

        query_tokens = _tokens(signal["query_text"])
        scored: list[tuple[int, dict[str, Any]]] = []
        for case in cases:
            retrieval_text = case.get("retrieval_text", "")
            tags = " ".join(case.get("retrieval_tags", []))
            score = len(query_tokens & _tokens(f"{retrieval_text} {tags}"))
            if case.get("primary_label") == (candidate_labels[0] if candidate_labels else ""):
                label_bonus = 5
            elif case.get("primary_label") in candidate_labels:
                label_bonus = 2
            else:
                label_bonus = 0
            scored.append((score + label_bonus, case))
        scored.sort(key=lambda item: (-item[0], item[1].get("sample_id", "")))

        results = []
        for score, case in scored[: self.max_cases]:
            playbook = case.get("repair_playbook", {})
            results.append(
                {
                    "sample_id": case.get("sample_id", ""),
                    "primary_label": case.get("primary_label", ""),
                    "similarity_score": score,
                    "retrieval_text": case.get("retrieval_text", ""),
                    "similarity_basis": "Compared current failure signal with retrieval_text and retrieval_tags.",
                    "difference_check": "Use as repair reference only; confirm task data, scope, and failure mechanism before applying.",
                    "repair_playbook": {
                        "repair_goal": playbook.get("repair_goal", ""),
                        "repair_principle": playbook.get("repair_principle", ""),
                        "recommended_actions": playbook.get("recommended_actions", []),
                        "forbidden_actions": playbook.get("forbidden_actions", []),
                        "validation_checks": playbook.get("validation_checks", []),
                        "success_criteria": playbook.get("success_criteria", []),
                    },
                }
            )
        return results

    def _case_files_for_labels(self, labels: list[str]) -> list[Path]:
        categories = sorted({label[0] for label in labels if label and label[0] in "ABCDE"})
        if not categories:
            return [self.all_cases_path]
        files: list[Path] = []
        for category in categories:
            entry = self.case_index.get("by_category", {}).get(category, {})
            path_value = entry.get("path", "")
            if path_value:
                files.append(self.repo_root / path_value)
        return files or [self.all_cases_path]

    def _build_step_branch_plan(self, classification: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
        step_report = signal.get("step_report", {})
        steps = step_report.get("steps", []) if isinstance(step_report, dict) else []
        suspected_step = self._suspected_step_from_report(steps)
        inferred_step = self._infer_step_from_signal(classification, signal)
        branch_step = self._choose_branch_step(suspected_step, inferred_step, signal)
        locked_prior_steps = self._locked_prior_steps(steps, branch_step.get("step_id", ""))
        return {
            "mode": "step_branch_repair",
            "branch_id": f"branch_from_{branch_step.get('step_id', 'inferred_step')}",
            "suspected_failed_step": branch_step,
            "locked_prior_steps": locked_prior_steps,
            "branch_repair_goal": (
                "Start the repair from the suspected failed step. Preserve earlier successful step logic and artifacts "
                "unless the branch plan marks them as suspect."
            ),
            "previous_output_dir_env": "PREVIOUS_OUTPUT_DIR",
            "step_validation_checks": self._step_validation_checks(classification, signal, branch_step),
            "non_gt_scope": (
                "Step checks are agent-visible self checks only. They must not read evaluator, reference, GT, review, "
                "or knowledge_base files."
            ),
        }

    @staticmethod
    def _sanitize_step_report(step_report: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(step_report, dict):
            return {"status": "missing", "steps": []}
        steps = step_report.get("steps", [])
        if not isinstance(steps, list):
            steps = []
        safe_steps: list[dict[str, Any]] = []
        for index, step in enumerate(steps[:12], start=1):
            if not isinstance(step, dict):
                continue
            safe_steps.append(
                {
                    "step_id": str(step.get("step_id", f"step_{index:02d}"))[:80],
                    "name": str(step.get("name", ""))[:120],
                    "status": str(step.get("status", ""))[:80],
                    "outputs": _safe_short_list(step.get("outputs", [])),
                    "gis_invariants_checked": _safe_short_list(step.get("gis_invariants_checked", [])),
                    "observations": _safe_short_list(step.get("observations", [])),
                    "suspected_issue": ErrorAwarePlugin._normalize_issue_text(step.get("suspected_issue", ""))[:300],
                }
            )
        return {
            "schema_version": str(step_report.get("schema_version", "0.1.0"))[:20],
            "status": str(step_report.get("status", "missing"))[:80],
            "message": str(step_report.get("message", ""))[:300],
            "steps": safe_steps,
        }

    @staticmethod
    def _choose_branch_step(
        reported_step: dict[str, Any],
        inferred_step: dict[str, Any],
        signal: dict[str, Any],
    ) -> dict[str, Any]:
        if not reported_step:
            return inferred_step
        if not inferred_step:
            return reported_step

        text = " ".join(
            [
                signal.get("query_text", ""),
                signal.get("failure_text", ""),
                " ".join(str(item) for item in signal.get("failed_checks", [])),
                signal.get("execution_log_excerpt", ""),
            ]
        ).lower()
        reported_id = str(reported_step.get("step_id", "")).lower()
        reported_reason = str(reported_step.get("reason", "")).lower()
        inferred_id = str(inferred_step.get("step_id", "")).lower()

        strong_task_signal = bool(
            re.search(CONTOUR_PATTERN, text)
            or re.search(HILLSHADE_PATTERN, text)
            or re.search(ZONAL_STATS_PATTERN, text)
            or re.search(LANDSCAN_PATTERN, text)
            or re.search(RASTER_REPROJECT_PATTERN, text)
            or re.search(POLYGON_DIFFERENCE_PATTERN, text)
            or re.search(LINE_VERTEX_PATTERN, text)
            or re.search(PROTECTED_ROAD_LENGTH_PATTERN, text)
            or re.search(ROAD_OVERLAY_PATTERN, text)
            or re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, text)
            or re.search(TERRAIN_RUGGEDNESS_PATTERN, text)
            or re.search(POPULATION_ALLOCATION_PATTERN, text)
            or re.search(RASTER_NEAREST_SAMPLING_PATTERN, text)
            or re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, text)
            or re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, text)
            or re.search(VORONOI_PATTERN, text)
        )
        if not strong_task_signal:
            return reported_step

        generic_reported_step = reported_id in {
            "normalize_crs",
            "normalize_crs_or_grid",
            "normalize_spatial_reference",
            "read_inputs",
            "write_outputs",
            "fatal_error",
            "error_handler",
            "error",
            "failure",
            "unhandled_exception",
            "workflow_error",
            "buffer_and_count",
            "raster_statistics",
            "reproject_raster",
        } or (reported_id == "geometry_vertex_extraction" and inferred_id == "raster_contour_generation") or (
            reported_id == "bounded_voronoi_geometry_construction" and inferred_id == "polygon_difference_merge"
        ) or (
            reported_id == "bounded_voronoi_geometry_construction" and inferred_id == "minimum_bounding_geometry"
        )
        field_conflict_points_to_overlay = (
            inferred_id == "overlay_length_aggregation"
            and re.search(r"\bfid\b|field|column|keyerror|groupby", reported_reason)
        )
        if generic_reported_step or field_conflict_points_to_overlay:
            chosen = dict(inferred_step)
            chosen["source"] = "inferred_from_failure_signal_over_reported_step"
            chosen["reported_step_overridden"] = reported_step
            chosen["reason"] = (
                f"{inferred_step.get('reason', '')} Reported step "
                f"{reported_step.get('step_id', '')!r} looked generic or mismatched with the task-specific failure."
            )
            return chosen
        return reported_step

    @staticmethod
    def _suspected_step_from_report(steps: list[Any]) -> dict[str, Any]:
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            status = str(step.get("status", "")).lower()
            issue = ErrorAwarePlugin._normalize_issue_text(step.get("suspected_issue", ""))
            if status in {"fail", "failed", "error", "suspect", "warning"} or issue:
                return {
                    "step_id": str(step.get("step_id", f"step_{index:02d}")),
                    "name": str(step.get("name", "reported_suspect_step")),
                    "source": "workflow_steps_report",
                    "reason": issue or f"step status was {status}",
                }
        return {}

    @staticmethod
    def _infer_step_from_signal(classification: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            [
                signal.get("query_text", ""),
                signal.get("failure_kind", ""),
                " ".join(str(item) for item in signal.get("failed_checks", [])),
            ]
        ).lower()
        primary = classification.get("primary_candidate", "")
        if re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, text):
            return {
                "step_id": "pairwise_distance_matrix",
                "name": "labelled_symmetric_pairwise_distance_matrix",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to pairwise distance matrix labels, source feature order, distance units, symmetry, or zero diagonal semantics.",
            }
        if re.search(TERRAIN_RUGGEDNESS_PATTERN, text):
            return {
                "step_id": "terrain_ruggedness_statistics",
                "name": "local_dem_window_relief_statistics",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to terrain ruggedness window semantics, neighbor inclusion, pixel spacing, or NoData exclusion.",
            }
        if re.search(LANDSCAN_PATTERN, text):
            return {
                "step_id": "landscan_population_statistics_binding",
                "name": "landscan_pixel_stats_and_output_field_binding",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to LandScan pixel inclusion, valid-pixel statistics, source feature identity binding, or numeric output fields.",
            }
        if re.search(ZONAL_STATS_PATTERN, text):
            return {
                "step_id": "raster_zonal_statistics",
                "name": "polygon_mask_valid_pixels_and_statistics",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to raster-to-polygon statistics, pixel inclusion semantics, NoData exclusion, or output field binding.",
            }
        if re.search(POPULATION_ALLOCATION_PATTERN, text):
            return {
                "step_id": "population_spatial_allocation",
                "name": "population_support_transfer_and_field_binding",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to population support transfer, source-target identity binding, overlay cardinality, or output population fields.",
            }
        if re.search(RASTER_NEAREST_SAMPLING_PATTERN, text):
            return {
                "step_id": "raster_nearest_sampling_and_matching",
                "name": "point_to_raster_nearest_cell_value_binding",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to raster sampling row/col conversion, nearest valid-cell matching, NoData handling, or sampled value binding.",
            }
        if re.search(
            r"nearest estimated|ground truth|location error|matched_ground_truth|within\s+\d+(\.\d+)?\s*meters?|valid_pair_flags",
            text,
        ):
            return {
                "step_id": "nearest_spatial_matching",
                "name": "thresholded_nearest_feature_matching",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to nearest feature matching, distance threshold semantics, source identity binding, or match summary statistics.",
            }
        if re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, text):
            return {
                "step_id": "raster_boolean_suitability_mask",
                "name": "aligned_multicriteria_boolean_mask",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to multi-criteria raster mask alignment, boolean threshold semantics, valid-pixel mask, or output raster profile.",
            }
        if re.search(CONTOUR_PATTERN, text):
            return {
                "step_id": "raster_contour_generation",
                "name": "reproject_mask_contour_lines_by_level",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to DEM reprojection, NoData masking, contour level generation, or row/col-to-map coordinate conversion.",
            }
        if re.search(HILLSHADE_PATTERN, text):
            return {
                "step_id": "raster_hillshade_derivation",
                "name": "dem_gradient_spacing_direction_and_profile",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to hillshade illumination direction, DEM pixel spacing, row/column gradient sign, NoData mask, or output raster profile.",
            }
        if re.search(PROTECTED_ROAD_LENGTH_PATTERN, text):
            return {
                "step_id": "overlay_length_aggregation",
                "name": "line_polygon_intersection_length_groupby",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to clipped road segment length allocation back to protected-region polygons.",
            }
        if re.search(POLYGON_DIFFERENCE_PATTERN, text):
            return {
                "step_id": "polygon_difference_merge",
                "name": "erase_overlap_and_merge_polygon_layers",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to polygon difference/erase semantics, merge schema, output CRS, or geometry validity.",
            }
        if re.search(ROAD_OVERLAY_PATTERN, text):
            return {
                "step_id": "road_overlay_attribute_binding",
                "name": "clip_roads_to_polygons_and_bind_region_attributes",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to road-polygon clipping, clipped segment counts, region attribute binding, or line length field semantics.",
            }
        if re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, text):
            return {
                "step_id": "minimum_bounding_geometry",
                "name": "minimum_rotated_rectangle_or_convex_hull_construction",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to minimum bounding polygon construction, orientation, area, source identity, or geometry validity.",
            }
        if re.search(VORONOI_PATTERN, text):
            return {
                "step_id": "bounded_voronoi_geometry_construction",
                "name": "centroid_voronoi_clip_and_source_id_binding",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to finite bounded Voronoi construction, clipping boundary, or source identity binding.",
            }
        if re.search(LINE_VERTEX_PATTERN, text):
            return {
                "step_id": "geometry_vertex_extraction",
                "name": "linestring_coordinate_sequence_to_points",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to line coordinate sequence extraction, source index preservation, or coordinate multiset semantics.",
            }
        if re.search(RASTER_REPROJECT_PATTERN, text):
            return {
                "step_id": "raster_reprojection_grid",
                "name": "calculate_target_transform_and_reproject_raster",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to raster target CRS, transform, pixel size, extent, resampling, or CRS metadata.",
            }
        if re.search(ATTRIBUTE_FILTER_PATTERN, text):
            return {
                "step_id": "attribute_filtering",
                "name": "filter_features_by_source_attribute_values",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to attribute filter semantics, excluded code list, schema preservation, or output feature identity.",
            }
        if primary.startswith("B2") or primary.startswith("B3") or re.search(r"raster|transform|nodata|mask|pixel|dem|slope|hillshade|contour", text):
            return {
                "step_id": "raster_processing",
                "name": "raster_alignment_mask_sampling_or_derivation",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to raster grid, transform, mask, sampling, or derived raster/vector products.",
            }
        if primary.startswith("A") or re.search(r"crs|epsg|projection|reproject|unit|meter|degree", text):
            return {
                "step_id": "normalize_spatial_reference",
                "name": "normalize_crs_units_axes",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to CRS, axis, or unit semantics.",
            }
        if primary.startswith("C") or re.search(r"overlay|intersect|voronoi|predicate|geometry", text):
            return {
                "step_id": "spatial_relation_operation",
                "name": "spatial_relation_or_geometry_construction",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to spatial predicate, overlay, clipping, or geometry construction.",
            }
        if primary.startswith("D") or re.search(r"nearest|allocation|statistics|summary|mean|count|threshold", text):
            return {
                "step_id": "analysis_semantics",
                "name": "allocation_statistics_or_sampling",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to allocation, nearest matching, sampling, or statistical semantics.",
            }
        if re.search(r"expected_output_exists|artifact_.*_exists|sidecar|write", text):
            return {
                "step_id": "write_outputs",
                "name": "write_outputs_and_schema",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points only to missing artifacts, sidecar files, or output write contract.",
            }
        if re.search(r"schema|field|column", text):
            return {
                "step_id": "attribute_binding",
                "name": "attribute_schema_and_identity_binding",
                "source": "inferred_from_failure_signal",
                "reason": "Failure points to field schema, source identity, or attribute binding semantics.",
            }
        return {
            "step_id": "task_specific_processing",
            "name": "task_specific_processing",
            "source": "fallback_inference",
            "reason": "No explicit failed workflow step was reported; branch from the most task-specific processing step.",
        }

    @staticmethod
    def _normalize_issue_text(value: Any) -> str:
        text = "" if value is None else str(value).strip()
        return "" if text.lower() in {"", "none", "null", "n/a", "na", "false"} else text

    @staticmethod
    def _locked_prior_steps(steps: list[Any], branch_step_id: str) -> list[dict[str, str]]:
        locked: list[dict[str, str]] = []
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            step_id = str(step.get("step_id", f"step_{index:02d}"))
            status = str(step.get("status", "")).lower()
            if step_id == branch_step_id:
                break
            if status in {"completed", "pass", "passed", "ok", ""}:
                locked.append({"step_id": step_id, "name": str(step.get("name", ""))})
        return locked[:8]

    @staticmethod
    def _step_validation_checks(
        classification: dict[str, Any],
        signal: dict[str, Any],
        branch_step: dict[str, Any],
    ) -> list[str]:
        primary = classification.get("primary_candidate", "")
        step_id = str(branch_step.get("step_id", ""))
        checks = [
            "After the branch repair, rewrite workflow_steps.json with status and observations for every step.",
            "Re-run local checks for all artifacts produced at and after the branch step before writing final outputs.",
        ]
        if primary.startswith("A") or "reference" in step_id:
            checks.append("Check CRS, axis order, units, bounds, and coordinate value ranges at the branch boundary.")
        if primary.startswith("B2") or primary.startswith("B3") or "raster" in step_id:
            checks.append("Check raster CRS, transform, pixel size, width/height, dtype, NoData/mask, and value range.")
        if primary.startswith("C") or "spatial_relation" in step_id:
            checks.append("Check geometry validity, predicate semantics, clipping boundary, feature count, and spatial bounds.")
        if primary.startswith("D") or "analysis" in step_id:
            checks.append("Check allocation/statistical support, join cardinality, denominator, threshold, and output field semantics.")
        if "geometry_vertex_extraction" in step_id:
            checks.append("Check point coordinate multiset, closed-line duplicate vertices, input index preservation, CRS, and Point geometry type.")
        if "overlay_length_aggregation" in step_id:
            checks.append("Check stable region id binding, line-polygon clipped segment lengths, linear-geometry filtering, all-region preservation, length_m dtype, and metre CRS.")
        if "road_overlay_attribute_binding" in step_id:
            checks.append("Check clipped road segment count, region attribute binding, original road attribute preservation, geometry type, segment length units, CRS, and Shapefile sidecars.")
        if "pairwise_distance_matrix" in step_id:
            checks.append("Check matrix row/column labels, source feature order, CRS/units, symmetry, zero diagonal, numeric distance values, and output file/schema contract.")
        if "terrain_ruggedness_statistics" in step_id:
            checks.append("Check DEM pixel spacing, local window inclusion, edge handling, NoData exclusion, statistic formula, output field binding, and source feature order.")
        if "population_spatial_allocation" in step_id:
            checks.append("Check source-target spatial support, overlay/intersection cardinality, allocation weights, population conservation, block-group or feature id binding, and numeric output fields.")
        if "raster_nearest_sampling" in step_id:
            checks.append("Check point-to-raster CRS, row/col conversion, nearest valid cell rule, NoData exclusion, sample value binding, point id/order, and output schema.")
        if "nearest_spatial_matching" in step_id:
            checks.append("Check nearest target search, distance threshold, one-to-one or many-to-one match semantics, source id/order, distance field, geometry choice, and summary statistics.")
        if "raster_boolean_suitability_mask" in step_id:
            checks.append("Check all criteria rasters are aligned, thresholds use task semantics, boolean operations are combined in the correct direction, valid mask is shared, and output profile matches the reference grid.")
        if "bounded_voronoi" in step_id:
            checks.append("Check one finite polygon per input centroid, explicit clipping to the task boundary, zero-based source_id, valid geometry, CRS, and final bounds.")
        if "minimum_bounding_geometry" in step_id:
            checks.append("Check one output polygon per input feature/group, orientation/area semantics, source id binding, CRS, valid geometry, and no accidental hull/Voronoi substitution.")
        if "raster_contour_generation" in step_id:
            checks.append("Check target CRS, NoData mask, positive 50-m contour levels, row/col-to-map coordinate conversion, LineString validity, id/elevation fields, and output sidecars.")
        if "raster_hillshade_derivation" in step_id:
            checks.append("Check DEM mask, x/y pixel spacing in metres, north-up row direction, azimuth/altitude convention, uint8 value range, nodata=0, and copied raster profile.")
        if "raster_zonal_statistics" in step_id:
            checks.append("Check polygon-to-raster CRS conversion, pixel-center inclusion, NoData exclusion, valid-pixel count, min/max/mean/std/sum fields, output CRS, and source id field binding.")
        if "landscan_population_statistics_binding" in step_id:
            checks.append("Check pixel-center inclusion, LandScan NoData exclusion, s_fid binding, px_count/pop_* numeric fields, source polygon geometry/order, and output Shapefile schema.")
        if "raster_reprojection_grid" in step_id:
            checks.append("Check output CRS metadata, calculated target transform, pixel size, width/height, bounds, nearest-neighbor resampling, dtype, band count, and NoData semantics.")
        if "attribute_filtering" in step_id:
            checks.append("Check source attribute values, excluded code list, feature count/id set, geometry type, CRS, and original attribute preservation.")
        if "polygon_difference_merge" in step_id:
            checks.append("Check polygon difference removes only overlap, both layers are merged in target CRS, output geometry is valid, and schema/feature count match task intent.")
        checks.extend(signal.get("failed_checks", [])[:4])
        return ErrorAwarePlugin._dedupe([str(check) for check in checks])

    def _build_repair_advice(
        self,
        classification: dict[str, Any],
        cases: list[dict[str, Any]],
        signal: dict[str, Any],
    ) -> dict[str, Any]:
        signal_actions = self._failure_specific_actions(signal)
        signal_forbidden = self._failure_specific_forbidden(signal)
        signal_validation = self._failure_specific_validation(signal)
        if not cases:
            return {
                "status": "insufficient_case_support",
                "message": "未检索到 verified 案例，不能编造修复案例；请基于可见证据和标注指南做保守修复。",
                "recommended_actions": signal_actions,
                "forbidden_actions": signal_forbidden,
                "validation_checks": signal_validation,
            }
        recommended: list[str] = []
        forbidden: list[str] = []
        validation: list[str] = []
        primary = classification.get("primary_candidate", "")
        support_cases = [case for case in cases if case.get("primary_label") == primary] or cases
        for case in support_cases:
            playbook = case["repair_playbook"]
            recommended.extend(playbook.get("recommended_actions", []))
            forbidden.extend(playbook.get("forbidden_actions", []))
            validation.extend(playbook.get("validation_checks", []))
        return {
            "status": "case_supported_repair_advice",
            "primary_candidate": classification.get("primary_candidate", ""),
            "case_count": len(cases),
            "playbook_case_count": len(support_cases),
            "repair_instruction": (
                "Revise the GIS workflow according to the candidate root cause, using retrieved cases only as analogies. "
                "Preserve task intent, avoid forbidden actions, and run validation checks after regenerating outputs."
            ),
            "recommended_actions": self._dedupe(signal_actions + recommended)[:10],
            "forbidden_actions": self._dedupe(signal_forbidden + forbidden)[:6],
            "validation_checks": self._dedupe(signal_validation + validation)[:10],
        }

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.repo_root).as_posix()

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        seen = set()
        deduped = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    @staticmethod
    def _has_hillshade_negative_correlation(signal: dict[str, Any]) -> bool:
        text = " ".join(
            [
                json.dumps(signal.get("diagnostic_hints", []), ensure_ascii=False),
                json.dumps(signal.get("failed_check_details", []), ensure_ascii=False),
            ]
        ).lower()
        if "strong_negative_hillshade_correlation" in text:
            return True
        value = ErrorAwarePlugin._find_nested_numeric(signal.get("failed_check_details", []), "pixel_correlation")
        return value is not None and value <= -0.8

    @staticmethod
    def _find_nested_numeric(value: Any, key_name: str) -> float | None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key) == key_name and isinstance(child, (int, float)):
                    return float(child)
                found = ErrorAwarePlugin._find_nested_numeric(child, key_name)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = ErrorAwarePlugin._find_nested_numeric(child, key_name)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _is_generic_insufficient_failure(signal: dict[str, Any]) -> bool:
        if signal.get("failure_kind") != "missing_output":
            return False
        failed_checks = {str(check).lower() for check in signal.get("failed_checks", [])}
        if failed_checks and failed_checks != {"expected_output_exists"}:
            return False
        text = " ".join(
            [
                signal.get("generated_code_excerpt", ""),
                signal.get("execution_log_excerpt", ""),
                signal.get("failure_text", ""),
            ]
        ).lower()
        gis_failure_terms = {
            "traceback",
            "exception",
            "geopandas",
            "rasterio",
            "pyproj",
            "shapely.errors",
            "topologyexception",
            "crs",
            "nodata",
            "geometry",
            "projection",
            "reproject",
            "overlay",
            "buffer",
            "sjoin",
        }
        has_gis_failure_signal = any(term in text for term in gis_failure_terms)
        return not has_gis_failure_signal

    @staticmethod
    def _failure_specific_actions(signal: dict[str, Any]) -> list[str]:
        failed_checks = " ".join(str(check).lower() for check in signal.get("failed_checks", []))
        failure_text = signal.get("failure_text", "").lower()
        execution_log = signal.get("execution_log_excerpt", "").lower()
        query_text = signal.get("query_text", "").lower()
        combined = " ".join([failed_checks, failure_text, execution_log, query_text])
        visible_failure = " ".join([failed_checks, failure_text])
        actions: list[str] = []
        connector_pattern = r"connector_geometry|nearest|nearest_.+|dist_m|flood_ord|\biqr\b|\bq1\b|\bq3\b"

        if re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, combined):
            actions.extend(
                [
                    "距离矩阵修复应以输入设施/点要素的稳定顺序为行列顺序，显式写出行标签和列标签，不能让 DataFrame 默认索引漂移。",
                    "计算距离前确认所有几何处于可度量 CRS；若源为经纬度，应按任务语义投影到合适米制 CRS 后计算距离。",
                    "矩阵应为数值型二维结果：同一对象到自身为 0，i->j 与 j->i 对称；不要把几何对象、字符串距离或坐标元组写进距离值列。",
                    "写出前本地验证 labels 集合、矩阵 shape、零对角线、对称性、单位量级和 CSV/文本输出格式同时满足任务契约。",
                ]
            )

        if re.search(TERRAIN_RUGGEDNESS_PATTERN, combined):
            actions.extend(
                [
                    "terrain ruggedness 修复应先固定 DEM 有效像元 mask，再在同一网格上对每个中心像元或目标区域计算任务定义的局部邻域统计。",
                    "若 ruggedness 依赖 3x3 或指定窗口，应明确窗口边界、中心像元、邻居集合和边缘处理；不要用 polygon difference、全图统计或单点高程代替局部 relief。",
                    "统计值必须排除 NoData/mask 外像元，并与同一个有效邻域绑定；输出字段应保持数值类型和源要素/像元身份顺序。",
                    "修复后抽查局部窗口，复核邻域像元、最大最小/均值/差值公式、NoData 排除和输出 id/字段绑定。",
                ]
            )

        if re.search(POPULATION_ALLOCATION_PATTERN, combined):
            actions.extend(
                [
                    "人口分配修复应先明确人口变量依附的空间支持，例如 block group、栅格像元、建筑物或 polygon；不要把一个支持上的总量直接复制到另一个支持。",
                    "面到面或面到点分配应使用任务指定权重或合理空间权重，例如 clipped area、覆盖比例、建筑物归属或交叠关系，并保持人口总量守恒语义。",
                    "输出应以任务要求的目标对象为主表，显式绑定源/目标 id 和人口字段；缺少交叠或无人口贡献的目标按任务契约写 0 或空统计。",
                    "修复后检查 join cardinality、population sum conservation、目标 id 集合、数值字段类型和空间范围。",
                ]
            )

        if re.search(RASTER_NEAREST_SAMPLING_PATTERN, combined):
            actions.extend(
                [
                    "栅格最近采样修复应先把采样点转换到 raster CRS，再用 raster transform/index 或 src.sample 将地图坐标映射到 row/col/value。",
                    "若任务要求最近有效像元，应在候选邻域内排除 NoData/mask 外像元后选择最近有效 cell；不要把越界或 NoData 采样值当作 0。",
                    "输出采样值必须绑定回源点或 checkpoint 的 id/order；不要假设栅格采样返回顺序可与另一个表的行顺序自动对齐。",
                    "修复后复核 checkpoint id 集合、row/col 范围、采样值数值类型、NoData 处理和输出字段契约。",
                ]
            )

        if re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, combined):
            actions.extend(
                [
                    "suitability mask 修复应把所有条件 raster 对齐到同一个 grid/profile 后再计算布尔条件；每个条件都应使用任务定义的阈值方向。",
                    "多个条件应按任务语义用 AND/OR/NOT 组合，并与共同 valid-data mask 求交；不要让任一 NoData/背景像元进入 suitable 区域。",
                    "输出 suitability raster 的 CRS、transform、height、width、dtype、nodata 和 value domain 应与目标 grid/profile 一致。",
                    "修复后统计 suitable/unsuitable/NoData 像元数量，抽查每个条件阈值、布尔组合方向和边界像元是否符合任务语义。",
                ]
            )

        if re.search(CONTOUR_PATTERN, combined):
            actions.extend(
                [
                    "等值线修复应把 contour 过程作为一个确定性子流程整体重写：prepare valid DEM surface -> make task levels -> run one contour engine -> convert row/col to map coordinates -> validate/write LineString，不要只局部改字段名或半像元。",
                    "写出前增加本地 contour verifier：每个任务 level 都有对应数值 elevation；所有坐标为有限地图坐标；LineString 至少两个不同点且长度大于 0；输出 bounds 落在 DEM 空间范围内；Shapefile sidecar 完整。",
                    "等值线修复应先固定输入 DEM 的有效像元集合：把 src.nodata、NaN、mask 外像元以及任务声明的背景值排除，再在有效 DEM 表面上生成 contour。",
                    "若先重投影 DEM，应使用同一个重投影后的数组、transform、CRS 和 NoData mask 生成所有等值线；不要在一个网格上取值、另一个网格上写坐标。",
                    "按任务指定间隔生成确定的 elevation level 集合，例如只使用正高程等级；不要使用自动分级、包含 0/负值的默认 levels，或让不同 attempt 改变 level 集合。",
                    "使用 skimage 或 matplotlib contour 时，要明确该库返回的是数组 row/col 坐标还是绘图坐标，并用对应 raster transform 转成地图 x/y；不要把数组坐标直接写入矢量文件。",
                    "不要随意添加或删除半像元偏移；如果所用 contour 坐标语义是像元中心，应一致地用像元中心坐标转换，并用输出 bounds 复核没有整体平移。",
                    "避免在填充值或 NoData 边界上生成伪线段；contour 前可把无效区域设为 masked/NaN，并在写出前过滤含 NaN/Inf 或长度为 0 的线。",
                    "若使用 matplotlib contour，cs.allsegs 中每个 segment 通常已经是 Nx2 顶点数组；只有 get_paths() 返回的 Path 才使用 path.vertices，不要混用两套 API。",
                    "每个输出要素应是有效且长度大于 0 的 LineString；写出前显式过滤 empty、invalid、zero-length、少于两个不同坐标或含 NaN/Inf 的线。",
                    "每条有效 contour 线应包含稳定递增的 id 和数值 elevation 字段；同一 elevation 的所有有效线段都应保留，不要 dissolve 到丢失属性。",
                    "若 schema、CRS、level set 和 LineString health 已经通过但 contours_by_elevation 仍失败，应停止只调字段或半像元；优先统一 contour 引擎、重采样方法、mask 填充值和行列到地图坐标约定这四个会改变 per-level 长度/覆盖的环节。",
                    "修复后按 elevation 分组复核线段数量、总长度量级、空间覆盖范围、CRS、字段类型和 Shapefile sidecar 是否同时成立。",
                ]
            )
        if re.search(HILLSHADE_PATTERN, combined):
            if ErrorAwarePlugin._has_hillshade_negative_correlation(signal):
                actions.extend(
                    [
                        "可见指标显示 hillshade pixel_correlation 为强负相关时，优先按光照方向、aspect 公式、row 方向或 y 像元间距符号反转来修；先不要把问题归因到字段、输出文件名或无关 CRS 元数据。",
                        "负相关修复应保持同一 DEM profile、mask、dtype 和输出文件契约，只调整梯度/aspect/azimuth 转换中的方向约定；避免一边修方向一边改 NoData 或 transform 造成新失败。",
                    ]
                )
            actions.extend(
                [
                    "hillshade 修复应从源 DEM 的 masked array 开始，只在有效高程像元上计算光照；无效像元在输出中应保持为任务要求的背景/NoData 值。",
                    "从 DEM transform 读取 x/y 像元间距；若 DEM 是 geographic CRS，应在栅格中心纬度把经纬度间距换算成近似米制距离，x 间距需乘 cos(latitude)。",
                    "north-up raster 通常 transform.e 为负，row 增大代表向南；计算 dz/dx、dz/dy 和 aspect 时必须处理这个方向约定，避免光照方向整体翻转。",
                    "使用任务给定的 azimuth/altitude 约定：azimuth 通常从北顺时针，altitude 是太阳高度角；公式中的角度要统一转为 radians。",
                    "使用 numpy.gradient 时显式传入 y/x 间距，并确认返回梯度顺序与数组 row/col 方向一致；不要把 row spacing 和 column spacing 互换。",
                    "输出 GeoTIFF profile 应复制源 DEM 的 CRS、transform、height、width、count，并明确 dtype、nodata；hillshade 常见契约是 uint8、nodata/background 为 0。",
                    "把有效 hillshade 值裁剪/缩放到 0-255，mask 外像元写为 NoData/background；不要让 NaN、负值或浮点数组直接进入 uint8 输出。",
                    "修复后复核输出 band count、shape、CRS、transform、nodata、dtype、有效像元 mask、值域，以及山脊/山谷阴影方向是否与 azimuth 语义一致。",
                ]
            )
        if re.search(LANDSCAN_PATTERN, combined):
            actions.extend(
                [
                    "LandScan 统计应以输入 polygon 为主表：保留每个 polygon 的几何、顺序和 CRS，只在统计环节把 polygon 转到 raster CRS。",
                    "输出字段契约要显式绑定：s_fid 表示源 polygon 身份；px_count、pop_sum、pop_mean、pop_min、pop_max 都应为数值字段并来自有效像元统计。",
                    "px_count 必须等于用于 pop_sum/pop_mean/pop_min/pop_max 的同一 valid_values 数组长度；不要从窗口面积、polygon 面积、全窗口像元数或另一个 mask 单独计算。",
                    "窗口统计时先用 raster transform 得到整数 Window，读取该 window 后用同一个 window transform 建立 pixel-center zone mask，再与 LandScan NoData/dataset mask 求交集。",
                    "不要依赖 Shapefile driver 自动 FID 充当 s_fid；应从源属性或源行顺序显式生成 s_fid，并在写出前确认没有空值、字符串 None 或错位。",
                    "px_count 是有效 LandScan 像元数量，不是人口总和、polygon 面积或所有接触像元数量；pop_mean 应由有效人口值计算，而不是由全窗口背景参与平均。",
                    "LandScan NoData、mask 外像元和无效填充值必须排除；若一个 polygon 没有有效像元，应按任务契约处理空统计，不要伪造人口值。",
                    "写出前检查字段名没有被截断或重命名，所有 pop_* 和 px_count 可被读取为 numeric，s_fid 与源 polygon 一一对应。",
                ]
            )
        if re.search(ZONAL_STATS_PATTERN, combined):
            actions.extend(
                [
                    "zonal statistics 应用 raster 自身 transform 和 shape 建立 polygon mask；若裁剪窗口统计，必须使用同一 window transform，而不是源全图 transform 或 polygon bounds 近似。",
                    "pixel-center inclusion 表示只有像元中心落入 polygon 才参与统计；使用 rasterize/geometry_mask 时应保持 all_touched=False，并确认 invert/True-False 语义没有写反。",
                    "统计数组应是 zone_mask 与 valid_data_mask 的交集：同时满足位于 polygon 内、不是 NoData、不是 mask 外、不是无效填充值。",
                    "若用 rasterio.windows.from_bounds，必须对 window 做 round_offsets/round_lengths 或等价整数化；geometry_mask 的 out_shape 应来自实际读取的 data.shape，transform 应来自 rasterio.windows.transform(window, src.transform)。",
                    "px_count/stat_count、min、max、mean、std、sum 必须全部从同一个 valid_values 数组计算；不能用一个 mask 计数、另一个 mask 算统计。",
                    "使用 rasterio.windows.from_bounds/intersection 后，应把 window 偏移和长度规范成整数，或直接用 data.shape 作为 geometry_mask 的 out_shape，避免把浮点 Window 宽高传给需要整数的数组尺寸。",
                    "如果统计结果显示 0 个 polygon 有有效像元，先检查 window/rasterize 异常、window 整数化和 mask 语义；不要在没有 CRS/bounds 证据时把 lon/lat 轴交换当作修复。",
                    "min、max、mean、std、sum 应从同一组有效像元计算；std 默认使用总体标准差 ddof=0，除非任务明确要求样本标准差。",
                    "输出 polygon 的行数、顺序、几何和 CRS 应与任务输出契约一致；统计时可临时投影，写出时不要把几何留在 raster CRS。",
                    "输出字段应使用任务指定名称和数值类型，例如 stat_min/stat_max/stat_mean/stat_std/stat_sum；不要把字段写成对象字符串或因 Shapefile 限制被意外截断。",
                    "修复后用一个小 polygon 独立重算有效像元数量和五个统计量，确认 inclusion、NoData 排除和字段绑定三者同时正确。",
                ]
            )
        if re.search(RASTER_REPROJECT_PATTERN, combined):
            actions.extend(
                [
                    "栅格重投影任务应使用 rasterio.warp.calculate_default_transform 或任务指定分辨率计算 target transform、width 和 height。",
                    "若任务指定 30 米像元，应在目标 CRS 中显式使用 resolution=(30, 30)，并确保 transform 的像元大小为 30 x 30。",
                    "写出时必须把 dst_crs 作为 output profile 的 crs，并保留源 band count、dtype、NoData；使用 nearest-neighbor 时不要换成 bilinear/cubic。",
                    "重投影后检查 CRS metadata、bounds、pixel size、valid pixel coverage、NoData 和有效值范围，避免只有数组正确但 CRS 字段缺失。",
                ]
            )
        if re.search(ATTRIBUTE_FILTER_PATTERN, combined):
            actions.extend(
                [
                    "属性过滤任务应按源字段的真实类型比较代码值；若 STATEFP 是字符串，应按零填充字符串排除，如 '02'、'15'、'72'，不要转 int 后丢失前导零。",
                    "过滤后输出必须保留源几何、源 CRS 和所有原始属性；不要 dissolve、重投影到无关 CRS 或只输出筛选字段。",
                    "写出前检查排除代码集合、保留 feature count、STATEFP 唯一值、几何类型和 Shapefile 组件。",
                ]
            )
        if re.search(POLYGON_DIFFERENCE_PATTERN, combined):
            actions.extend(
                [
                    "polygon erase/merge 任务应先统一两个图层到目标 CRS，再计算 generated polygon 与 county union 的 difference，保留未重叠 residual polygon。",
                    "最终输出应把原 counties 要素和 residual polygon 合并到同一个 polygon 图层；不要把 overlap 部分重复写入或把 counties 从结果中删除。",
                    "difference 后应修复空几何和无效几何，展开 MultiPolygon 中的有效 polygon，并保证输出 CRS 与任务一致。",
                ]
            )

        if re.search(
            r"\bslope\b|finite differences|gradient|pixel sizes?|nearest raster cell|sample slope|centroid_slope|terrain_derivatives|coordinates_and_elevation",
            combined,
        ):
            actions.extend(
                [
                    "DEM 坡度/采样任务应先在 DEM 原始网格上用像元大小计算 x/y 方向梯度，再把坡度转换为 degree；不要在经纬度度单位上直接做米制坡度。",
                    "建筑物或采样点应先与 DEM 处于同一投影坐标语义下，再用 raster transform 把点坐标转换为 row/col，并按最近有效像元或任务指定采样规则取值。",
                    "采样输出必须保留源要素身份与几何顺序，新增坡度或高程字段应为数值型，并避免把 DEM NoData 或越界像元当作 0。",
                    "修复后检查点数、id 集合、坡度字段、采样 row/col 范围、NoData 排除和输出 CRS/profile 语义是否同时成立。",
                ]
            )

        if re.search(
            r"nearest estimated|ground truth|location error|matched_ground_truth|within\s+\d+(\.\d+)?\s*meters?|valid_pair_flags|checkpoint_id_set|nearest_sample_values",
            combined,
        ):
            actions.extend(
                [
                    "最近匹配任务应以参考/ground-truth 对象为主表逐一查找候选目标，按真实距离选择阈值内最近目标，并保留未匹配对象的处理语义。",
                    "匹配后输出应保留参考对象几何和身份字段，再添加目标对象 id、距离/误差字段和匹配标志；不要把 estimated 点集顺序当作 ground-truth 顺序。",
                    "若任务要求一对一匹配，应避免多个参考对象复用同一目标对象；若允许复用，也要让输出字段明确体现任务定义。",
                    "摘要文件应基于成功匹配的参考对象集合计算数量和均值，不能把未匹配对象或超过阈值对象纳入平均误差。",
                ]
            )

        if re.search(LINE_VERTEX_PATTERN, combined):
            actions.extend(
                [
                    "LineString 顶点展开应遍历每个输入要素的完整坐标序列，逐坐标写成 Point；闭合线最后一个重复坐标也必须保留。",
                    "输出应保持坐标多重集而不是集合：不要用 set、drop_duplicates、unary_union 或几何 dissolve 去重重合点。",
                    "每个输出点都要继承其来源线要素的 index 字段；若输入字段存在 index，应复制该属性值，不要写成空值、行号猜测或字符串 None。",
                    "若存在 MultiLineString，应按子线顺序展开所有子线坐标；输出 CRS 与源线 CRS 保持一致。",
                ]
            )

        if re.search(
            ROAD_OVERLAY_PATTERN,
            combined,
        ):
            actions.extend(
                [
                    "道路叠加行政区任务应先统一道路与面数据的空间参考，再用 overlay/intersection/sjoin 后裁剪线段到面边界，而不是只按 bbox 或属性连接。",
                    "每个输出道路片段应绑定相交省份的 prov_id、prov_name、pinyin、prov_code 等目标面属性，并保留或重算线段长度字段。",
                    "长度字段应在合适的投影单位下计算，若源 CRS 不适合米制长度，应临时投影计算后再按任务要求写回源 CRS。",
                    "输出前检查道路片段数量、几何类型、属性字段完整性、长度字段数值型和 Shapefile 主/sidecar 文件是否完整。",
                ]
            )

        if re.search(PROTECTED_ROAD_LENGTH_PATTERN, combined):
            actions.extend(
                [
                    "保护区道路长度任务应以 polygon 区域为主表保留所有区域要素及属性，再把道路裁剪后的长度按区域 fid 汇总回主表。",
                    "overlay 前应把区域标识复制成稳定聚合键（如 _region_fid），并只用 roads[['geometry']] 与 regions[['_region_fid','geometry']] 参与相交，避免道路 fid 与区域 fid 在 overlay 后变成 fid_1/fid_2。",
                    "先确认道路和区域在任务要求的米制 CRS 中；使用真实 line-polygon intersection 得到 clipped road segments 后再计算长度。",
                    "overlay/intersection 后必须先把结果筛为顶层 LineString/MultiLineString 再计算 length_m；不要对未过滤的 GeoSeries 直接 .length。",
                    "Point、Polygon 或 GeometryCollection 等边界接触/混合几何不能直接参与道路长度汇总；若确需处理集合，也必须先显式抽取线性分量并验证不会引入边界伪长度。",
                    "按稳定区域键聚合后再 left join 回原始区域 fid；没有道路穿过的区域 length_m 应为 0.0，且 length_m 必须是数值字段。",
                ]
            )

        if re.search(VORONOI_PATTERN, combined):
            actions.extend(
                [
                    "有界 Voronoi/Thiessen 任务应先用输入点生成全局 Voronoi 单元，再用任务指定边界裁剪每个单元；若任务说 source extent expanded by 100，应使用源要素总 bounds 向外扩展 100 native units 的 box 作为最终裁剪边界。",
                    "不要假设 shapely.ops.voronoi_diagram 的 envelope/extend_to 参数已经完成最终裁剪；每个 cell 写出前都必须显式执行 cell.intersection(boundary)。",
                    "输出应保证每个输入点对应一个 polygon，并保留点身份字段；不要输出无界射线、裸线段、点缓冲近似或未裁剪的无限多边形。",
                    "若使用 scipy.spatial.Voronoi，应添加足够远的辅助点或用有限区域重建方法关闭无界 cell，再逐个输入点裁剪到任务边界。",
                    "不能假设 shapely.ops.voronoi_diagram 返回 polygon 的顺序等于输入点顺序；应通过每个 centroid 落在哪个 cell 内来绑定 source_id。",
                    "构造后修复空几何和无效 polygon，输出 source_id 为零基输入顺序，并保持 supplied local planar CRS。",
                ]
            )

        if re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, combined) and not re.search(VORONOI_PATTERN, combined):
            actions.extend(
                [
                    "最小外接/最小旋转矩形修复应以每个输入要素或任务指定分组为单位生成一个 polygon，并显式保留源 id 或分组 id。",
                    "若任务要求 minimum rotated rectangle，应使用几何的 minimum_rotated_rectangle/oriented_envelope 语义，不要用 axis-aligned bounds、buffer 或 Voronoi 近似。",
                    "若任务要求 convex hull，应只对任务指定的点/几何集合求 hull；不要把全局 hull 复制给每个对象或把 hull 与 bounding box 混淆。",
                    "写出前检查 polygon 有效性、面积量级、源 id 绑定、feature count、CRS 和输出 schema。",
                ]
            )

        if re.search(connector_pattern, combined):
            actions.extend(
                [
                    "把最近连接、最近设施或最近目标任务视为空间分配问题：应为每个源对象寻找真正最近的目标几何，并连接到目标几何上的最近点。",
                    "使用空间索引时要显式把返回的索引映射回目标要素表；若 STRtree/query_nearest 返回数组或索引对，应逐个源对象确认目标行号和目标几何。",
                    "生成连接线时优先使用源几何与目标几何之间的最近点对，而不是目标质心、代表点或包围盒中心。",
                    "若需要输出源对象顺序、源对象属性和目标对象属性，应把源/目标属性语义映射到最终字段名，而不是假设输入字段名已经与输出字段名完全相同。",
                    "若任务包含离群过滤，应先在完整候选连接集合上计算距离统计量，再按任务阈值过滤输出对象。",
                    "输出文件名和 Shapefile sidecar 组件必须与任务契约一致；不要因字段别名缺失或单条连接失败导致完全不写输出。",
                    "修复后重新检查连接线数量、几何端点、距离字段、源对象顺序、目标对象属性和输出文件名是否共同满足任务语义。",
                ]
            )

        if re.search(r"feature_count|id_set|preserved_attributes|schema|field|column|tag|attribute", combined):
            actions.extend(
                [
                    "先确认筛选或连接条件来自真实源属性语义，而不是文件名、输出名或字段名猜测。",
                    "若关键属性被编码在字符串字段中，应鲁棒解析 JSON、Python 字面量或键值对文本，并保留原始属性和 CRS。",
                    "对于 Shapefile/DBF 的长字符串属性，不要把完整解析失败等同于类别缺失；必要时保留文本级 key-value 模式匹配，避免因字段截断漏选要素。",
                    "修复后重新检查要素数量、要素身份集合、几何类型和关键属性是否同时满足任务要求。",
                ]
            )
        if re.search(r"transform|pixel|grid|extent|alignment|window|profile|raster|dem|hillshade|contour", combined):
            actions.extend(
                [
                    "处理栅格裁剪、派生或重采样时，应从源栅格或裁剪窗口继承 CRS、transform、pixel size、nodata、dtype、count、height 和 width；不要随手重建一个无关 profile。",
                    "如果使用窗口或 mask 裁剪，应使用窗口/裁剪函数返回的 transform 更新输出 profile，使像元行列与地图坐标精确对齐。",
                    "写出 GeoTIFF 前检查输出数组形状与 profile 的 height/width 一致，transform 的平移项和像元大小与输出范围一致。",
                    "派生栅格或栅格采样时，应用 raster transform/index 将地图坐标与 row/col 互转；不要把数组行列号直接当作地图坐标。",
                ]
            )
        if re.search(r"clip.*dem|dem.*clip|pa_dem_clipped|raster_shape|dem_values|nodata_mask", combined):
            actions.extend(
                [
                    "DEM 按面边界裁剪任务应把边界重投影到 DEM CRS 后优先使用 rasterio.mask.mask(src, shapes, crop=True, filled=True, nodata=src.nodata) 同时获得裁剪数组和 out_transform。",
                    "若不用 rasterio.mask.mask 而手写 window + geometry_mask，必须确认 geometry_mask 的 True/False 语义：inside polygon 的像元应保留原 DEM 值，outside union 的像元应写 NoData。",
                    "输出 profile 应从源 DEM profile 复制并只更新 height、width、transform、count、nodata、dtype；不要只按 bounds 裁剪后忘记 union 外 mask。",
                    "裁剪后的有效高程值必须来自源 DEM 原值，不做重采样、缩放或填 0；NoData mask 应和 polygon union 外部一致。",
                ]
            )
        if re.search(r"contour|elevation|line_geometry_health", combined):
            actions.extend(
                [
                    "栅格等值线任务应使用当前环境可用的稳定等值线方法，例如 skimage.measure.find_contours 或 matplotlib contour 结果转换；避免调用不存在的 rasterio.features.contours/contour_generate。",
                    "生成等值线前先建立有效像元 mask，避免 NoData、NaN、背景值或相等端点插值产生 NaN/Inf 几何。",
                    "把等值线从行列坐标转换到源栅格 transform 对应的地图坐标，并保留源 CRS；不要把像素坐标直接写成空间坐标。",
                    "输出前检查每条等值线为有效 LineString，并包含任务要求的数值级别字段，级别值应来自任务指定 elevation/level 而不是自动分级猜测。",
                ]
            )
        if re.search(CONTOUR_PATTERN, combined):
            actions.extend(
                [
                    "DEM 重投影后生成等值线时，应先把源 NoData 语义设置清楚；若任务声明源值 0 为 NoData，应在重投影和 contour 前把 0 排除为无效值。",
                    "按任务指定间隔生成严格的正高程 level 序列，例如从第一个正的间隔值开始到有效最大值；不要生成 0、负值或自动猜测的非任务级别。",
                    "若用 skimage.measure.find_contours，返回坐标是数组 row/col 浮点坐标，必须用重投影后 raster transform 转成地图 x/y 坐标，再写 LineString。",
                    "每条 contour 输出应有稳定递增 id 和数值 elevation 字段；过滤少于两个有效坐标、NaN 坐标、空线和无效线。",
                ]
            )
        if re.search(ZONAL_STATS_PATTERN, combined):
            actions.extend(
                [
                    "栅格分区统计应把 polygon 复制到 raster CRS 中做 mask，但最终输出 CRS 应遵循任务要求，通常保留源 polygon CRS。",
                    "使用 pixel-center inclusion 时应保持 all_touched=False；统计对象是落入 polygon 的有效像元中心，而不是所有接触 polygon 的像元。",
                    "统计前必须排除 raster NoData、mask 外像元和无效值；px_count/stat_count 只计算有效像元。",
                    "输出字段应使用任务指定名称和数值类型，例如 stat_min/stat_max/stat_mean/stat_std/stat_sum 或 px_count/pop_sum/pop_mean/pop_min/pop_max。",
                    "若源 polygon 含 fid 且任务要求重命名，应先复制为 s_fid，再避免写出时与 driver 自动 fid 混淆。",
                ]
            )
        if re.search(RASTER_REPROJECT_PATTERN, combined):
            actions.extend(
                [
                    "栅格重投影任务应使用 rasterio.warp.calculate_default_transform 或任务指定分辨率计算 target transform、width 和 height。",
                    "若任务指定 30 米像元，应在目标 CRS 中显式使用 resolution=(30, 30)，并确保 transform 的像元大小为 30 x 30。",
                    "写出时必须把 dst_crs 作为 output profile 的 crs，并保留源 band count、dtype、NoData；使用 nearest-neighbor 时不要换成 bilinear/cubic。",
                    "重投影后检查 CRS metadata、bounds、pixel size、valid pixel coverage、NoData 和有效值范围，避免只有数组正确但 CRS 字段缺失。",
                ]
            )
        if re.search(ATTRIBUTE_FILTER_PATTERN, combined):
            actions.extend(
                [
                    "属性过滤任务应按源字段的真实类型比较代码值；若 STATEFP 是字符串，应按零填充字符串排除，如 '02'、'15'、'72'，不要转 int 后丢失前导零。",
                    "过滤后输出必须保留源几何、源 CRS 和所有原始属性；不要 dissolve、重投影到无关 CRS 或只输出筛选字段。",
                    "写出前检查排除代码集合、保留 feature count、STATEFP 唯一值、几何类型和 Shapefile 组件。",
                ]
            )
        if re.search(POLYGON_DIFFERENCE_PATTERN, combined):
            actions.extend(
                [
                    "polygon erase/merge 任务应先统一两个图层到目标 CRS，再计算 generated polygon 与 county union 的 difference，保留未重叠 residual polygon。",
                    "最终输出应把原 counties 要素和 residual polygon 合并到同一个 polygon 图层；不要把 overlap 部分重复写入或把 counties 从结果中删除。",
                    "difference 后应修复空几何和无效几何，展开 MultiPolygon 中的有效 polygon，并保证输出 CRS 与任务一致。",
                ]
            )
        if re.search(r"hillshade|shade|illumination", combined):
            actions.extend(
                [
                    "山影或 DEM 派生栅格应在源 DEM 有效像元上计算，并使用像元大小参与坡度/方位或梯度计算。",
                    "输出 hillshade 时保持源 DEM 的 CRS、transform、height、width 和 NoData/mask 语义，避免仅保存裸数组导致空间参考漂移。",
                    "hillshade 数组应写成稳定 dtype 和 0-255 或任务要求的值域，同时保留无效像元 mask。",
                    "若 DEM 是 geographic CRS，应在栅格中心纬度把经纬度像元间距近似换算为米；north-up raster 的 transform.e 通常为负，不要在没有同步调整 aspect 公式时盲目把 y 间距改成正值。",
                    "使用 numpy.gradient 时可保留 signed dy_m，并用 downhill vector 计算 aspect，例如 aspect = mod(arctan2(-dz_dx, -dz_dy), 2*pi)，以避免光照方向整体翻转。",
                ]
            )
        if re.search(r"nodata|mask|missing|null|background", combined):
            actions.extend(
                [
                    "显式区分真实观测值、背景值和 NoData/mask 状态，避免把无效像元或记录纳入统计和提取。",
                    "读取栅格时优先使用 masked array 或源 NoData 元数据；裁剪、派生和写出后要保持有效像元 mask 与输出数组一致。",
                    "不要把 NoData 填成 0 后参与均值、等值线、山影或二值掩膜；若必须填充值，应同时写正确 nodata 元数据并排除无效像元。",
                ]
            )
        if re.search(r"crs|epsg|projection|reproject", visible_failure) or re.search(
            r"crserror|proj_create|proj\.db|from_epsg", execution_log
        ):
            actions.extend(
                [
                    "保持 CRS 定义、转换目标和输出 CRS 一致；不要在生成代码中改写 PROJ_LIB、PROJ_DATA 或 GDAL_DATA。",
                    "栅格输出除了写 CRS 字段，还要让 CRS、transform、pixel size 和 extent 共同描述同一个空间位置，避免只有元数据看似正确。",
                    "遇到本机 PROJ 数据库报错时，优先依赖宿主运行环境提供的 CRS 配置，而不是手动切换到外部 PROJ 数据目录。",
                ]
            )
        if re.search(r"no module named 'osgeo'|modulenotfounderror", combined):
            actions.append("避免依赖当前环境未安装的 GIS 库，优先使用任务环境已有的 geopandas、rasterio、shapely、pyproj、numpy 和 matplotlib。")
        if re.search(r"expected_output_exists|artifact_.*_exists|missing_output", combined):
            actions.append("必须把任务要求的每个输出文件直接写入 OUTPUT_DIR，文件名、扩展名和 Shapefile 组件需与输出契约一致。")

        return ErrorAwarePlugin._dedupe(actions)

    @staticmethod
    def _failure_specific_forbidden(signal: dict[str, Any]) -> list[str]:
        failed_checks = " ".join(str(check).lower() for check in signal.get("failed_checks", []))
        failure_text = signal.get("failure_text", "").lower()
        execution_log = signal.get("execution_log_excerpt", "").lower()
        query_text = signal.get("query_text", "").lower()
        combined = " ".join([failed_checks, failure_text, execution_log, query_text])
        forbidden: list[str] = []
        if re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把距离矩阵行列标签交给 DataFrame 默认索引或排序猜测；标签必须来自源要素身份并保持一致。",
                    "不能在经纬度 CRS 下直接把 degree 距离当作米制距离，除非任务明确要求角度单位。",
                    "不能输出非对称矩阵、非零对角线，或把几何/坐标对象写进距离数值单元格。",
                ]
            )
        if re.search(TERRAIN_RUGGEDNESS_PATTERN, combined):
            forbidden.extend(
                [
                    "不能用 polygon difference、全图最大最小差或单点高程替代任务定义的局部 terrain ruggedness。",
                    "不能让 NoData 或窗口外像元参与 ruggedness 统计。",
                    "不能把窗口行列方向、中心像元或边缘处理交给默认行为而不验证。",
                ]
            )
        if re.search(POPULATION_ALLOCATION_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把源人口总量无权重复制给每个目标对象，或把目标数量平均分配当作空间分配。",
                    "不能因 overlay/sjoin 产生一对多关系就重复累计人口而不做权重或去重处理。",
                    "不能丢失 block group、建筑物、目标 polygon 等源/目标身份字段，导致人口值错行绑定。",
                ]
            )
        if re.search(RASTER_NEAREST_SAMPLING_PATTERN, combined):
            forbidden.extend(
                [
                    "不能导入不存在的 rasterio.sample.sample；应使用 src.sample(coords) 或可用的 sample_gen。",
                    "不能把点坐标直接当作 raster row/col，或把 row/col 顺序写反。",
                    "不能把 NoData、越界采样或第一个候选像元伪装成最近有效采样值。",
                ]
            )
        if re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, combined):
            forbidden.extend(
                [
                    "不能在条件 raster 未对齐时直接逐像元做布尔运算。",
                    "不能把阈值方向写反，例如把低于阈值适宜误写成高于阈值适宜。",
                    "不能让 NoData/背景像元因填 0 或填 False/True 进入最终 suitable 区域。",
                ]
            )
        if re.search(r"\bslope\b|finite differences|gradient|pixel sizes?|nearest raster cell|sample slope|centroid_slope", combined):
            forbidden.extend(
                [
                    "不能忽略 DEM pixel size 直接用数组索引差分当作真实坡度。",
                    "不能在采样点越界或落入 NoData 时返回 0 并伪装成有效坡度值。",
                    "不能丢失建筑物/采样点原始 id 或把采样结果按错误顺序写回。",
                ]
            )
        if re.search(r"nearest estimated|ground truth|location error|matched_ground_truth|within\s+\d+(\.\d+)?\s*meters?|valid_pair_flags|checkpoint_id_set|nearest_sample_values", combined):
            forbidden.extend(
                [
                    "不能把 estimated 点集顺序、最近 bbox 候选或第一个候选直接当作 ground-truth 匹配结果。",
                    "不能把超过阈值的候选纳入 matched count 或 mean error。",
                    "不能在任务要求保留 ground-truth 几何时输出 estimated 几何作为主几何。",
                ]
            )
        if re.search(LINE_VERTEX_PATTERN, combined):
            forbidden.extend(
                [
                    "不能对顶点坐标去重；重合点和闭合线重复终点都是任务定义的一部分。",
                    "不能把输出 index 字段写成空值、字符串 None 或与输入 index 字段无关的顺序号。",
                    "不能只取每条线的起点/终点或用边界框角点替代完整坐标序列。",
                ]
            )
        if re.search(ROAD_OVERLAY_PATTERN, combined):
            forbidden.extend(
                [
                    "不能只做 sjoin 后保留整条原始道路而不按省界裁剪线段。",
                    "不能只输出道路属性而丢失省份标识、名称、拼音或编码字段。",
                    "不能在经纬度 CRS 下直接把长度字段当作米制长度。",
                ]
            )
        if re.search(PROTECTED_ROAD_LENGTH_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把相交道路的整线长度分配给区域，必须使用裁剪到区域内的线段长度。",
                    "不能用道路 fid 覆盖区域 fid，也不能让 overlay 自动产生的 fid_1/fid_2 混淆区域聚合键。",
                    "不能因没有道路而删除区域要素；输出必须保留所有 polygon 区域，并把缺失 length_m 填为 0.0。",
                    "不能用 keep_geom_type=True 静默丢弃会影响长度汇总的线性相交结果；也不能用 keep_geom_type=False 后直接统计 Point/Polygon/GeometryCollection 的 length。",
                    "不能导入或使用不存在的 shapely.geometry.Linestring；Shapely 类名是 LineString，且通常可直接用 geom_type 字符串筛选线性几何。",
                ]
            )
        if re.search(VORONOI_PATTERN, combined):
            forbidden.extend(
                [
                    "不能用点缓冲、最近邻圆或未裁剪无限 Voronoi 区域代替有界 Voronoi polygon。",
                    "不能只把扩展 envelope 传给 Voronoi 函数后就直接写出结果；必须再次用任务边界逐 cell 裁剪。",
                    "不能输出少于或多于输入点数量的单元，除非任务明确允许合并或过滤。",
                    "不能让 Voronoi 单元越过任务指定的 convex hull 或边界。",
                    "不能把 Voronoi 输出列表顺序直接当作输入点顺序，除非已逐点验证对应关系。",
                ]
            )
        if re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, combined) and not re.search(VORONOI_PATTERN, combined):
            forbidden.extend(
                [
                    "不能用 axis-aligned bounds 代替 minimum rotated rectangle，除非任务明确要求普通 bbox。",
                    "不能用点缓冲、Voronoi cell 或全局 hull 代替每个源对象/分组的最小外接几何。",
                    "不能丢失源 id 绑定或输出无效/空 polygon。",
                ]
            )
        if re.search(r"connector_geometry|nearest|nearest_.+|dist_m|flood_ord|\biqr\b|\bq1\b|\bq3\b", combined):
            forbidden.extend(
                [
                    "不能把空间索引返回的包围盒候选、任意相交候选或第一个候选直接当作最近目标。",
                    "不能用目标对象质心或代表点替代任务要求的目标几何最近点，除非任务明确允许近似。",
                    "不能在生成完整连接集合之前就计算离群阈值或丢弃候选连接。",
                    "不能因为某个目标属性字段名不完全匹配就中止整个输出；应先检查可用字段、别名和任务所需语义。",
                ]
            )
        if re.search(r"transform|pixel|grid|extent|alignment|window|profile|raster|dem|hillshade|contour", combined):
            forbidden.extend(
                [
                    "不能用 from_origin(0, height, 1, 1) 或任意默认 transform 代替源栅格/裁剪窗口的真实 transform。",
                    "不能只写数组而不更新 GeoTIFF profile 中的 CRS、transform、height、width、nodata 和 dtype。",
                    "不能把 contour 的行列坐标、数组索引或绘图坐标直接当作地图坐标输出。",
                    "不能在栅格裁剪后沿用源 height/width 却写出新的小数组，或只改数组不改 profile。",
                ]
            )
        if re.search(CONTOUR_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把 DEM 中任务声明的 NoData 值当作真实高程参与等值线。",
                    "不能输出 0 或负高程等值线，除非任务明确要求。",
                    "不能把 skimage/matplotlib contour 的 row/col 坐标直接写入 Shapefile。",
                    "不能让 id/elevation 字段缺失、非数值或与实际 contour level 不一致。",
                    "不能在 NoData 填充值边界上生成伪等值线，再通过 dissolve 或 simplify 掩盖几何不一致。",
                    "不能在不了解 contour 库坐标约定时盲目添加或删除半像元偏移。",
                    "不能把 matplotlib cs.allsegs 中的 ndarray segment 当作 Path 对象访问 .vertices。",
                    "不能把 invalid、zero-length、重复坐标退化线或含非有限坐标的 LineString 写入最终 contour 图层。",
                    "不能在 contours_by_elevation 失败但 schema/CRS/line health 已通过时继续只改字段名、driver 或 simplify 参数；根因通常在 DEM 预处理、contour 引擎或坐标转换。",
                ]
            )
        if re.search(HILLSHADE_PATTERN, combined):
            forbidden.extend(
                [
                    "不能在 geographic CRS 下直接用度单位当作米制水平距离计算坡度或山影。",
                    "不能盲目把 north-up raster 的 y pixel size 改成正值而不同步修正梯度/aspect 方向；这会造成 hillshade 光照方向翻转。",
                    "不能把 row/col 梯度顺序写反，或把 azimuth 当作从东逆时针的数学角而不转换。",
                    "不能输出缺 CRS/transform/profile 的裸数组，也不能把 float hillshade 直接写成没有 nodata 的 GeoTIFF。",
                    "不能让 DEM NoData 或 mask 外像元参与梯度，再只在最后把输出裁成 0。",
                ]
            )
        if re.search(LANDSCAN_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把 s_fid 留给 driver 自动生成，或让它与源 polygon 顺序、源 fid、统计行错位。",
                    "不能把 px_count 写成人口总和、polygon 面积、窗口像元总数或字符串字段。",
                    "不能把 pop_sum/pop_mean/pop_min/pop_max 从不同像元集合分别计算；它们必须来自同一有效像元 mask。",
                    "不能用 all_touched、bbox window 全量像元或 polygon 面积近似替代 pixel-center inclusion 下的有效 LandScan 像元集合。",
                    "不能因为字段类型写错而把数值字段存成 object/string，导致 evaluator 无法按 numeric 比较。",
                ]
            )
        if re.search(ZONAL_STATS_PATTERN, combined):
            forbidden.extend(
                [
                    "不能用 all_touched=True 替代任务要求的 pixel-center inclusion。",
                    "不能把 NoData、mask 外像元或填充值纳入 min/max/mean/std/sum。",
                    "不能在输出回源 polygon CRS 时把几何留在 raster CRS，或丢失源 polygon 属性。",
                    "不能让源 fid 与输出 driver 的 fid 混淆；任务要求时应显式重命名为 s_fid。",
                    "不能用 polygon centroid 单点采样、bbox 均值或全 raster 统计代替 polygon 内有效像元统计。",
                    "不能把 geometry_mask 的 True/False 语义写反，导致 polygon 外部像元参与统计。",
                    "不能把 rasterio Window 的浮点 width/height 直接传入 geometry_mask 或 numpy 数组 shape；应使用整数 window 或 data.shape。",
                    "不能让 px_count/stat_count 与 min/max/mean/std/sum 使用不同的 valid mask。",
                    "不能因为所有统计为空或 window 为空就启发式交换 lon/lat；只有明确 CRS/axis/bounds 证据支持时才考虑 A1 轴序问题。",
                ]
            )
        if re.search(RASTER_REPROJECT_PATTERN, combined):
            forbidden.extend(
                [
                    "不能只改 profile.crs 而不真正重投影数组、transform、width/height 和 bounds。",
                    "不能在任务要求 30m 像元时沿用源分辨率或自动分辨率。",
                    "不能把 nearest-neighbor 重采样替换成会改变类别/离散 DEM 值语义的其他方法，除非任务允许。",
                ]
            )
        if re.search(ATTRIBUTE_FILTER_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把 STATEFP 前导零丢掉后再比较排除列表。",
                    "不能只按州名、文件名或空间位置猜测 contiguous US，而忽略任务给出的 STATEFP 代码列表。",
                    "不能丢弃原始属性或改变源几何。",
                ]
            )
        if re.search(POLYGON_DIFFERENCE_PATTERN, combined):
            forbidden.extend(
                [
                    "不能把 generated polygon 与 counties 简单 append 后造成重叠区域重复。",
                    "不能用 union 替代 difference；任务要求去掉 overlap 后再 merge。",
                    "不能写出空 residual、无效 polygon 或错误 CRS。",
                ]
            )
        if re.search(r"clip.*dem|dem.*clip|pa_dem_clipped|raster_shape|dem_values|nodata_mask", combined):
            forbidden.extend(
                [
                    "不能只按 polygon bounds 裁剪后把边界外像元继续保留为有效 DEM 值。",
                    "不能把 geometry_mask 的 True/False 语义写反，导致 polygon 内部变 NoData、外部保留原值。",
                    "不能把源 DEM 的有效高程值改成 0、NaN 或新插值结果来凑输出形状。",
                ]
            )
        if re.search(r"hillshade|shade|illumination", combined):
            forbidden.extend(
                [
                    "不能在 geographic CRS 下直接用度单位当作米制水平距离计算坡度或山影。",
                    "不能盲目把 north-up raster 的 y pixel size 改成正值而不同步修正梯度/aspect 方向；这会造成 hillshade 光照方向翻转。",
                ]
            )
        if re.search(r"nodata|mask|missing|null|background", combined):
            forbidden.append("不能把 NoData、背景值或 mask 外像元直接当作 0 或普通有效值参与计算。")
        return ErrorAwarePlugin._dedupe(forbidden)

    @staticmethod
    def _failure_specific_validation(signal: dict[str, Any]) -> list[str]:
        failed_checks = " ".join(str(check).lower() for check in signal.get("failed_checks", []))
        query_text = signal.get("query_text", "").lower()
        combined = " ".join([failed_checks, query_text])
        validation: list[str] = []
        if re.search(r"feature_count|id_set|geometry_by_|preserved_attributes|schema|field|column", failed_checks):
            validation.append("复核输出要素数、要素身份集合、几何逐要素一致性、字段 schema 和属性保留情况。")
        if re.search(r"expected_output_exists|artifact_.*_exists", failed_checks):
            validation.append("复核 OUTPUT_DIR 下是否存在指定主文件及必要的同名 sidecar 文件。")
        if re.search(PAIRWISE_DISTANCE_MATRIX_PATTERN, combined):
            validation.append("复核距离矩阵行列标签、shape、零对角线、对称性、距离单位、数值 dtype 和输出格式。")
        if re.search(TERRAIN_RUGGEDNESS_PATTERN, combined):
            validation.append("复核 terrain ruggedness 的局部窗口、像元间距、NoData 排除、边缘处理、统计公式和字段绑定。")
        if re.search(POPULATION_ALLOCATION_PATTERN, combined):
            validation.append("复核人口空间支持、allocation weights、population sum conservation、源/目标 id 绑定、join cardinality 和数值字段。")
        if re.search(RASTER_NEAREST_SAMPLING_PATTERN, combined):
            validation.append("复核采样点 CRS、row/col 转换、最近有效像元规则、NoData 排除、id/order 绑定和采样值字段。")
        if re.search(RASTER_BOOLEAN_SUITABILITY_PATTERN, combined):
            validation.append("复核条件 raster 对齐、阈值方向、AND/OR/NOT 组合、共同 valid mask、NoData 像元和输出 raster profile。")
        if re.search(r"crs|epsg|projection", failed_checks):
            validation.append("复核输出 CRS 与任务要求一致，且 CRS、transform/pixel size、extent 共同对应同一个空间参考。")
        if re.search(r"nodata|mask", failed_checks):
            validation.append("复核有效值、NoData、mask 和背景值的像元数量、空间分布及统计摘要。")
        if re.search(r"transform|pixel|grid|extent|alignment|window|profile|raster", failed_checks):
            validation.append("复核输出 raster profile 的 CRS、transform、height/width、pixel size、extent、dtype 和 nodata 与输出数组一致。")
        if re.search(r"clip.*dem|dem.*clip|pa_dem_clipped|raster_shape|dem_values|nodata_mask", combined):
            validation.append("复核 DEM 裁剪输出的 shape、transform、NoData mask、有效高程值范围和值逐像元一致性。")
        if re.search(r"contour|elevation|line_geometry_health", failed_checks):
            validation.append("复核等值线 level/elevation 字段、线几何有效性、坐标范围、CRS 和每个指定高程级别的要素集合。")
        if re.search(CONTOUR_PATTERN, combined):
            validation.append("复核 contour level 序列、NoData 排除、row/col 到地图坐标转换、LineString 有效性、id/elevation 字段和输出 CRS。")
            validation.append("按 elevation 分组复核每组线段数量、总长度量级、几何覆盖范围和是否存在 NoData 边界伪线或整体半像元平移。")
            validation.append("在写出前运行本地 contour verifier，确认每条线有限、非空、长度大于 0、elevation 数值绑定正确，且全部主文件和 sidecar 均位于 OUTPUT_DIR。")
        if re.search(HILLSHADE_PATTERN, combined):
            validation.append("复核 hillshade 的 shape、CRS、transform、dtype、nodata、有效像元 mask、0-255 值域、像元间距换算和光照方向。")
            validation.append("抽查 north-up DEM 的 row/col 梯度方向与 azimuth/altitude 约定，确认山脊阴影没有整体翻转或横纵间距互换。")
        if re.search(LANDSCAN_PATTERN, combined):
            validation.append("复核 s_fid 与源 polygon 一一绑定，px_count/pop_sum/pop_mean/pop_min/pop_max 为数值字段且来自同一有效 LandScan 像元集合。")
            validation.append("复核输出 geometry、行数、行顺序、CRS 和字段 schema 没有因 Shapefile 写出或 driver fid 混淆而漂移。")
            validation.append("抽查至少一个 polygon，确认 px_count == valid_values.size，且 pop_* 全部由这个 valid_values 数组计算。")
        if re.search(ZONAL_STATS_PATTERN, combined):
            validation.append("复核分区统计的 pixel-center inclusion、有效像元数量、NoData 排除、统计字段数值、输出 CRS 和源 polygon 属性保留。")
            validation.append("用 raster transform 和 polygon mask 独立重算至少一个分区，确认 all_touched=False、mask 语义和 std/sum 计算规则一致。")
            validation.append("复核 window offset/shape 为整数，geometry_mask out_shape 与 data.shape 一致，统计字段和计数字段共享同一 valid mask。")
        if re.search(RASTER_REPROJECT_PATTERN, combined):
            validation.append("复核重投影 GeoTIFF 的 CRS、transform、pixel size、width/height、bounds、resampling、dtype、band count 和 NoData。")
        if re.search(ATTRIBUTE_FILTER_PATTERN, combined):
            validation.append("复核排除 STATEFP 代码集合、保留要素数、STATEFP 字段类型/前导零、原始属性、几何和 CRS。")
        if re.search(POLYGON_DIFFERENCE_PATTERN, combined):
            validation.append("复核 residual polygon 不与 counties 重叠、counties 全部保留、合并结果 CRS 正确、几何有效且无重复 overlap。")
        if re.search(r"hillshade|shade|illumination", failed_checks):
            validation.append("复核 hillshade 数值范围、有效像元 mask、CRS/transform/profile、中心纬度米制像元间距和光照方向一致性。")
        if re.search(r"connector_geometry|nearest|dist_m|flood_ord|\biqr\b|\bq1\b|\bq3\b", failed_checks):
            validation.extend(
                [
                    "抽查每条连接线是否从源对象出发并终止于目标几何上的最近点，距离字段应与连接线长度一致。",
                    "复核离群过滤阈值是否基于完整连接长度集合计算，过滤前后的源对象顺序和目标属性应保持可追溯。",
                ]
            )
        if re.search(r"\bslope\b|finite differences|gradient|pixel sizes?|nearest raster cell|sample slope|centroid_slope", combined):
            validation.append("复核坡度单位为 degree，采样点 row/col 在 raster 范围内，NoData 被排除，输出点数和原始 id 集合保持一致。")
        if re.search(r"nearest estimated|ground truth|location error|matched_ground_truth|within\s+\d+(\.\d+)?\s*meters?|valid_pair_flags|checkpoint_id_set|nearest_sample_values", combined):
            validation.append("复核每个 ground-truth 对象的最近候选、距离阈值、匹配唯一性、输出主几何和摘要统计的 matched count/mean error。")
        if re.search(LINE_VERTEX_PATTERN, combined):
            validation.append("复核输出点坐标多重集、每个点的 index 字段、闭合重复点保留情况、输出 CRS 和 Point 几何类型。")
        if re.search(ROAD_OVERLAY_PATTERN, combined):
            validation.append("复核道路已按省界裁剪，省份字段完整绑定，seg_len_m 为数值型且长度计算单位合理。")
        if re.search(PROTECTED_ROAD_LENGTH_PATTERN, combined):
            validation.append("复核区域要素数和 fid 集合保持不变，length_m 为筛选后的 LineString/MultiLineString clipped segments 按区域 fid 汇总后的米制数值。")
        if re.search(VORONOI_PATTERN, combined):
            validation.append("复核 Voronoi polygon 数量、source_id 零基顺序、点到单元关联、逐 cell 显式裁剪后的边界范围、几何有效性和单元重叠/空洞情况。")
        if re.search(MINIMUM_BOUNDING_GEOMETRY_PATTERN, combined) and not re.search(VORONOI_PATTERN, combined):
            validation.append("复核最小外接/凸包 polygon 数量、源 id 绑定、面积/方向语义、CRS、几何有效性和输出 schema。")
        return ErrorAwarePlugin._dedupe(validation)
