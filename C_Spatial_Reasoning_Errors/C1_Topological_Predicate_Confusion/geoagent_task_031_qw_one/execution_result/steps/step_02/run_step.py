import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"generated_polygon": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\generated_polygon\\generated_polygon.shp", "pacounties": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp"}''')
current_step_assets_by_id = json.loads(r'''{"pacounties": {"asset_id": "pacounties", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp", "role": "reference", "format": "shp", "crs": "EPSG:4269", "metadata": {"feature_count": 67, "columns": ["STATEFP", "COUNTYFP", "COUNTYNS", "AFFGEOID", "GEOID", "NAME", "NAMELSAD", "STUSPS", "STATE_NAME", "LSAD", "ALAND", "AWATER"], "geometry_types": ["MultiPolygon", "Polygon"], "field_types": {"STATEFP": "str", "COUNTYFP": "str", "COUNTYNS": "str", "AFFGEOID": "str", "GEOID": "str", "NAME": "str", "NAMELSAD": "str", "STUSPS": "str", "STATE_NAME": "str", "LSAD": "str", "ALAND": "int64", "AWATER": "int64"}, "sample_rows": [{"STATEFP": "42", "COUNTYFP": "129", "COUNTYNS": "01209191", "AFFGEOID": "0500000US42129", "GEOID": "42129", "NAME": "Westmoreland", "NAMELSAD": "Westmoreland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2661762744, "AWATER": 21294228}, {"STATEFP": "42", "COUNTYFP": "111", "COUNTYNS": "01209188", "AFFGEOID": "0500000US42111", "GEOID": "42111", "NAME": "Somerset", "NAMELSAD": "Somerset County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2784357763, "AWATER": 17118618}, {"STATEFP": "42", "COUNTYFP": "097", "COUNTYNS": "01209186", "AFFGEOID": "0500000US42097", "GEOID": "42097", "NAME": "Northumberland", "NAMELSAD": "Northumberland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 1185344304, "AWATER": 50674892}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-80.519891, 39.7198, -74.689516, 42.26986]}}}''')
artifact_paths_by_name = json.loads(r'''{"generated_polygon_diff.shp": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_01\\generated_polygon_diff.shp"}''')
current_step_artifacts_by_name = json.loads(r'''{"generated_polygon_diff.shp": {"name": "generated_polygon_diff.shp", "path": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_01\\generated_polygon_diff.shp", "artifact_type": "vector", "description": ""}}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_02\\merged_polygon.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_02\\merged_polygon.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import geopandas as gpd
import pandas as pd
import json

diff_path = artifact_paths_by_name["generated_polygon_diff.shp"]
counties_path = asset_paths_by_id["pacounties"]
output_path = output_paths[0]

gdf_diff = gpd.read_file(diff_path)
gdf_counties = gpd.read_file(counties_path)

merged_df = pd.concat([gdf_diff, gdf_counties], ignore_index=True)
merged_gdf = gpd.GeoDataFrame(merged_df, geometry="geometry")
merged_gdf.crs = "EPSG:4269"

merged_gdf.to_file(output_path)

print(json.dumps({"status": "success", "output": output_path, "feature_count": len(merged_gdf)}))