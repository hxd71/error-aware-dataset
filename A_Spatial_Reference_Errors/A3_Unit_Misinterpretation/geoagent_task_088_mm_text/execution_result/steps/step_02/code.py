import json
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from scipy.interpolate import Rbf

# Load the filtered points from prior step artifact
input_shp = current_step_artifacts_by_name["filtered_points_2013_onward.shp"]["path"]
gdf = gpd.read_file(input_shp)

# Extract x, y coordinates and elevation field
x = gdf.geometry.x.values
y = gdf.geometry.y.values
z = gdf["elevatio_1"].values

# Filter out NaN values
mask = ~np.isnan(z)
x, y, z = x[mask], y[mask], z[mask]

# Get bounding box and define 10m grid
bounds = gdf.total_bounds
minx, miny, maxx, maxy = bounds
cell_size = 10.0

# Calculate grid dimensions
cols = int(np.ceil((maxx - minx) / cell_size))
rows = int(np.ceil((maxy - miny) / cell_size))

# Create grid coordinates
grid_x = np.linspace(minx, maxx, cols)
grid_y = np.linspace(maxy, miny, rows)
grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)

# Perform IDW interpolation using scipy's Rbf with 'inverse' function
rbf = Rbf(x, y, z, function='inverse', smooth=0.0)
grid_z = rbf(grid_xx, grid_yy)

# Create raster transform from bounds
transform = from_bounds(minx, miny, maxx, maxy, cols, rows)

# Write output GeoTIFF
output_path = output_paths[0]
with rasterio.open(
    output_path,
    'w',
    driver='GTiff',
    height=rows,
    width=cols,
    count=1,
    dtype=np.float32,
    crs=str(gdf.crs),
    transform=transform,
    nodata=np.nan
) as dst:
    dst.write(grid_z.astype(np.float32), 1)

print(json.dumps({
    "step_id": "step_02",
    "status": "success",
    "output_paths": output_paths,
    "grid_shape": [rows, cols],
    "cell_size": cell_size,
    "bounds": [minx, miny, maxx, maxy],
    "point_count": len(x)
}))
