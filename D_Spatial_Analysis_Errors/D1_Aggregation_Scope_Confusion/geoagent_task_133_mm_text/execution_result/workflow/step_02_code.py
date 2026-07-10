import geopandas as gpd
from pathlib import Path

# Load the joined rainfall zones data from previous step
input_path = current_step_artifacts_by_name["joined_rainfall_zones.shp"]["path"]
gdf = gpd.read_file(input_path)

print(f"CRS: {gdf.crs}")
print(f"Columns: {list(gdf.columns)}")
print(f"Feature count: {len(gdf)}")

# Detect the index column (case-insensitive lookup)
cols_lower = {c.lower(): c for c in gdf.columns}
index_col = cols_lower.get('index')
if index_col is None:
    raise ValueError(f"Index column not found in {list(gdf.columns)}")

print(f"Using index column: {index_col}")

# Group by index and export each zone as separate shapefile
output_count = 0
for zone_id, group in gdf.groupby(index_col):
    if output_count < len(output_paths):
        output_path = output_paths[output_count]
        group.to_file(output_path, driver='ESRI Shapefile')
        output_count += 1

print(f"Exported {output_count} zone shapefiles")

import json
print(json.dumps({"step_id": "step_02", "output_count": output_count, "status": "success"}))