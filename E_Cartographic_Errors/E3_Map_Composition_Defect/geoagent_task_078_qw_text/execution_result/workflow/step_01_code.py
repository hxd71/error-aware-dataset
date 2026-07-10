import geopandas as gpd
import json

input_path = current_step_assets_by_id["penn_state_buildings"]["path"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)
gdf = gdf.to_crs("EPSG:4326")
gdf["geometry"] = gdf.geometry.centroid
gdf.to_file(output_path, driver="ESRI Shapefile")

print(json.dumps({"status": "success", "output": output_path, "features": len(gdf)}))