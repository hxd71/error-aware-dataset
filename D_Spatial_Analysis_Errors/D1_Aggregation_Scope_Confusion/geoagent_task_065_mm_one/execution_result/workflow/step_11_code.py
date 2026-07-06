import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
import json

# Define paths from runtime bindings
counties_path = asset_paths_by_id["pennsylvaniacounties"]
tri_path = artifact_paths_by_name["ruggedness_index.tif"]
output_path = output_paths[0]

# Load county polygons
counties_gdf = gpd.read_file(counties_path)

# Compute zonal statistics for TRI within each county
stats_list = zonal_stats(
    counties_gdf,
    tri_path,
    stats=['mean', 'min', 'max', 'std']
)

# Build output DataFrame with required columns
result_df = pd.DataFrame({
    'COUNTYFP': counties_gdf['COUNTYFP'],
    'mean_TRI': [s['mean'] for s in stats_list],
    'min_TRI': [s['min'] for s in stats_list],
    'max_TRI': [s['max'] for s in stats_list],
    'std_TRI': [s['std'] for s in stats_list]
})

# Export to CSV
result_df.to_csv(output_path, index=False)

# Print execution summary
print(json.dumps({
    'step_id': 'step_02',
    'status': 'success',
    'counties_processed': len(result_df),
    'output': output_path
}))
