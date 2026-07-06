from src.tools.raster_tools import terrain_derivative
import json

dem_path = asset_paths_by_id["pa_dem"]
output_path = output_paths[0]

summary = terrain_derivative(
    dem_path,
    output_path=output_path,
    derivative="tri",
    band=1,
    nodata=0.0
)

print(json.dumps({
    "step_id": "step_01",
    "output_paths": [output_path],
    "summary": summary
}))