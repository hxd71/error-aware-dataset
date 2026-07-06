import geopandas as gpd
import json

# Read the clipped Thiessen polygons (no filtering needed - preserve all polygons)
src_path = artifact_paths_by_name["thiessen_polygons_clipped.shp"]
dst_path = output_paths[0]

gdf = gpd.read_file(src_path)
gdf.to_file(dst_path)

summary = {
    "step_id": "step_04",
    "status": "success",
    "output_count": len(gdf),
    "geometry_types": list(gdf.geometry.geom_type.unique()),
    "output_path": str(dst_path)
}
print(json.dumps(summary))