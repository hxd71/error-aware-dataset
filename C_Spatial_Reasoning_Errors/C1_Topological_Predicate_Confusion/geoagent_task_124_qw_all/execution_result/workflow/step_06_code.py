import json
from src.tools.vector_tools import spatial_join_vectors

overlap_path = artifact_paths_by_name["overlap_areas.shp"]
circles_path = asset_paths_by_id["circles"]
output_path = output_paths[0]

summary = spatial_join_vectors(
    left_vector=overlap_path,
    right_vector=circles_path,
    output_path=output_path,
    predicate="intersects"
)

print(json.dumps({"step": "step_02", "status": "completed", "output": output_path}))