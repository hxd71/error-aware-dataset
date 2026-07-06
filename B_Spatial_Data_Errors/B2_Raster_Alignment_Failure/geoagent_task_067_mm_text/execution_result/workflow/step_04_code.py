import json
import numpy as np
import rasterio
from pathlib import Path

# Input: merged DEM from step_01
input_dem_path = artifact_paths_by_name["merged_dem_richland.tif"]
output_aspect_path = output_paths[0]

# Read the DEM
with rasterio.open(input_dem_path) as dem_src:
    dem = dem_src.read(1)
    transform = dem_src.transform
    crs = dem_src.crs
    nodata = dem_src.nodata
    res = dem_src.res[0]

# Convert to float for gradient calculation
dem_float = dem.astype(np.float64)
if nodata is not None:
    dem_float[dem_float == nodata] = np.nan

# Compute gradients using finite differences
# gradient returns (dy, dx) where dx is gradient in column direction (east positive)
# dy is gradient in row direction (south positive)
dy, dx = np.gradient(dem_float, res)

# Compute aspect: compass direction of steepest downhill slope
# atan2 returns radians from -pi to pi; flip dx sign because positive x (east) should give west aspect
aspect_rad = np.arctan2(-dx, -dy)

# Convert to degrees 0-360, with 0=North, 90=East, 180=South, 270=West
aspect_deg = np.degrees(aspect_rad)
aspect_deg = (aspect_deg + 360) % 360

# Handle nodata: set to -1 to indicate flat/undefined areas
nodata_aspect = -1.0
valid_mask = np.isfinite(dem_float)
if not valid_mask.all():
    aspect_deg[~valid_mask] = nodata_aspect

# Convert to float32 for output
aspect_output = aspect_deg.astype(np.float32)

# Write output aspect raster
with rasterio.open(
    output_aspect_path,
    'w',
    driver='GTiff',
    height=aspect_output.shape[0],
    width=aspect_output.shape[1],
    count=1,
    dtype=np.float32,
    crs=crs,
    transform=transform,
    nodata=nodata_aspect
) as dst:
    dst.write(aspect_output, 1)

print(json.dumps({
    'step_id': 'step_03',
    'status': 'completed',
    'input': str(input_dem_path),
    'output': str(output_aspect_path),
    'aspect_units': 'degrees_0_360_North_origin',
    'nodata_value': nodata_aspect
}))
