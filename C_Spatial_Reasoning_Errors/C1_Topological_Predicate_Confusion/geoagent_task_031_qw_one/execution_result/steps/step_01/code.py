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