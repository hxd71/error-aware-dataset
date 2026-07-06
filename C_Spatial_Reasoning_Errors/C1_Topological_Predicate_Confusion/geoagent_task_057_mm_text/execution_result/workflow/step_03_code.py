from pathlib import Path
import geopandas as gpd
import numpy as np
import geovoronoi
from src.tools.vector_tools import create_voronoi_polygons

# Input point dataset
input_path = asset_paths_by_id["richland_sc_fastfood"]
output_path = output_paths[0]

# Load points and verify geometry
points_gdf = gpd.read_file(input_path)
print(f"Loaded {len(points_gdf)} point features from {input_path}")
print(f"Source CRS: {points_gdf.crs}")
print(f"Geometry type: {points_gdf.geom_type.unique()}")

# Generate Voronoi polygons from points
# create_voronoi_polygons handles the tessellation internally
summary = create_voronoi_polygons(
    input_path,
    output_path=output_path
)

print(f"Voronoi polygon generation complete: {summary}")

# Verify output
result_gdf = gpd.read_file(output_path)
print(f"Output contains {len(result_gdf)} polygon features")
print(f"Output CRS: {result_gdf.crs}")
print(f"Output geometry type: {result_gdf.geom_type.unique()}")

execution_summary = {
    "step_id": "step_02",
    "operation": "create_voronoi_polygons",
    "input_features": len(points_gdf),
    "output_features": len(result_gdf),
    "output_crs": str(result_gdf.crs),
    "output_path": output_path
}
print(json.dumps(execution_summary, indent=2))