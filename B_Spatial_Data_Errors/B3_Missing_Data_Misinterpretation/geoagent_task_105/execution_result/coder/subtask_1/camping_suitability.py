
# -*- coding: utf-8 -*-
"""
Camping Suitability Analysis
============================
Criteria:
  1. Terrain aspect > 100 degrees.
  2. Within 1000 meters of a road.

Works entirely in native CRS (EPSG:4326) using PROJ4 strings to avoid
PROJ database version conflicts. Distances are computed with
latitude-aware degree-to-meter scaling.

Data:
  DEM:     data/PA_DEM.tif
  Roads:   data/PA_Roads/PA_Roads.shp
"""

import os
import sys
import numpy as np
import rasterio
from rasterio import features
from rasterio.transform import from_bounds
import fiona
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Environment: suppress the broken PROJ database ─────────────────────
# The host has a conflicting proj.db from PostgreSQL.  We point PROJ_LIB
# at rasterio's own PROJ data so that CRS lookups succeed.
try:
    import rasterio.crs
    import rasterio._crs
    # Attempt to find rasterio's bundled PROJ data
    _rasterio_dir = os.path.dirname(rasterio.__file__)
    _proj_dir = os.path.join(_rasterio_dir, 'proj_data')
    if os.path.isdir(_proj_dir):
        os.environ['PROJ_LIB'] = _proj_dir
except Exception:
    pass

# ── Paths ──────────────────────────────────────────────────────────────
WORKING_DIRECTORY = os.getcwd()
DEM_PATH = os.path.join(WORKING_DIRECTORY, 'data', 'PA_DEM.tif')
ROADS_PATH = os.path.join(WORKING_DIRECTORY, 'data', 'PA_Roads', 'PA_Roads.shp')
OUTPUT_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_TIF = os.path.join(OUTPUT_DIR, 'camping_suitability.tif')
OUTPUT_PNG = os.path.join(OUTPUT_DIR, 'camping_suitability_map.png')

# Proj4 string for NAD83 / Conus Albers (EPSG:5070), used ONLY if reprojection succeeds
PROJ4_ALBERS = (
    '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 '
    '+x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
)

print("=" * 60)
print("CAMPING SUITABILITY ANALYSIS")
print("=" * 60)

# ── Step 1: Load DEM (keep in native CRS) ──────────────────────────────
print("\n[1/4] Loading DEM...")

with rasterio.open(DEM_PATH) as src:
    dem = src.read(1).astype(np.float32)
    dem_transform = src.transform
    dem_crs = src.crs
    dem_width = src.width
    dem_height = src.height
    dem_bounds = src.bounds
    dem_nodata = src.nodata

# Mask nodata: original nodata is 0; also mask elevations <= -50 as likely ocean/noise
dem_mask = (dem <= -50) | (dem == dem_nodata)
dem[dem_mask] = np.nan

res_x_deg = dem_transform[0]   # degrees longitude per pixel
res_y_deg = abs(dem_transform[4])  # degrees latitude per pixel

# Build latitude array for scaling longitude degrees to meters
latitudes = np.linspace(
    dem_bounds.top - res_y_deg / 2,
    dem_bounds.bottom + res_y_deg / 2,
    dem_height
)
lat_rad = np.radians(latitudes)
# Meters per degree of longitude at each latitude
meters_per_deg_lon = 111320.0 * np.cos(lat_rad)   # shape (height,)
meters_per_deg_lat = 111320.0                      # nearly constant

# Pixel ground dimensions (meters)
pix_x_m = res_x_deg * meters_per_deg_lon[:, np.newaxis]  # (height, width)
pix_y_m = res_y_deg * meters_per_deg_lat                  # scalar-ish

print(f"  DEM: {dem_height} rows x {dem_width} cols")
print(f"  Resolution: {res_x_deg:.6f}° × {res_y_deg:.6f}°")
print(f"  Pixel size at centre: ~{np.mean(pix_x_m):.1f} m (EW) × {pix_y_m:.1f} m (NS)")
print(f"  CRS: {dem_crs}")

# ── Step 2: Compute Aspect ─────────────────────────────────────────────
print("\n[2/4] Computing terrain aspect...")

# Gradient in degrees
dy_deg, dx_deg = np.gradient(dem, res_y_deg, res_x_deg)

# Convert degree-gradients to meter-gradients for correct aspect ratio
# dz/dx (m) = dz/dx (deg) / meters_per_deg_lon
# dz/dy (m) = dz/dy (deg) / meters_per_deg_lat
dz_dx_m = dx_deg / meters_per_deg_lon[:, np.newaxis]
dz_dy_m = dy_deg / meters_per_deg_lat

# Aspect: arctan2(dz/dx, -dz/dy)  (negative dy because raster y increases southward)
aspect_rad = np.arctan2(dz_dx_m, -dz_dy_m)
aspect_deg = np.degrees(aspect_rad)
aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360, aspect_deg)

# Flats get NaN
slope_mag = np.sqrt(dz_dx_m**2 + dz_dy_m**2)
aspect_deg = np.where(slope_mag < 1e-6, np.nan, aspect_deg)
aspect_deg = np.where(np.isnan(dem), np.nan, aspect_deg)

aspect_mask = (aspect_deg > 100) & (~np.isnan(aspect_deg))

print(f"  Aspect computed. Pixels with aspect > 100°: {np.sum(aspect_mask):,}")

# ── Step 3: Distance to Roads ──────────────────────────────────────────
print("\n[3/4] Computing distance to nearest road...")

# Rasterize roads at native DEM resolution
roads_raster = np.zeros((dem_height, dem_width), dtype=np.uint8)

with fiona.open(ROADS_PATH) as src:
    road_geoms = []
    for feat in src:
        geom = feat['geometry']
        if geom is not None:
            road_geoms.append(geom)

print(f"  Loaded {len(road_geoms)} road segments.")

# Rasterize in native CRS (EPSG:4326)
shapes = [(geom, 1) for geom in road_geoms]
roads_raster = features.rasterize(
    shapes=shapes,
    out_shape=(dem_height, dem_width),
    transform=dem_transform,
    fill=0,
    dtype=np.uint8,
    all_touched=True,
)

# Euclidean distance transform (pixel units)
non_road = (roads_raster == 0).astype(np.uint8)
dist_pixels, _ = distance_transform_edt(non_road, return_indices=True)

# Convert pixel distances to meters using latitude-aware scaling
# Average pixel size in meters at each row
pix_mean_m = (pix_x_m + pix_y_m) / 2.0   # (height, width)
distance_meters = dist_pixels * pix_mean_m

# Mask nodata
distance_meters = np.where(np.isnan(dem), np.nan, distance_meters)

proximity_mask = (distance_meters <= 1000) & (~np.isnan(distance_meters))

print(f"  Distance computed. Pixels within 1000 m of a road: {np.sum(proximity_mask):,}")

# ── Step 4: Combine & Save ─────────────────────────────────────────────
print("\n[4/4] Combining criteria and saving outputs...")

suitability = np.where(aspect_mask & proximity_mask, 1, 0).astype(np.uint8)
suitability = np.where(np.isnan(dem), 0, suitability)

suitable_count = np.sum(suitability == 1)
total_valid = np.sum(~np.isnan(dem))
print(f"  Suitable pixels: {suitable_count:,} / {total_valid:,} "
      f"({100 * suitable_count / total_valid:.2f}%)")

# ── Save GeoTIFF ─────────────────────────────────────────────────────
out_profile = {
    'driver': 'GTiff',
    'height': dem_height,
    'width': dem_width,
    'count': 1,
    'dtype': 'uint8',
    'crs': dem_crs,
    'transform': dem_transform,
    'nodata': 0,
    'compress': 'lzw',
}

with rasterio.open(OUTPUT_TIF, 'w', **out_profile) as dst:
    dst.write(suitability, 1)

print(f"  Saved suitability raster: {OUTPUT_TIF}")

# ── Generate Map ─────────────────────────────────────────────────────
print("  Generating suitability map...")

# Get bounds in native CRS (lon/lat)
left = dem_bounds.left
right = dem_bounds.right
bottom = dem_bounds.bottom
top = dem_bounds.top

fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# --- Panel 1: Aspect condition ---
ax1 = axes[0]
aspect_vis = np.where(aspect_deg > 100, 1, 0).astype(np.float32)
aspect_vis[np.isnan(dem)] = np.nan
im1 = ax1.imshow(aspect_vis, cmap='YlOrRd', interpolation='nearest',
                 extent=[left, right, bottom, top])
ax1.set_title('Condition 1: Aspect > 100°')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')

# --- Panel 2: Proximity condition ---
ax2 = axes[1]
prox_vis = np.where(distance_meters <= 1000, 1, 0).astype(np.float32)
prox_vis[np.isnan(dem)] = np.nan
im2 = ax2.imshow(prox_vis, cmap='Blues', interpolation='nearest',
                 extent=[left, right, bottom, top])
ax2.set_title('Condition 2: Within 1000 m of Roads')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')

# --- Panel 3: Combined suitability ---
ax3 = axes[2]
suit_vis = suitability.astype(np.float32)
suit_vis[suitability == 0] = np.nan
# Background: hillshade-like DEM
dem_vis = np.where(np.isnan(dem), np.nan, dem)
im3 = ax3.imshow(dem_vis, cmap='terrain', interpolation='nearest',
                 extent=[left, right, bottom, top], alpha=0.5)
im3b = ax3.imshow(suit_vis, cmap='Greens', interpolation='nearest',
                  extent=[left, right, bottom, top], vmin=0, vmax=1, alpha=0.8)
ax3.set_title('Camping Suitability Map\n(Aspect > 100° AND within 1000 m of roads)')
ax3.set_xlabel('Longitude')
ax3.set_ylabel('Latitude')

green_patch = mpatches.Patch(color='green', alpha=0.8, label='Suitable for Camping')
ax3.legend(handles=[green_patch], loc='upper right')

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches='tight')
plt.close()

print(f"  Saved suitability map: {OUTPUT_PNG}")

# Approximate area calculation
avg_pixel_area_m2 = np.mean(pix_x_m * pix_y_m)
suitable_area_km2 = suitable_count * avg_pixel_area_m2 / 1e6

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print(f"  Output raster: {OUTPUT_TIF}")
print(f"  Output map:    {OUTPUT_PNG}")
print(f"  Suitable area: ~{suitable_area_km2:.2f} km²")
print(f"  Suitable pixels: {suitable_count:,}")
print("=" * 60)
