import geopandas as gpd
import rasterio
import rasterstats
import json

# Input paths from artifacts
centroids_path = artifact_paths_by_name["building_centroids.shp"]
slope_path = artifact_paths_by_name["slope_rolla.tif"]
output_path = output_paths[0]

# Load building centroids
centroids = gpd.read_file(centroids_path)
print(f"Loaded {len(centroids)} building centroids")

# Sample slope values at each centroid using rasterstats point_query
slope_values = rasterstats.point_query(
    centroids,
    slope_path,
    nodata=-9999
)

# Add slope values as new column
centroids["slope"] = slope_values

# Write output vector with slope field
centroids.to_file(output_path)
print(f"Wrote {len(centroids)} features to {output_path}")

# Print execution summary
summary = {
    "step_id": "step_03",
    "operation": "point_in_raster_sampling",
    "input_features": len(centroids),
    "output_path": output_path,
    "new_fields": ["slope"]
}
print(json.dumps(summary))