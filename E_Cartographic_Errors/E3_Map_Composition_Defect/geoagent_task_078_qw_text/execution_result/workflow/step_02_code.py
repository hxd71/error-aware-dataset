import json
import geopandas as gpd
import rasterio

# Load inputs from runtime bindings
centroids_path = artifact_paths_by_name["building_centroids.shp"]
dem_path = asset_paths_by_id["psu_dem"]
output_path = output_paths[0]

# Read vector data
gdf = gpd.read_file(centroids_path)

# Sample DEM at point locations
with rasterio.open(dem_path) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)
    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    elevations = [float(vals[0]) for vals in src.sample(coords)]

# Handle nodata value 0.0
nodata_val = 0.0
gdf["elevation"] = [None if v == nodata_val else v for v in elevations]

# Write output
gdf.to_file(output_path)

print(json.dumps({"status": "success", "output": output_path, "count": len(gdf)}))