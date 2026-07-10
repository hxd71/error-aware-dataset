import json
import geopandas as gpd
import pandas as pd

input_path = artifact_paths_by_name["pa_counties_point_counts.shp"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

# Identify the point count column dynamically to handle naming variations from step_01
count_col = next((c for c in gdf.columns if "count" in c.lower()), "point_count")

# Convert the count column to numeric to avoid TypeError during comparison
gdf[count_col] = pd.to_numeric(gdf[count_col], errors='coerce')

# Apply explicit predicate: count < 10
filtered_gdf = gdf[gdf[count_col] < 10].copy()
filtered_gdf.to_file(output_path, driver="ESRI Shapefile")

print(json.dumps({
    "step": "step_02",
    "status": "success",
    "input": input_path,
    "output": output_path,
    "filter_rule": f"{count_col} < 10",
    "features_kept": int(len(filtered_gdf))
}))