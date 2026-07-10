import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"pacounties": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp", "pa_data_epsg4326": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PA_Data_EPSG4326\\PA_Data_EPSG4326.shp"}''')
current_step_assets_by_id = json.loads(r'''{}''')
artifact_paths_by_name = json.loads(r'''{"pa_counties_point_counts.shp": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_01\\pa_counties_point_counts.shp"}''')
current_step_artifacts_by_name = json.loads(r'''{"pa_counties_point_counts.shp": {"name": "pa_counties_point_counts.shp", "path": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_01\\pa_counties_point_counts.shp", "artifact_type": "vector", "description": ""}}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_02\\pa_counties_filtered_lt10.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_02\\pa_counties_filtered_lt10.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

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