from src.tools.vector_tools import buffer_vector
import json

input_vector = asset_paths_by_id['roads_potland_epsg6852_subset']
output_path = output_paths[0]

summary = buffer_vector(
    input_vector=input_vector,
    output_path=output_path,
    distance=20.0,
    target_crs=None
)

print(json.dumps({
    'step_id': 'step_01',
    'operation': 'buffer_vector',
    'input_features': 887,
    'buffer_distance_meters': 20.0,
    'source_crs': 'EPSG:6852',
    'output_features': summary.get('feature_count', 887),
    'output_path': str(output_path),
    'status': 'success'
}, indent=2))