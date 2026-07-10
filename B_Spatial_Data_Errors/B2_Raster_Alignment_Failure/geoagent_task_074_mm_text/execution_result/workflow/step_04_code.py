from src.tools.raster_tools import clip_raster_by_bounds
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.transform import from_bounds
from scipy.spatial.distance import cdist

# Load hospital points
hospitals_path = asset_paths_by_id["sanfranciscohospitals"]
hospitals_gdf = gpd.read_file(hospitals_path)

# Use tracts_mask_100m.tif as template for resolution and extent
template_path = artifact_paths_by_name["tracts_mask_100m.tif"]
with rasterio.open(template_path) as src:
    template_transform = src.transform
    template_crs = src.crs
    template_width = src.width
    template_height = src.height
    template_bounds = src.bounds

# Extract hospital coordinates in raster CRS
hospital_coords = hospitals_gdf.geometry.apply(lambda g: (g.x, g.y)).tolist()
hospital_coords = np.array(hospital_coords)

# Generate cell center coordinates for the template raster
y_coords = np.arange(template_height - 0.5, -0.5, -1) * abs(template_transform.a) + template_transform.f
x_coords = np.arange(0.5, template_width + 0.5, 1) * template_transform.a + template_transform.c
xx, yy = np.meshgrid(x_coords, y_coords)
cell_centers = np.stack([xx.ravel(), yy.ravel()], axis=1)

# Compute Euclidean distance from each cell to nearest hospital
distances = cdist(cell_centers, hospital_coords).min(axis=1)
distance_grid = distances.reshape(template_height, template_width)

# Write output raster matching template CRS and resolution
output_path = output_paths[0]
with rasterio.open(
    output_path,
    'w',
    driver='GTiff',
    height=template_height,
    width=template_width,
    count=1,
    dtype=rasterio.float64,
    crs=template_crs,
    transform=template_transform,
    nodata=-999
) as dst:
    dst.write(distance_grid.astype(rasterio.float64), 1)

print(json.dumps({"step_id": "step_02", "output": output_path, "status": "success"}))