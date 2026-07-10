import json
from src.tools.raster_tools import raster_calculator

red_path = asset_paths_by_id["lc08_l1tp_190055_20200214_20200823_02_t1_b4"]
nir_path = asset_paths_by_id["lc08_l1tp_190055_20200214_20200823_02_t1_b5"]
output_path = output_paths[0]

raster_calculator(
    input_rasters={"red": red_path, "nir": nir_path},
    output_path=output_path,
    expression="(nir - red) / (nir + red)",
    nodata=0.0,
    dtype="float32"
)

print(json.dumps({"step": "step_01", "status": "completed", "output": output_path}))