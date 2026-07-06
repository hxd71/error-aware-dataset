from src.tools.vector_tools import spatial_join_vectors
import json

# Perform spatial join: damaged house points (subject) within SAF Special Study Zone polygons (reference)
# Both datasets use EPSG:26710, so no target_crs transformation needed
subject_path = asset_paths_by_id["damagedhouses"]
reference_path = asset_paths_by_id["saf_specialstudyzone"]
output_path = output_paths[0]

summary = spatial_join_vectors(
    left_vector=subject_path,
    right_vector=reference_path,
    output_path=output_path,
    predicate="within"
)

print(json.dumps({
    "step_id": "step_01",
    "operation": "spatial_join_vectors",
    "predicate": "within",
    "subject": "damagedhouses (points)",
    "reference": "saf_specialstudyzone (polygons)",
    "result_features": summary.get("feature_count", 0),
    "output": output_path
}))
