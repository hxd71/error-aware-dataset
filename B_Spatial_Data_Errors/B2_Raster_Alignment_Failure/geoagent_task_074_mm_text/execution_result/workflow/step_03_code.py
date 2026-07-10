import geopandas as gpd
from rasterio.transform import from_bounds
from rasterio.features import rasterize
import rasterio
import numpy as np
from pathlib import Path

# Paths from runtime bindings
vector_path = asset_paths_by_id["sanfrancisco_tracts_central"]
output_path = output_paths[0]

# Read the vector shapefile
print(f"Reading vector shapefile: {vector_path}")
gdf = gpd.read_file(vector_path)
print(f"Loaded {len(gdf)} census tract features")

# Get extent bounds [minx, miny, maxx, maxy]
bounds = gdf.total_bounds
print(f"Extent: {bounds}")

# Calculate raster dimensions for 100m resolution
resolution = 100
width = int((bounds[2] - bounds[0]) / resolution)
height = int((bounds[3] - bounds[1]) / resolution)
print(f"Raster dimensions: {width} x {height} at {resolution}m resolution")

# Create affine transform from bounds
transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)

# Initialize output array with 0 (background)
out_data = np.zeros((height, width), dtype=np.uint8)

# Rasterize polygons - burn value 1 for tract areas
shapes = [(geom, 1) for geom in gdf.geometry]
rasterized = rasterize(shapes, out_shape=(height, width), transform=transform, dtype=np.uint8)
out_data[:] = rasterized

# Write output raster
crs = gdf.crs
print(f"Writing binary mask to: {output_path}")

with rasterio.open(
    output_path,
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=np.uint8,
    crs=crs,
    transform=transform,
    nodata=255
) as dst:
    dst.write(out_data, 1)

print(f"Successfully wrote tracts_mask_100m.tif ({width*height} pixels)")
print(json.dumps({"step_id": "step_01", "status": "success", "output": output_path, "pixels_written": int(out_data.sum())}))