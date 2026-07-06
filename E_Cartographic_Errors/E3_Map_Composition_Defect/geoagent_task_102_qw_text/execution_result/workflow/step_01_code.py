import json
import geopandas as gpd
from shapely.geometry import Point

input_path = current_step_assets_by_id["walmart_4_site_epsg32111"]["path"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)
mean_x = gdf.geometry.x.mean()
mean_y = gdf.geometry.y.mean()

centroid_gdf = gpd.GeoDataFrame(
    {"id": ["centroid"]},
    geometry=[Point(mean_x, mean_y)],
    crs=gdf.crs
)

centroid_gdf.to_file(output_path)

print(json.dumps({"status": "success", "centroid": [mean_x, mean_y], "output": output_path}))