from src.tools.vector_tools import spatial_join_vectors

# Perform spatial join: rainfall points within zone polygons
# Rainfall points (subject) joined with zone polygons (reference)
# predicate='within' ensures each rainfall point gets the index of its containing zone
summary = spatial_join_vectors(
    left_vector=asset_paths_by_id['rainfall'],
    right_vector=asset_paths_by_id['zone'],
    output_path=output_paths[0],
    predicate='within',
    target_crs=None
)

print(json.dumps({'step_id': 'step_01', 'operation': 'spatial_join', 'status': 'success', 'output': output_paths[0], 'summary': summary}))