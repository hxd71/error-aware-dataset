from src.tools.vector_tools import minimum_bounding_geometry
import json

# Create bounding rectangle from all point features
# Use runtime binding for input path to avoid invalid escape sequences
input_path = asset_paths_by_id["richland_sc_fastfood"]
output_path = output_paths[0]

summary = minimum_bounding_geometry(
    input_vector=input_path,
    output_path=output_path,
    geometry_type="rectangle"
)

print(json.dumps({
    "step_id": "step_01",
    "operation": "minimum_bounding_geometry",
    "geometry_type": "rectangle",
    "input_features": 263,
    "output_features": summary.get("feature_count", 1),
    "status": "success"
}))