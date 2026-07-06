import json
import geopandas as gpd
from shapely.geometry import Point

# Load the CSV table
csv_path = asset_paths_by_id["hiv"]
df = gpd.read_file(csv_path)

# Create Point geometries from X (longitude) and Y (latitude) columns
geometry = [Point(xy) for xy in zip(df["X"], df["Y"])]

# Create GeoDataFrame with point geometries
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Write to shapefile using the provided output path
output_path = output_paths[0]
gdf.to_file(output_path, driver="ESRI Shapefile")

# Print execution summary
summary = {
    "step_id": "step_01",
    "status": "success",
    "output": output_path,
    "feature_count": len(gdf),
    "crs": "EPSG:4326",
    "columns": list(gdf.columns)
}
print(json.dumps(summary))