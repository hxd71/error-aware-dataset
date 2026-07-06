import json
from src.tools.vector_tools import buffer_vector

input_path = current_step_assets_by_id["new_york_coffee_shops_epsg6535"]["path"]
output_path = output_paths[0]

buffer_vector(
    input_path,
    output_path=output_path,
    distance=600.0
)

print(json.dumps({"status": "success", "output_path": output_path}))