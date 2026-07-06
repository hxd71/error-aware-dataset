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
