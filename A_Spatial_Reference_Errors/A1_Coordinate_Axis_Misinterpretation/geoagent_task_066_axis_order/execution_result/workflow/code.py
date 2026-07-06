from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


TASK_ROOT = Path(__file__).resolve().parents[2]
INPUT_POINTS = TASK_ROOT / "data_source" / "input_01" / "PA_Fastfoods.shp"
ARTIFACT_DIR = TASK_ROOT / "execution_result" / "artifacts"
WRONG_OUTPUT = ARTIFACT_DIR / "axis_swapped.geojson"
REFERENCE_OUTPUT = ARTIFACT_DIR / "axis_correct.geojson"


def main():
    fastfoods = gpd.read_file(INPUT_POINTS).to_crs("EPSG:4326")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    reference = fastfoods.copy()
    reference.to_file(REFERENCE_OUTPUT, driver="GeoJSON")

    wrong_geometries = [
        Point(point.y, point.x) if point is not None and not point.is_empty else point
        for point in fastfoods.geometry
    ]
    swapped = fastfoods.copy()
    swapped = gpd.GeoDataFrame(swapped.drop(columns="geometry"), geometry=wrong_geometries, crs="EPSG:4326")
    swapped.to_file(WRONG_OUTPUT, driver="GeoJSON")

    print(f"feature_count={len(swapped)}")
    print(f"source_bounds={list(reference.total_bounds)}")
    print(f"axis_swapped_bounds={list(swapped.total_bounds)}")


if __name__ == "__main__":
    main()
