import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"generated_polygon": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\generated_polygon\\generated_polygon.shp", "pacounties": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp"}''')
current_step_assets_by_id = json.loads(r'''{"generated_polygon": {"asset_id": "generated_polygon", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\generated_polygon\\generated_polygon.shp", "role": "subject", "format": "shp", "crs": "EPSG:4269", "metadata": {"feature_count": 1, "columns": ["id"], "geometry_types": ["Polygon"], "field_types": {"id": "int64"}, "sample_rows": [{"id": 1}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-79.04459441641437, 41.68838747148277, -78.25545675967948, 42.50639601809821]}}, "pacounties": {"asset_id": "pacounties", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp", "role": "reference", "format": "shp", "crs": "EPSG:4269", "metadata": {"feature_count": 67, "columns": ["STATEFP", "COUNTYFP", "COUNTYNS", "AFFGEOID", "GEOID", "NAME", "NAMELSAD", "STUSPS", "STATE_NAME", "LSAD", "ALAND", "AWATER"], "geometry_types": ["MultiPolygon", "Polygon"], "field_types": {"STATEFP": "str", "COUNTYFP": "str", "COUNTYNS": "str", "AFFGEOID": "str", "GEOID": "str", "NAME": "str", "NAMELSAD": "str", "STUSPS": "str", "STATE_NAME": "str", "LSAD": "str", "ALAND": "int64", "AWATER": "int64"}, "sample_rows": [{"STATEFP": "42", "COUNTYFP": "129", "COUNTYNS": "01209191", "AFFGEOID": "0500000US42129", "GEOID": "42129", "NAME": "Westmoreland", "NAMELSAD": "Westmoreland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2661762744, "AWATER": 21294228}, {"STATEFP": "42", "COUNTYFP": "111", "COUNTYNS": "01209188", "AFFGEOID": "0500000US42111", "GEOID": "42111", "NAME": "Somerset", "NAMELSAD": "Somerset County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2784357763, "AWATER": 17118618}, {"STATEFP": "42", "COUNTYFP": "097", "COUNTYNS": "01209186", "AFFGEOID": "0500000US42097", "GEOID": "42097", "NAME": "Northumberland", "NAMELSAD": "Northumberland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 1185344304, "AWATER": 50674892}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-80.519891, 39.7198, -74.689516, 42.26986]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_01\\generated_polygon_diff.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-6344b54d-031-geoagent_031-try01\\steps\\step_01\\generated_polygon_diff.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import json
from src.tools.vector_tools import filter_vector_by_spatial_relationship

subject_path = current_step_assets_by_id["generated_polygon"]["path"]
reference_path = current_step_assets_by_id["pacounties"]["path"]
out_path = output_paths[0]

# Explicit spatial predicate: retain features from generated_polygon that are disjoint from pacounties (erase overlap)
result = filter_vector_by_spatial_relationship(
    subject_path,
    reference_path,
    output_path=out_path,
    predicate="disjoint"
)

print(json.dumps({"step_id": "step_01", "status": "success", "output_path": out_path}))