import json
import numpy as np
import rasterio
from pathlib import Path

# Input: merged DEM from step_01
dem_path = artifact_paths_by_name["merged_dem_richland.tif"]
output_path = output_paths[0]

# Compute slope using finite difference method
with rasterio.open(dem_path) as src:
    dem = src.read(1)
    nodata = src.nodata
    transform = src.transform
    crs = src.crs
    profile = src.profile.copy()
    
    # Get pixel size for slope scaling
    pixel_size_x = abs(transform.a)
    pixel_size_y = abs(transform.e)
    
    # Convert DEM to float32 BEFORE masking to allow filling with NaN
    dem_float = dem.astype(np.float32)
    
    # Create masked array handling nodata
    dem_masked = np.ma.masked_equal(dem_float, nodata) if nodata is not None else dem_float
    
    # Calculate gradients using finite differences
    # dz_dx: change in elevation per unit x (horizontal)
    # dz_dy: change in elevation per unit y (vertical)
    dz_dy, dz_dx = np.gradient(dem_masked.filled(np.nan), pixel_size_y, pixel_size_x)
    
    # Replace nodata gradients with nan for masking
    if np.ma.is_masked(dem_masked):
        mask = dem_masked.mask
        dz_dx = np.where(mask, np.nan, dz_dx)
        dz_dy = np.where(mask, np.nan, dz_dy)
    
    # Compute slope as angle of steepest descent (degrees)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)
    
    # Replace any infinite values with nan
    slope_deg = np.where(np.isfinite(slope_deg), slope_deg, np.nan)
    
    # Prepare output profile
    profile.update(
        driver='GTiff',
        count=1,
        dtype='float32',
        nodata=np.nan,
        compress='lzw'
    )
    
    # Write slope output
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(slope_deg.astype('float32'), 1)

print(json.dumps({
    "step_id": "step_02",
    "operation": "slope_computation",
    "input_dem": str(dem_path),
    "output_slope": str(output_path),
    "method": "finite_difference_arctan",
    "units": "degrees",
    "status": "success"
}))