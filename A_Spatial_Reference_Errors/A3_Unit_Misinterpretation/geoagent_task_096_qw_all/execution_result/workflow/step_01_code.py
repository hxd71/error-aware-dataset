import json
import geopandas as gpd
from pathlib import Path

input_path = asset_paths_by_id["level3_30"]
output_path = output_paths[0]

Path(output_path).parent.mkdir(parents=True, exist_ok=True)

gdf = gpd.read_file(input_path)
threshold_m = 0.0635
filtered_gdf = gdf[gdf["Rain"] > threshold_m].copy()
filtered_gdf.to_file(output_path, driver="ESRI Shapefile")

print(json.dumps({
    "step_id": "step_01",
    "input_count": len(gdf),
    "output_count": len(filtered_gdf),
    "threshold_m": threshold_m,
    "output_path": output_path
}))