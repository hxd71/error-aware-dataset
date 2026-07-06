from src.tools.vector_tools import join_nearest_features
import json

# Ground truth points as source; estimated points as target
# Both datasets are in EPSG:6569 (projected meters)
gt_path = asset_paths_by_id["trunk_location_ground_truth_epsg6569"]
est_path = asset_paths_by_id["trunk_location_estimated_epsg6569"]
output_path = output_paths[0]

summary = join_nearest_features(
    source_vector=gt_path,
    target_vector=est_path,
    output_path=output_path,
    distance_column="distance_to_nearest",
    target_prefix="nearest_",
    target_crs="EPSG:6569"
)

print(json.dumps({
    "step_id": "step_01",
    "output_paths": output_paths,
    "features_written": summary.get("features_written", 0),
    "distance_units": "meters (EPSG:6569 projected)"
}))
