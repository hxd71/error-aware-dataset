import geopandas as gpd
from shapely.ops import nearest_points
import json

centroid_path = artifact_paths_by_name["walmart_centroid.shp"]
buffer_path = artifact_paths_by_name["roads_300m_buffer.shp"]
roads_path = asset_paths_by_id["motorway_epsg32111"]
out_path = output_paths[0]

centroid_gdf = gpd.read_file(centroid_path)
buffer_gdf = gpd.read_file(buffer_path).to_crs(centroid_gdf.crs)
roads_gdf = gpd.read_file(roads_path).to_crs(centroid_gdf.crs)

centroid = centroid_gdf.iloc[0].geometry
buffer_geom = buffer_gdf.unary_union

if buffer_geom.covers(centroid):
    proposed = centroid
else:
    all_roads = roads_gdf.unary_union
    _, proposed = nearest_points(centroid, all_roads)

out_gdf = gpd.GeoDataFrame(geometry=[proposed], crs=centroid_gdf.crs)
out_gdf.to_file(out_path)

print(json.dumps({"status": "success", "output_path": out_path}))