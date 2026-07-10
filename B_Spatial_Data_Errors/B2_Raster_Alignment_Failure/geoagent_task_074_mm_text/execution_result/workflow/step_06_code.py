import rasterio
import json

# Input and output paths from runtime bindings
input_raster = artifact_paths_by_name["tracts_hospital_distances.tif"]
output_raster = output_paths[0]

# Copy the raster using rasterio.open() in write mode with source profile
with rasterio.open(input_raster) as src:
    profile = src.profile
    with rasterio.open(output_raster, 'w', **profile) as dst:
        dst.write(src.read())

# Validate the output raster properties
with rasterio.open(output_raster) as src:
    crs = src.crs
    resolution = src.res
    bounds = src.bounds
    nodata = src.nodata
    shape = src.shape

# Reference bounds from sanfrancisco_tracts_central asset
ref_bounds = [523221.31202312454, 4146314.8895950876, 587808.8484534516, 4207741.988431644]

# Validation checks
covers_extent = (
    bounds.left <= ref_bounds[0] and
    bounds.bottom <= ref_bounds[1] and
    bounds.right >= ref_bounds[2] and
    bounds.top >= ref_bounds[3]
)
has_100m_resolution = resolution[0] == 100.0 and resolution[1] == 100.0
has_correct_crs = str(crs) == "EPSG:26710"

# Execution summary
summary = {
    "step_id": "step_04",
    "operation": "rename_and_validate",
    "input": input_raster,
    "output": output_raster,
    "validation": {
        "crs_matches_epsg_26710": has_correct_crs,
        "has_100m_resolution": has_100m_resolution,
        "resolution": resolution,
        "covers_tract_bounds": covers_extent,
        "output_bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
        "nodata_value": nodata,
        "shape": shape
    },
    "status": "success"
}

print(json.dumps(summary, indent=2))