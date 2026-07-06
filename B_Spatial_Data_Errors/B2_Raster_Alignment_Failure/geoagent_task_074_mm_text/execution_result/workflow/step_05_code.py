import json
import numpy as np
import rasterio

# Get input and output paths from runtime bindings
distance_raster_path = artifact_paths_by_name["distance_to_hospitals.tif"]
mask_raster_path = artifact_paths_by_name["tracts_mask_100m.tif"]
output_raster_path = output_paths[0]

# Read both raster datasets
with rasterio.open(distance_raster_path) as distance_src, rasterio.open(mask_raster_path) as mask_src:
    distance_data = distance_src.read(1)
    mask_data = mask_src.read(1)
    profile = distance_src.profile.copy()
    
    # Set nodata value for output
    nodata_value = -9999.0
    profile['nodata'] = nodata_value
    
    # Apply mask: keep distance values where tracts_mask == 1, set nodata elsewhere
    masked_data = np.where(mask_data == 1, distance_data, nodata_value)
    
    # Write the masked raster output
    with rasterio.open(output_raster_path, 'w', **profile) as dst:
        dst.write(masked_data, 1)

# Print execution summary
print(json.dumps({
    "step_id": "step_03",
    "status": "success",
    "output": output_raster_path,
    "valid_cells": int(np.sum(mask_data == 1))
}))