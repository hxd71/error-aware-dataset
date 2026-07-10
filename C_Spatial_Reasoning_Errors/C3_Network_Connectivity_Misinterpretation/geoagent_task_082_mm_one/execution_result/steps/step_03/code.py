import geopandas as gpd
import json

# Read the GeoJSON line features from prior step artifact
input_path = artifact_paths_by_name["street_paths.geojson"]
gdf = gpd.read_file(input_path)

# Ensure CRS is EPSG:4326 (maintain original coordinate reference system)
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
elif gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")

# Write to ESRI shapefile format
output_path = output_paths[0]
gdf.to_file(output_path, driver="ESRI Shapefile")

# Print execution summary
summary = {
    "step_id": "step_03",
    "output_features": int(len(gdf)),
    "geometry_types": list(gdf.geometry.geom_type.unique()),
    "crs": str(gdf.crs),
    "output_path": output_path
}
print(json.dumps(summary))