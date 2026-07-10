import geopandas as gpd
from pathlib import Path
import json

# Step: Create centroid points from building footprint polygons
# Input: rolla_building_footprints (6909 building polygons)
# Output: building_centroids.shp with centroid points

# Use the runtime-provided path binding
input_path = asset_paths_by_id["rolla_building_footprints"]
output_path = output_paths[0]

# Read building footprint polygons
gdf = gpd.read_file(input_path)

# Define filtering rule: compute centroid geometry for each polygon
# Keep explicit reference to source field for join operations
keep_fields = ["bid", "ftprntid", "id", "fd_id", "st_damcat", "occtype", "bldgtype", "sqft", "num_story", "height"]
keep_fields = [f for f in keep_fields if f in gdf.columns]

# Create centroid GeoDataFrame preserving CRS from source
centroids_gdf = gpd.GeoDataFrame(
    gdf[keep_fields].copy(),
    geometry=gpd.points_from_xy(gdf.geometry.centroid.x, gdf.geometry.centroid.y),
    crs=gdf.crs
)

# Write filtered result (centroid points) to output path
centroids_gdf.to_file(output_path, driver="ESRI Shapefile")

# Verify centroid count matches expected
centroid_count = len(centroids_gdf)

# Print execution summary
print(json.dumps({
    "step_id": "step_02",
    "operation": "centroid_generation",
    "filter_rule": "polygon_to_point_centroid",
    "input_polygons": len(gdf),
    "output_points": centroid_count,
    "id_field_preserved": "bid and ftprntid",
    "output_path": str(output_path),
    "status": "success" if centroid_count == 6909 else "warning"
}))
