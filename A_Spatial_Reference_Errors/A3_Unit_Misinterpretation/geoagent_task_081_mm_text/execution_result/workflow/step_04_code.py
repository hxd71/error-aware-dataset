import geopandas as gpd
import pandas as pd
import json

# Read the nearest estimated-to-GT matching results
gdf = gpd.read_file(artifact_paths_by_name["nearest_estimated_to_gt.geojson"])

# Print actual columns for debugging
print(f"Available columns: {list(gdf.columns)}")

# Identify the distance column - include actual column names from error feedback
distance_candidates = ['distance', 'dist', 'h_distance', 'error', 'error_m', 'distance_m', 'nearest_distance', 'distance_to_nearest']
dist_col = None
for col in distance_candidates:
    if col in gdf.columns:
        dist_col = col
        print(f"Using distance column: {dist_col}")
        break

if dist_col is None:
    raise ValueError(f"No recognized distance column found. Available: {list(gdf.columns)}")

# Filter: distance <= 3.0 meters
filtered_gdf = gdf[gdf[dist_col] <= 3.0].copy()

# Output 1: filtered GeoJSON of GT points with matched estimated locations within 3m
filtered_gdf.to_file(output_paths[0], driver="GeoJSON")

# Compute summary statistics
matched_count = int(len(filtered_gdf))
avg_error = float(filtered_gdf[dist_col].mean()) if matched_count > 0 else 0.0

# Output 2: CSV summary with count and average_error_meters
summary_df = pd.DataFrame([{
    "matched_gt_count": matched_count,
    "average_error_meters": round(avg_error, 4)
}])
summary_df.to_csv(output_paths[1], index=False)

# Execution summary
print(json.dumps({
    "step_id": "step_02",
    "distance_column_used": dist_col,
    "matched_gt_count": matched_count,
    "average_error_meters": round(avg_error, 4),
    "outputs_written": [str(output_paths[0]), str(output_paths[1])]
}))