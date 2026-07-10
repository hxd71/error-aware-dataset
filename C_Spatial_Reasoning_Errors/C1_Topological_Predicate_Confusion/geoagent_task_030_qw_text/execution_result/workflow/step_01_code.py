import json
from src.tools.vector_tools import filter_vector_by_spatial_relationship

input_vec = current_step_assets_by_id["pacounties"]["path"]
filter_vec = current_step_assets_by_id["generated_polygon"]["path"]
output_path = output_paths[0]

filter_vector_by_spatial_relationship(
    input_vector=input_vec,
    filter_vector=filter_vec,
    output_path=output_path,
    predicate="intersects"
)

print(json.dumps({"step_id": "step_01", "status": "success", "output_path": output_path}))