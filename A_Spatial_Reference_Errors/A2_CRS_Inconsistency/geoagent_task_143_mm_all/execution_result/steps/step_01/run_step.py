import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"country": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\12\\2\\input\\country.shp"}''')
current_step_assets_by_id = json.loads(r'''{"country": {"asset_id": "country", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\12\\2\\input\\country.shp", "role": "subject", "format": "shp", "crs": "EPSG:4326", "metadata": {"feature_count": 146, "columns": ["AREA"], "geometry_types": ["MultiPolygon", "Polygon"], "field_types": {"AREA": "float64"}, "sample_rows": [{"AREA": 1041.095}, {"AREA": 16004.784}, {"AREA": 212659.463}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-180.0, -90.0, 180.0, 83.59603881835938]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-143-geoagent_143-try01\\steps\\step_01\\country_3857.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-143-geoagent_143-try01\\steps\\step_01\\country_3857.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

from src.tools.vector_tools import reproject_vector
import json

input_path = "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\12\\2\\input\\country.shp"
output_path = "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-143-geoagent_143-try01\\steps\\step_01\\country_3857.shp"

summary = reproject_vector(
    input_vector=input_path,
    output_path=output_path,
    target_crs="EPSG:3857"
)

print(json.dumps({
    "step_id": "step_01",
    "operation": "reproject_vector",
    "input_crs": "EPSG:4326",
    "output_crs": "EPSG:3857",
    "output_path": output_path,
    "status": "success"
}))
