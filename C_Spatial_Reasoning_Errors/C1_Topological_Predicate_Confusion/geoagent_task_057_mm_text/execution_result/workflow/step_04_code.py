from src.tools.vector_tools import intersect_vectors
import json

# Clip raw Thiessen polygons with bounding rectangle to produce rectangular polygon shapes
summary = intersect_vectors(
    left_vector="[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260420T112719Z-2446843a-057-geoagent_057-try01\\steps\\step_02\\thiessen_polygons_raw.shp",
    right_vector="[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260420T112719Z-2446843a-057-geoagent_057-try01\\steps\\step_01\\bounding_rectangle.shp",
    output_path="[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260420T112719Z-2446843a-057-geoagent_057-try01\\steps\\step_03\\thiessen_polygons_clipped.shp"
)

print(json.dumps({
    "step_id": "step_03",
    "operation": "intersect_vectors",
    "status": "success",
    "output_features": summary.get("feature_count", 0),
    "output_path": summary.get("output_path", "")
}))