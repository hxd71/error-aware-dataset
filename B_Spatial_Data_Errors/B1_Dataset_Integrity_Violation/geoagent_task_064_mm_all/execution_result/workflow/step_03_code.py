from src.tools.vector_tools import add_geometry_fields
import json

# Use the full path from the artifact catalog
input_path = artifact_paths_by_name["roads_nad27_utm10.shp"]

# Add a 'Length' field containing the geometric length of each feature
# The roads layer is already in UTM (meter-based) projection from step_01
summary = add_geometry_fields(
    input_path,
    output_path="roads_with_length.shp",
    length_field="Length"
)

print(json.dumps({"step_id": "step_02", "status": "success", "output": summary}))