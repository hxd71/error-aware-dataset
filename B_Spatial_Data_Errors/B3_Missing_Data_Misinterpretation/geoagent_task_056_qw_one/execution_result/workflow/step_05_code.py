import json
from src.tools.raster_tools import polygonize_raster

input_raster = artifact_paths_by_name["zero_mask.tif"]
output_vector = output_paths[0]

polygonize_raster(
    input_raster,
    output_path=output_vector,
    band=1,
    foreground_values=[0]
)

print(json.dumps({"step": "step_02", "status": "completed", "output": output_vector}))