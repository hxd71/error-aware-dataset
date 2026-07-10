import geopandas as gpd
import json
from pathlib import Path

input_path = asset_paths_by_id["columbia_roads"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

def extract_highway(tag_str):
    try:
        d = json.loads(tag_str.replace("'", '"'))
        return d.get("highway")
    except (json.JSONDecodeError, AttributeError):
        return None

gdf["_highway"] = gdf["tags"].apply(extract_highway)
filtered_gdf = gdf[gdf["_highway"] == "residential"].drop(columns=["_highway"]).copy()

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
filtered_gdf.to_file(output_path)

print(json.dumps({
    "step": "step_01",
    "status": "success",
    "input_features": int(len(gdf)),
    "output_features": int(len(filtered_gdf)),
    "output_path": output_path
}))