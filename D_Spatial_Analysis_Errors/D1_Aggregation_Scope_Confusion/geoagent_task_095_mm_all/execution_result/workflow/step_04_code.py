import json
from src.tools.vector_tools import spatial_join_vectors

# Perform spatial join: find weather stations within county polygons
# Subject (reference) dataset: sc_weatherstations (points with NAME, ID) -> should be left for output geometry
# Reference (subject) dataset: sc_county_boundaries (polygons with NAME, GEOID) -> container
# Predicate: within

stations_path = asset_paths_by_id["sc_weatherstations"]
counties_path = asset_paths_by_id["sc_county_boundaries"]
output_path = output_paths[0]

# Execute spatial join with 'within' predicate
# Stations on left so point geometry is preserved; counties on right as the container
summary = spatial_join_vectors(
    left_vector=stations_path,
    right_vector=counties_path,
    output_path=output_path,
    predicate="within"
)

# Print execution summary
print(json.dumps({
    "step_id": "step_01",
    "operation": "spatial_join_vectors",
    "predicate": "within",
    "left": "sc_weatherstations",
    "right": "sc_county_boundaries",
    "output_features": summary.get("feature_count", 0),
    "output_path": output_path
}, indent=2))
