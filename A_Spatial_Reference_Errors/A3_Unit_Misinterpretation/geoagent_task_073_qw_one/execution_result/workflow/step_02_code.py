import json
import geopandas as gpd

input_path = asset_paths_by_id["us_counties"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

# Reproject to EPSG:3857 for accurate geometric centroid calculation, then back to EPSG:4326
centroids = gdf.geometry.to_crs("EPSG:3857").centroid.to_crs("EPSG:4326")
gdf["centroid_x"] = centroids.x
gdf["centroid_y"] = centroids.y

# Drop geometry column for CSV export
gdf = gdf.drop(columns=["geometry"])

# Write to CSV
gdf.to_csv(output_path, index=False)

print(json.dumps({"status": "success", "records_written": len(gdf), "output_path": output_path}))