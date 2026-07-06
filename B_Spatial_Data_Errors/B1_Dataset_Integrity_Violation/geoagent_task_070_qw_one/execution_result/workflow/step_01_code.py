import json
from src.tools.vector_tools import reproject_vector

input_path = asset_paths_by_id["nigeria_major_roads"]
output_path = output_paths[0]
target_crs = "EPSG:26392"

reproject_vector(input_path, output_path=output_path, target_crs=target_crs)

print(json.dumps({"status": "success", "output": output_path, "target_crs": target_crs}))