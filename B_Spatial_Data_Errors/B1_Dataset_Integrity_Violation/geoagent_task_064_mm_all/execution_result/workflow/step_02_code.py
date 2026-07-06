import geopandas as gpd
import json

# Input path from runtime bindings
input_path = asset_paths_by_id["roads"]

# Output path from runtime bindings
output_path = output_paths[0]

# Target CRS for reprojection (NAD27 / UTM zone 10N)
target_crs = "EPSG:26710"

# Read the source vector data (EPSG:4326)
roads_gdf = gpd.read_file(input_path)

# Reproject to target CRS
roads_reprojected = roads_gdf.to_crs(target_crs)

# Write the reprojected output to declared filename
roads_reprojected.to_file(output_path)

# Print execution summary
summary = {
    "step_id": "step_01",
    "operation": "reproject",
    "input_crs": "EPSG:4326",
    "output_crs": target_crs,
    "feature_count": len(roads_reprojected),
    "output_path": output_path
}
print(json.dumps(summary))