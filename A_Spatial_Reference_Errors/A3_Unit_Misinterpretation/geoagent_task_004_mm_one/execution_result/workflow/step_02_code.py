import json
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import LineString
from skimage import measure

# Input and output paths
dem_path = asset_paths_by_id["puerto_dem"]
output_path = output_paths[0]

# Read DEM with rasterio
with rasterio.open(dem_path) as src:
    dem_data = src.read(1).astype(np.float64)
    transform = src.transform
    crs = src.crs
    nodata = src.nodata

# Check elevation statistics
print(f"DEM dtype: {dem_data.dtype}")
print(f"DEM min: {np.nanmin(dem_data):.2f}")
print(f"DEM max: {np.nanmax(dem_data):.2f}")
print(f"DEM mean: {np.nanmean(dem_data):.2f}")
print(f"Nodata value: {nodata}")

# Mask nodata values (only if nodata is set and not part of valid data)
if nodata is not None and nodata == 0.0:
    # For elevation 0 may be valid (sea level), only mask if clearly nodata regions exist
    valid_mask = dem_data != nodata
    if np.any(~valid_mask):
        dem_data = np.where(~valid_mask, np.nan, dem_data)
        print(f"Masked {np.sum(~valid_mask)} nodata pixels")

# Calculate contour levels at 50m interval
contour_interval = 50.0
min_val = np.nanmin(dem_data)
max_val = np.nanmax(dem_data)

print(f"Elevation range: {min_val:.2f}m to {max_val:.2f}m")

# Calculate contour levels
start = np.floor(min_val / contour_interval) * contour_interval
end = np.ceil(max_val / contour_interval) * contour_interval
levels = np.arange(start, end + contour_interval, contour_interval)

print(f"Contour levels: {len(levels)} levels from {start:.1f}m to {end:.1f}m")

contour_records = []

# Process each contour level using marching squares algorithm
for level in levels:
    contours = measure.find_contours(dem_data, level)
    
    for contour in contours:
        # Skip very small contours (likely artifacts)
        if len(contour) < 3:
            continue
            
        # Convert pixel coordinates to map coordinates using affine transform
        coords = []
        for row, col in contour:
            x = transform.c + col * transform.a + row * transform.b
            y = transform.f + col * transform.d + row * transform.e
            coords.append((x, y))
        
        if len(coords) >= 2:
            line = LineString(coords)
            # Ensure we have proper LineString geometry (not polygon-like)
            if line.geom_type == 'LineString' and line.is_valid:
                contour_records.append({
                    'geometry': line,
                    'elevation': float(level)
                })

print(f"Generated {len(contour_records)} contour features")

# Create GeoDataFrame with explicit LineString geometry
if contour_records:
    gdf = gpd.GeoDataFrame(contour_records, crs=crs, geometry='geometry')
else:
    gdf = gpd.GeoDataFrame(columns=['elevation', 'geometry'], crs=crs, geometry='geometry')

# Verify geometry type before writing
unique_types = gdf.geom_type.unique()
print(f"Output geometry types: {list(unique_types)}")

# Ensure all geometries are LineString
if not all(gt == 'LineString' for gt in unique_types):
    print(f"WARNING: Non-LineString geometries detected: {unique_types}")

# Write to ESRI Shapefile
gdf.to_file(output_path, driver='ESRI Shapefile')
print(f"Written to: {output_path}")

# Verify the output by reading it back
verify_gdf = gpd.read_file(output_path)
print(f"Verified: {len(verify_gdf)} features in output file")
print(f"Verified geometry types: {verify_gdf.geom_type.unique().tolist()}")

# Execution summary
summary = {
    "step_id": "step_01",
    "operation": "contour_generation",
    "interval_meters": 50,
    "input_crs": str(crs),
    "elevation_range": [float(min_val), float(max_val)],
    "contour_levels": len(levels),
    "contour_count": len(gdf),
    "geometry_types": list(unique_types),
    "output_path": str(output_path)
}
print(json.dumps(summary))