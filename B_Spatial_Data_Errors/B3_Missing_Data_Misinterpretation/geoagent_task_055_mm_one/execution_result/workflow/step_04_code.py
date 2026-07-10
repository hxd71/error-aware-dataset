import json
import numpy as np
import rasterio
from rasterio.features import shapes as raster_shapes
import geopandas as gpd
from shapely.geometry import shape
from src.tools.raster_tools import threshold_raster

# Step 1: Create binary mask using threshold_raster
# Valid pixels have data (not nodata), so threshold on being finite
# threshold=0 with comparison='>' creates 1 for any finite value, 0 for nodata
result = threshold_raster(
    asset_paths_by_id["elevation_mask_nodata"],
    output_path=output_paths[0],
    threshold=0,
    comparison='>',
    true_value=1,
    false_value=0,
    nodata=0
)

# Step 2: Polygonize the binary raster to vector
with rasterio.open(output_paths[0]) as src:
    binary_data = src.read(1)
    crs = src.crs
    transform = src.transform

# Extract polygons where value == 1 (valid pixels)
geometries = []
for geom, val in raster_shapes(binary_data, transform=transform):
    if val == 1:
        geometries.append(shape(geom))

# Create GeoDataFrame with proper CRS
gdf = gpd.GeoDataFrame(geometry=geometries, crs=crs)

# Write to GeoJSON
gdf.to_file(output_paths[1], driver="GeoJSON")

# Execution summary
summary = {
    "step_id": "step_01",
    "status": "success",
    "outputs": {
        "binary_mask": output_paths[0],
        "vector_polygons": output_paths[1]
    },
    "polygon_count": len(gdf),
    "crs": str(crs)
}
print(json.dumps(summary))