import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"street_image": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_view_image\\street_image\\street_image.shp"}''')
current_step_assets_by_id = json.loads(r'''{}''')
artifact_paths_by_name = json.loads(r'''{"pano_graph.json": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_01\\pano_graph.json", "street_paths.geojson": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_02\\street_paths.geojson"}''')
current_step_artifacts_by_name = json.loads(r'''{"street_paths.geojson": {"name": "street_paths.geojson", "path": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_02\\street_paths.geojson", "artifact_type": "vector", "description": ""}}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_03\\street_paths.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_03\\street_paths.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

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