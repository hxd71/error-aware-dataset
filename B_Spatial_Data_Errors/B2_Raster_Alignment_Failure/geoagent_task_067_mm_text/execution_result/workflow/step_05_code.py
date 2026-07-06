import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds

# Get the input path from artifacts
merged_dem_path = artifact_paths_by_name["merged_dem_richland.tif"]
output_path = output_paths[0]

# Read the DEM
with rasterio.open(merged_dem_path) as dem_dataset:
    dem = dem_dataset.read(1).astype(np.float64)
    transform = dem_dataset.transform
    crs = dem_dataset.crs
    nodata = dem_dataset.nodata

    # Get pixel size in degrees
    cell_size_x = transform.a
    cell_size_y = -transform.e

    # Handle nodata values - replace with NaN for gradient calculation
    if nodata is not None:
        dem[dem == nodata] = np.nan

    # Calculate meters per degree at the center latitude for accurate hillshade
    bounds = dem_dataset.bounds
    center_lat = (bounds.bottom + bounds.top) / 2.0
    lat_rad = np.radians(center_lat)
    meters_per_deg_lat = 111132.92 - 559.82 * np.cos(2.0 * lat_rad) + 1.175 * np.cos(4.0 * lat_rad)
    meters_per_deg_lon = 111412.84 * np.cos(lat_rad) - 93.5 * np.cos(3.0 * lat_rad)

    # Convert z to meters (DEM is in meters, 1 arc-second = ~30m)
    z_scale = meters_per_deg_lat

    # Compute gradients in meters
    dx, dy = np.gradient(dem)
    dx_m = dx * cell_size_x * meters_per_deg_lon
    dy_m = dy * cell_size_y * meters_per_deg_lat

    # Standard hillshade parameters
    azimuth_rad = np.radians(315.0)  # NW illumination
    altitude_rad = np.radians(45.0)  # 45 degree altitude

    # Calculate slope and aspect from gradients
    slope = np.arctan(np.sqrt(dx_m**2 + dy_m**2) / z_scale)
    aspect = np.arctan2(-dx_m, dy_m)

    # Compute hillshade illumination
    hillshade = np.sin(altitude_rad) * np.cos(slope) + \
                np.cos(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect)

    # Scale to 0-255 and clip
    hillshade = (hillshade * 255.0).clip(0.0, 255.0).astype(np.uint8)

    # Restore nodata regions
    if nodata is not None:
        hillshade[np.isnan(dem)] = 0

    # Prepare output profile
    profile = dem_dataset.profile.copy()
    profile.update({
        'dtype': 'uint8',
        'count': 1,
        'nodata': 0
    })

    # Write output
    with rasterio.open(output_path, 'w', **profile) as output_dataset:
        output_dataset.write(hillshade, 1)

# Execution summary
print(json.dumps({
    "step_id": "step_04",
    "status": "success",
    "output_path": str(output_path),
    "input_dem": str(merged_dem_path),
    "illumination_azimuth": 315,
    "illumination_altitude": 45,
    "output_shape": list(hillshade.shape),
    "output_dtype": str(hillshade.dtype)
}))
