from pathlib import Path

import geopandas as gpd
import pandas as pd


TASK_ROOT = Path(__file__).resolve().parents[2]
INPUT_POINTS = TASK_ROOT / "data_source" / "input_01" / "street_image.shp"
ARTIFACT_DIR = TASK_ROOT / "execution_result" / "artifacts"
WRONG_OUTPUT = ARTIFACT_DIR / "year_equal_interval.geojson"
REFERENCE_OUTPUT = ARTIFACT_DIR / "year_unique_categories.geojson"


def main():
    points = gpd.read_file(INPUT_POINTS).to_crs("EPSG:4326")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    points["year"] = points["image_date"].astype(str).str.extract(r"(\d{4})")[0].astype("Int64")

    wrong = points.copy()
    year = wrong["year"].astype(float)
    wrong["wrong_class"] = pd.cut(year, bins=5).astype(str)
    wrong.to_file(WRONG_OUTPUT, driver="GeoJSON")

    reference = points.copy()
    reference.to_file(REFERENCE_OUTPUT, driver="GeoJSON")

    print(f"year_count={points['year'].nunique(dropna=True)}")
    print(f"wrong_class_count={wrong['wrong_class'].nunique(dropna=True)}")


if __name__ == "__main__":
    main()
