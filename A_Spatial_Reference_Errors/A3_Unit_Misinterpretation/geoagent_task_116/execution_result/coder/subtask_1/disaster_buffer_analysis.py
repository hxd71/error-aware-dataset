# -*- coding: utf-8 -*-
"""
Multi-ring buffer analysis for disaster impact assessment.
- Creates multi-ring buffers (100, 200, 300, 400 m) around area.shp
- Overlays (intersects) road.shp with those buffer rings
- Saves the result as a new Shapefile.
"""

import os
import sys

# --- Determine WORKING_DIRECTORY ---
# The script is executed from the working directory; use that as root.
WORKING_DIRECTORY = os.getcwd()
# Ensure 'coder/subtask_1' exists for outputs
OUTPUT_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Resolve input paths ---
AREA_PATH = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'area.shp')
ROAD_PATH = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'road.shp')

print(f"WORKING_DIRECTORY: {WORKING_DIRECTORY}")
print(f"Area file: {AREA_PATH}")
print(f"Road file: {ROAD_PATH}")
print(f"Output dir: {OUTPUT_DIR}")

try:
    import geopandas as gpd
    from shapely.geometry import Polygon, MultiPolygon
    import pandas as pd
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. Read input data
# ---------------------------------------------------------------------------
print("\n[Step 1] Reading input shapefiles ...")
area_gdf = gpd.read_file(AREA_PATH)
road_gdf = gpd.read_file(ROAD_PATH)

print(f"  Area features : {len(area_gdf)}")
print(f"  Road features : {len(road_gdf)}")
print(f"  Area CRS      : {area_gdf.crs}")
print(f"  Road CRS      : {road_gdf.crs}")

# Ensure CRS consistency — if one has CRS and the other doesn't, propagate it.
if area_gdf.crs is None and road_gdf.crs is not None:
    area_gdf = area_gdf.set_crs(road_gdf.crs)
elif road_gdf.crs is None and area_gdf.crs is not None:
    road_gdf = road_gdf.set_crs(area_gdf.crs)
# If both are None, we proceed as-is (both share the same projected meter system).

# ---------------------------------------------------------------------------
# 2. Create multi-ring buffers
# ---------------------------------------------------------------------------
print("\n[Step 2] Creating multi-ring buffers at 100, 200, 300, 400 m ...")

BUFFER_DISTANCES = [100, 200, 300, 400]

# Dissolve all area polygons into one unified disaster zone for cleaner rings.
# (Multi-ring buffers from individual polygons would otherwise overlap heavily.)
area_union = area_gdf.geometry.unary_union
print(f"  Union geometry type: {area_union.geom_type}")

buffer_records = []
for dist in BUFFER_DISTANCES:
    ring = area_union.buffer(dist)
    buffer_records.append({
        'distance_m': dist,
        'ring_label': f'{dist}m',
        'geometry': ring,
    })

buffer_gdf = gpd.GeoDataFrame(buffer_records, crs=area_gdf.crs)
print(f"  Created {len(buffer_gdf)} buffer rings.")

# ---------------------------------------------------------------------------
# 3. Overlay roads with buffers (intersection)
# ---------------------------------------------------------------------------
print("\n[Step 3] Overlaying roads with buffer rings (intersection) ...")

# Perform spatial intersection: for each road segment, clip it to each buffer ring.
# This gives us road portions that fall within each distance band.
overlay_parts = []
for idx, buf_row in buffer_gdf.iterrows():
    ring_geom = buf_row['geometry']
    dist = buf_row['distance_m']
    ring_label = buf_row['ring_label']

    # Clip roads to this ring
    clipped = road_gdf.copy()
    clipped['geometry'] = clipped.geometry.intersection(ring_geom)

    # Remove empty results (roads that don't intersect this ring)
    clipped = clipped[~clipped.geometry.is_empty]
    clipped = clipped[clipped.geometry.is_valid]

    if len(clipped) == 0:
        print(f"  Ring {ring_label}: no roads intersected.")
        continue

    # Add ring metadata
    clipped['distance_m'] = dist
    clipped['ring_label'] = ring_label

    # Explode multi-part geometries into single parts
    clipped = clipped.explode(index_parts=False).reset_index(drop=True)

    overlay_parts.append(clipped)
    print(f"  Ring {ring_label}: {len(clipped)} road segment(s) after intersection.")

if overlay_parts:
    overlay_gdf = gpd.GeoDataFrame(
        pd.concat(overlay_parts, ignore_index=True),
        crs=road_gdf.crs,
    )
else:
    print("  WARNING: No road segments intersected any buffer ring. Creating empty result.")
    overlay_gdf = gpd.GeoDataFrame(
        columns=list(road_gdf.columns) + ['distance_m', 'ring_label', 'geometry'],
        crs=road_gdf.crs,
    )

print(f"  Total overlay features: {len(overlay_gdf)}")

# ---------------------------------------------------------------------------
# 4. Save result as Shapefile
# ---------------------------------------------------------------------------
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'disaster_impact_roads.shp')
print(f"\n[Step 4] Saving result to: {OUTPUT_PATH} ...")

overlay_gdf.to_file(OUTPUT_PATH, encoding='utf-8')
print("  Done. Shapefile saved successfully.")

# Also save the buffer rings for visualisation reference
BUFFER_OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'multi_ring_buffers.shp')
buffer_gdf.to_file(BUFFER_OUTPUT_PATH, encoding='utf-8')
print(f"  Buffer rings saved to: {BUFFER_OUTPUT_PATH}")

print("\n=== All processing completed successfully. ===")
