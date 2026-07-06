import json
from src.tools.vector_tools import buffer_vector

input_path = asset_paths_by_id["motorway_epsg32111"]
output_path = output_paths[0]

result = buffer_vector(
    input_path,
    output_path=output_path,
    distance=300.0,
    target_crs="EPSG:32111"
)

print(json.dumps({"step": "step_02", "status": "success", "output": output_path}))