import json
import numpy as np
import rasterio

# Paths
dem_path = asset_paths_by_id['rolla_dem_projected']
output_path = output_paths[0]

# Read DEM and compute slope using rasterio's terrain utilities
with rasterio.open(dem_path) as src:
    dem = src.read(1)
    profile = src.profile.copy()
    crs = src.crs
    nodata = src.nodata

# Get proper cell size from the transform
with rasterio.open(dem_path) as src:
    transform = src.transform
    cell_size_x = abs(transform.a)  # pixel width
    cell_size_y = abs(transform.e)  # pixel height (usually negative, so use abs)

# For a DEM in projected CRS with meter units, cell_size is in meters
cell_size = (cell_size_x + cell_size_y) / 2.0

# Convert DEM to float64 for processing
dem_float = dem.astype(np.float64)

# Replace nodata values with NaN for processing
if nodata is not None:
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)

# Compute slope using Horn's method with proper array indexing
# Pad the array to handle edges
padded = np.pad(dem_float, 1, mode='edge')

# Extract windowed views for vectorized computation
z_tl = padded[0:-2, 0:-2]   # top-left
z_tm = padded[0:-2, 1:-1]   # top-middle
z_tr = padded[0:-2, 2:]     # top-right
z_ml = padded[1:-1, 0:-2]   # middle-left
z_mr = padded[1:-1, 2:]     # middle-right
z_bl = padded[2:, 0:-2]     # bottom-left
z_bm = padded[2:, 1:-1]    # bottom-middle
z_br = padded[2:, 2:]       # bottom-right

# Horn's method: weight center rows/cols by 2
# dz/dx (east-west gradient)
dz_dx = ((z_tr + 2 * z_mr + z_br) - (z_tl + 2 * z_ml + z_bl)) / (8.0 * cell_size)

# dz/dy (north-south gradient) - note: row index increases downward
# z_br - z_tr gives south minus north
dz_dy = ((z_bl + 2 * z_bm + z_br) - (z_tl + 2 * z_tm + z_tr)) / (8.0 * cell_size)

# Calculate slope in degrees
slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
slope_deg = np.degrees(slope_rad)

# Handle any NaN values from edges or nodata
slope_deg = np.where(np.isnan(slope_deg), -9999.0, slope_deg)

# Update profile for output
profile.update(
    dtype=rasterio.float32,
    nodata=-9999.0,
    count=1,
    compress='lzw'
)

# Write output slope raster
with rasterio.open(output_path, 'w', **profile) as dst:
    dst.write(slope_deg.astype(np.float32), 1)

# Print execution summary
print(json.dumps({
    'step_id': 'step_01',
    'operation': 'terrain_slope_calculation',
    'input_dem': dem_path,
    'output_slope': output_path,
    'slope_units': 'degrees',
    'cell_size_x_metres': cell_size_x,
    'cell_size_y_metres': cell_size_y,
    'cell_size_avg_metres': cell_size,
    'source_crs': str(crs),
    'nodata_input': nodata,
    'nodata_output': -9999.0,
    'slope_range_check': {
        'min': float(np.min(slope_deg[slope_deg > -9999.0])) if np.any(slope_deg > -9999.0) else None,
        'max': float(np.max(slope_deg[slope_deg > -9999.0])) if np.any(slope_deg > -9999.0) else None,
        'valid_degrees': float(np.max(slope_deg[slope_deg > -9999.0])) < 90.0 if np.any(slope_deg > -9999.0) else True
    }
}))