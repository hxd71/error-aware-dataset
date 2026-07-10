import csv
import json
import math
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

try:
    from shapely import make_valid
except ImportError:  # pragma: no cover - Shapely 1.x fallback
    make_valid = None


ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data" / "geonature"
RUNS_ROOT = ROOT / "runs"

FOREST_RUN = RUNS_ROOT / "20260709_171038_gn_v5_62_forest_cover_rank_bigearthnet_deepseek-v4-pro"
CO2_RUN = RUNS_ROOT / "20260709_171112_gn_v5_21_compare_co2_candidate_pool_deepseek-v4-pro"
BUFFER_RUN = RUNS_ROOT / "20260709_171537_gbx_port_murcia_50km_buffer_intersections_deepseek-v4-pro"


def normalized_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def ensure_reference_dir(run_dir: Path) -> Path:
    reference_dir = run_dir / "reference"
    reference_dir.mkdir(exist_ok=True)
    return reference_dir


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_forest_cover() -> dict:
    stats = json.loads((DATA_ROOT / "bigearthnet_portugal_stats.json").read_text(encoding="utf-8"))
    target_districts = ["Beja", "Faro", "Lisboa", "Portalegre"]
    forest_labels = {"Coniferous Forest", "Broadleaf Forest"}
    records = []

    for district in target_districts:
        entry = stats[district]
        breakdown = entry["breakdown"]
        forest_pct = sum(float(item["percentage"]) for item in breakdown if item["label"] in forest_labels)
        forest_patch_estimate = float(entry["total_patches"]) * forest_pct / 100.0
        records.append(
            {
                "District": district,
                "ConiferousPct": next(float(item["percentage"]) for item in breakdown if item["label"] == "Coniferous Forest"),
                "BroadleafPct": next(float(item["percentage"]) for item in breakdown if item["label"] == "Broadleaf Forest"),
                "ForestCoverPct": round(forest_pct, 1),
                "ForestPatchEstimate": round(forest_patch_estimate, 2),
            }
        )

    df = pd.DataFrame(records).sort_values("ForestCoverPct", ascending=False).reset_index(drop=True)
    df["Rank"] = df["ForestCoverPct"].rank(ascending=False, method="dense").astype(int)
    observed = pd.read_csv(FOREST_RUN / "forest_cover_rank.csv")

    reference_dir = ensure_reference_dir(FOREST_RUN)
    df.to_csv(reference_dir / "forest_cover_rank_reference.csv", index=False)
    write_json(reference_dir / "forest_cover_rank_reference.json", df.to_dict(orient="records"))

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(df["District"], df["ForestCoverPct"], color="#4c8c5c")
    ax.set_ylabel("Forest cover (%)")
    ax.set_title("Reference forest cover: coniferous + broadleaf")
    for bar, rank in zip(bars, df["Rank"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8, f"#{rank}", ha="center", va="bottom")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(reference_dir / "forest_cover_rank_reference.png", dpi=160)
    plt.close(fig)

    observed_zero_count = int((observed["ForestCover"] == 0).sum())
    return {
        "task_id": "gn_v5_62_forest_cover_rank_bigearthnet",
        "reference_records": df.to_dict(orient="records"),
        "observed_records": observed.to_dict(orient="records"),
        "observed_zero_forest_rows": observed_zero_count,
        "expected_top_district": str(df.iloc[0]["District"]),
        "expected_top_forest_cover_pct": float(df.iloc[0]["ForestCoverPct"]),
        "all_observed_values_zero": observed_zero_count == len(observed),
        "reference_files": [
            "reference/forest_cover_rank_reference.csv",
            "reference/forest_cover_rank_reference.json",
            "reference/forest_cover_rank_reference.png",
        ],
    }


def find_province(provinces: dict, name: str) -> dict:
    target = normalized_name(name)
    for key, value in provinces.items():
        if normalized_name(key) == target or normalized_name(value.get("name", "")) == target:
            return value
    raise KeyError(f"Province not found: {name}")


def audit_co2_candidate_pool() -> dict:
    rankings = json.loads((DATA_ROOT / "province_rankings.json").read_text(encoding="utf-8"))
    provinces = rankings["provinces"]
    targets = ["Murcia", "Córdoba"]
    records = []
    for name in targets:
        entry = find_province(provinces, name)
        co2 = entry["co2"]
        candidate_pool = float(co2["conditional_pct"]) + float(co2["eligible_pct"])
        records.append(
            {
                "province": entry["name"],
                "not_eligible_pct": float(co2["not_eligible_pct"]),
                "conditional_pct": float(co2["conditional_pct"]),
                "eligible_pct": float(co2["eligible_pct"]),
                "candidate_pool_pct": round(candidate_pool, 1),
            }
        )

    df = pd.DataFrame(records)
    better = str(df.sort_values(["candidate_pool_pct", "eligible_pct"], ascending=False).iloc[0]["province"])
    observed = pd.read_csv(CO2_RUN / "murcia_cordoba_co2_comparison.csv")

    reference_dir = ensure_reference_dir(CO2_RUN)
    df.to_csv(reference_dir / "murcia_cordoba_co2_reference.csv", index=False)
    decision = {
        "better_province": better,
        "decision_metric": "candidate_pool_pct = conditional_pct + eligible_pct",
        "records": df.to_dict(orient="records"),
    }
    write_json(reference_dir / "murcia_cordoba_co2_reference_decision.json", decision)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    x = range(len(df))
    ax.bar(x, df["conditional_pct"], label="Conditional", color="#f0b35e")
    ax.bar(x, df["eligible_pct"], bottom=df["conditional_pct"], label="Eligible", color="#5f8cc0")
    ax.set_xticks(list(x), df["province"])
    ax.set_ylabel("Territory share (%)")
    ax.set_title("Reference CO2 candidate pool")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(reference_dir / "murcia_cordoba_co2_reference.png", dpi=160)
    plt.close(fig)

    observed_candidate_values = [float(value) for value in observed["candidate_pool"].tolist()]
    return {
        "task_id": "gn_v5_21_compare_co2_candidate_pool",
        "reference_decision": decision,
        "observed_records": observed.to_dict(orient="records"),
        "observed_candidate_pool_values": observed_candidate_values,
        "expected_better_province": better,
        "all_observed_candidate_values_zero": all(value == 0 for value in observed_candidate_values),
        "reference_files": [
            "reference/murcia_cordoba_co2_reference.csv",
            "reference/murcia_cordoba_co2_reference_decision.json",
            "reference/murcia_cordoba_co2_reference.png",
        ],
    }


def ring_is_usable(ring: list) -> bool:
    return isinstance(ring, list) and len(ring) >= 4


def clean_geometry_dict(geometry: dict) -> tuple[dict | None, dict]:
    stats = {"total_rings": 0, "dropped_degenerate_rings": 0}
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")

    def clean_polygon(poly_coords: list) -> list | None:
        if not poly_coords:
            return None
        cleaned = []
        for ring in poly_coords:
            stats["total_rings"] += 1
            if ring_is_usable(ring):
                if ring[0] != ring[-1]:
                    ring = ring + [ring[0]]
                cleaned.append(ring)
            else:
                stats["dropped_degenerate_rings"] += 1
        if not cleaned:
            return None
        return cleaned

    if geom_type == "Polygon":
        polygon = clean_polygon(coords)
        if polygon is None:
            return None, stats
        return {"type": "Polygon", "coordinates": polygon}, stats
    if geom_type == "MultiPolygon":
        polygons = []
        for poly_coords in coords:
            polygon = clean_polygon(poly_coords)
            if polygon is not None:
                polygons.append(polygon)
        if not polygons:
            return None, stats
        return {"type": "MultiPolygon", "coordinates": polygons}, stats
    return geometry, stats


def valid_geometry(geometry):
    if make_valid is not None:
        geometry = make_valid(geometry)
    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    return geometry


def write_feature_collection(path: Path, features: list[dict]) -> None:
    write_json(path, {"type": "FeatureCollection", "features": features})


def iter_polygons(geometry):
    if geometry.is_empty:
        return
    if geometry.geom_type == "Polygon":
        yield geometry
    elif geometry.geom_type == "MultiPolygon":
        yield from geometry.geoms
    elif geometry.geom_type == "GeometryCollection":
        for part in geometry.geoms:
            yield from iter_polygons(part)


def audit_murcia_buffer() -> dict:
    raw = json.loads((DATA_ROOT / "spain_provinces.geojson").read_text(encoding="utf-8"))
    cleaned_features = []
    total_rings = 0
    dropped_rings = 0
    features_with_dropped_rings = 0

    for feature in raw["features"]:
        cleaned_geometry, stats = clean_geometry_dict(feature["geometry"])
        total_rings += stats["total_rings"]
        dropped_rings += stats["dropped_degenerate_rings"]
        if stats["dropped_degenerate_rings"] > 0:
            features_with_dropped_rings += 1
        if cleaned_geometry is None:
            continue
        geom = valid_geometry(shape(cleaned_geometry))
        if geom.is_empty:
            continue
        cleaned_features.append(
            {
                "type": "Feature",
                "properties": feature["properties"],
                "geometry": mapping(geom),
            }
        )

    to_25830 = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True).transform
    to_4326 = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True).transform
    murcia_feature = next(feature for feature in cleaned_features if feature["properties"].get("name") == "Murcia")
    murcia_geom_25830 = transform(to_25830, shape(murcia_feature["geometry"]))
    buffer_25830 = murcia_geom_25830.buffer(50000)
    buffer_4326 = transform(to_4326, buffer_25830)

    intersecting = []
    selected_features = []
    for feature in cleaned_features:
        geom_25830 = transform(to_25830, shape(feature["geometry"]))
        if geom_25830.intersects(buffer_25830):
            props = feature["properties"]
            distance_m = 0.0 if geom_25830.intersects(murcia_geom_25830) else geom_25830.distance(murcia_geom_25830)
            intersecting.append(
                {
                    "name": props.get("name"),
                    "code": props.get("code"),
                    "distance_to_murcia_m": round(distance_m, 2),
                }
            )
            selected_features.append(feature)

    intersecting = sorted(intersecting, key=lambda row: (row["distance_to_murcia_m"], row["name"]))
    reference_dir = ensure_reference_dir(BUFFER_RUN)
    with (reference_dir / "murcia_50km_intersecting_provinces_reference.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "code", "distance_to_murcia_m"])
        writer.writeheader()
        writer.writerows(intersecting)
    write_json(reference_dir / "murcia_50km_intersecting_provinces_reference.json", intersecting)
    write_feature_collection(
        reference_dir / "murcia_50km_buffer_reference.geojson",
        [{"type": "Feature", "properties": {"name": "Murcia 50 km buffer"}, "geometry": mapping(buffer_4326)}],
    )
    write_feature_collection(reference_dir / "murcia_50km_selected_provinces_reference.geojson", selected_features)

    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    for feature in cleaned_features:
        geom = shape(feature["geometry"])
        for polygon in iter_polygons(geom):
            x, y = polygon.exterior.xy
            ax.plot(x, y, color="#b9b9b9", linewidth=0.35)
    for feature in selected_features:
        geom = shape(feature["geometry"])
        for polygon in iter_polygons(geom):
            x, y = polygon.exterior.xy
            ax.fill(x, y, color="#f0b35e", alpha=0.35, linewidth=0)
    for polygon in iter_polygons(buffer_4326):
        x, y = polygon.exterior.xy
        ax.plot(x, y, color="#316c9f", linewidth=1.0)
    for polygon in iter_polygons(shape(murcia_feature["geometry"])):
        x, y = polygon.exterior.xy
        ax.fill(x, y, color="#a94a45", alpha=0.6, linewidth=0)
    ax.set_title("Reference: Murcia 50 km buffer intersections")
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(reference_dir / "murcia_50km_intersections_reference.png", dpi=170)
    plt.close(fig)

    return {
        "task_id": "gbx_port_murcia_50km_buffer_intersections",
        "total_features": len(raw["features"]),
        "cleaned_features": len(cleaned_features),
        "total_rings": total_rings,
        "dropped_degenerate_rings": dropped_rings,
        "features_with_dropped_rings": features_with_dropped_rings,
        "buffer_distance_m": 50000,
        "projected_crs": "EPSG:25830",
        "intersecting_province_count": len(intersecting),
        "intersecting_provinces": [row["name"] for row in intersecting],
        "observed_error": "ValueError: A linearring requires at least 4 coordinates.",
        "reference_files": [
            "reference/murcia_50km_intersecting_provinces_reference.csv",
            "reference/murcia_50km_intersecting_provinces_reference.json",
            "reference/murcia_50km_buffer_reference.geojson",
            "reference/murcia_50km_selected_provinces_reference.geojson",
            "reference/murcia_50km_intersections_reference.png",
        ],
    }


def main() -> int:
    summaries = [audit_forest_cover(), audit_co2_candidate_pool(), audit_murcia_buffer()]
    for run_dir, summary in zip([FOREST_RUN, CO2_RUN, BUFFER_RUN], summaries):
        write_json(run_dir / "audit_summary.json", summary)
    write_json(ROOT / "geonature_audit_summary.json", summaries)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
