from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


LABEL_KEYWORDS: dict[str, list[str]] = {
    "A1. Coordinate Axis Misinterpretation": ["axis", "lon", "lat", "longitude", "latitude", "row", "col", "swapped"],
    "A2. CRS Inconsistency": ["crs", "epsg", "projection", "reproject", "reference frame", "misaligned", "overlay"],
    "A3. Unit Misinterpretation": ["unit", "meter", "degree", "buffer", "distance", "area", "density", "radius"],
    "B1. Dataset Integrity Violation": ["missing file", "shapefile", "dbf", "prj", "schema", "field", "metadata"],
    "B2. Raster Alignment Failure": ["raster", "grid", "resolution", "extent", "pixel", "transform", "alignment"],
    "B3. Missing Data Misinterpretation": ["nodata", "mask", "missing", "null", "background", "-9999"],
    "C1. Topological Predicate Confusion": ["within", "contains", "intersects", "touches", "predicate", "spatial relation"],
    "C2. Invalid Geometry Handling": ["invalid geometry", "self-intersection", "ring", "empty geometry", "validity"],
    "C3. Network Connectivity Misinterpretation": ["network", "route", "path", "reachable", "node", "edge", "connectivity"],
    "D1. Aggregation Scope Confusion": ["aggregation", "group", "scope", "global", "local", "district", "zone"],
    "D2. Spatial Allocation Error": ["allocate", "weight", "spatial support", "centroid", "area-weighted", "transfer"],
    "D3. Spatial Statistical Misinterpretation": ["statistic", "threshold", "mean", "indicator", "denominator", "correlation"],
    "E1. Classification Scheme Misuse": ["classification", "break", "quantile", "equal interval", "class", "bin"],
    "E2. Symbolization Error": ["symbol", "color", "size", "shape", "palette", "visual encoding"],
    "E3. Map Composition Defect": ["legend", "scale", "title", "label", "layer", "composition", "context"],
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_\-.]+", text.lower()))


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
    ) -> dict[str, Any]:
        signal = self._collect_signal(task_view, generated_code, execution_log, agent_visible_report)
        candidates = self._screen_rule_cards(signal)
        classification = self._classify_with_taxonomy(signal, candidates)
        cases = self._retrieve_cases(signal, classification["candidate_labels"])
        repair_advice = self._build_repair_advice(classification, cases)
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
            "retrieved_cases": cases,
            "repair_advice": repair_advice,
        }

    def _collect_signal(
        self,
        task_view: dict[str, Any],
        generated_code: str,
        execution_log: str,
        agent_visible_report: dict[str, Any],
    ) -> dict[str, Any]:
        failure_text = " ".join(agent_visible_report.get("failure_reasons", []))
        metrics_text = json.dumps(agent_visible_report.get("metrics_diff", {}), ensure_ascii=False)
        summary = " | ".join(
            part
            for part in [
                task_view.get("prompt", ""),
                agent_visible_report.get("failure_kind", ""),
                failure_text,
                metrics_text,
                execution_log,
            ]
            if part
        )
        return {
            "summary": summary[:2000],
            "query_text": summary,
            "requires_visual_check": bool(agent_visible_report.get("requires_visual_check", False)),
            "generated_code_excerpt": generated_code[:2000],
        }

    def _screen_rule_cards(self, signal: dict[str, Any]) -> list[dict[str, Any]]:
        query = signal["query_text"].lower()
        scored: list[tuple[int, str, list[str]]] = []
        for label, keywords in LABEL_KEYWORDS.items():
            hits = [keyword for keyword in keywords if keyword in query]
            if hits:
                scored.append((len(hits), label, hits))
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
            label_bonus = 2 if case.get("primary_label") in candidate_labels else 0
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

    def _build_repair_advice(self, classification: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
        if not cases:
            return {
                "status": "insufficient_case_support",
                "message": "未检索到 verified 案例，不能编造修复案例；请基于可见证据和标注指南做保守修复。",
                "recommended_actions": [],
                "forbidden_actions": [],
                "validation_checks": [],
            }
        recommended: list[str] = []
        forbidden: list[str] = []
        validation: list[str] = []
        for case in cases:
            playbook = case["repair_playbook"]
            recommended.extend(playbook.get("recommended_actions", []))
            forbidden.extend(playbook.get("forbidden_actions", []))
            validation.extend(playbook.get("validation_checks", []))
        return {
            "status": "case_supported_repair_advice",
            "primary_candidate": classification.get("primary_candidate", ""),
            "case_count": len(cases),
            "repair_instruction": (
                "Revise the GIS workflow according to the candidate root cause, using retrieved cases only as analogies. "
                "Preserve task intent, avoid forbidden actions, and run validation checks after regenerating outputs."
            ),
            "recommended_actions": self._dedupe(recommended)[:8],
            "forbidden_actions": self._dedupe(forbidden)[:6],
            "validation_checks": self._dedupe(validation)[:8],
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
