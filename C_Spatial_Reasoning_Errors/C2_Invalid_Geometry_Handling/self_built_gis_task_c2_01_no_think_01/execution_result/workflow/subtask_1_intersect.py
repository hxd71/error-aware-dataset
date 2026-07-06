# -*- coding: utf-8 -*-
"""
Intersect zones.geojson with masks.geojson and save as overlap_result.gpkg.

Steps:
1. Load and inspect both files.
2. Clean and normalize geometries (explode multipart, repair invalid).
3. Perform spatial intersection.
4. Preserve source_id and mask_id attributes.
5. Final geometry validation.
6. Save output to GeoPackage.
7. Verify output.
"""

import os
import sys

# Determine the working directory (the parent of this coder/subtask_1 folder)
WORKING_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity

print("=" * 60)
print("Starting intersection workflow")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. LOAD AND INSPECT BOTH FILES
# ---------------------------------------------------------------------------
zones_path = os.path.join(WORKING_DIRECTORY, 'data', 'zones.geojson')
masks_path = os.path.join(WORKING_DIRECTORY, 'data', 'masks.geojson')

print(f"\nLoading zones from: {zones_path}")
zones_raw = gpd.read_file(zones_path)
print(f"  CRS: {zones_raw.crs}")
print(f"  Rows: {len(zones_raw)}")
print(f"  Geometry types: {zones_raw.geometry.geom_type.unique().tolist()}")
print(f"  Columns: {zones_raw.columns.tolist()}")

print(f"\nLoading masks from: {masks_path}")
masks_raw = gpd.read_file(masks_path)
print(f"  CRS: {masks_raw.crs}")
print(f"  Rows: {len(masks_raw)}")
print(f"  Geometry types: {masks_raw.geometry.geom_type.unique().tolist()}")
print(f"  Columns: {masks_raw.columns.tolist()}")

# Confirm required columns
assert 'source_id' in zones_raw.columns, "zones missing source_id column"
assert 'mask_id' in masks_raw.columns, "masks missing mask_id column"

# Check invalid geometries in zones
print("\n--- Zone geometry validity ---")
invalid_count = 0
for idx, row in zones_raw.iterrows():
    if not row.geometry.is_valid:
        invalid_count += 1
        print(f"  Row {idx} ({row['source_id']}): INVALID - {explain_validity(row.geometry)}")
    else:
        print(f"  Row {idx} ({row['source_id']}): valid")
print(f"  Total invalid: {invalid_count}")

# Check invalid geometries in masks
print("\n--- Mask geometry validity ---")
invalid_count_m = 0
for idx, row in masks_raw.iterrows():
    if not row.geometry.is_valid:
        invalid_count_m += 1
        print(f"  Row {idx} ({row['mask_id']}): INVALID - {explain_validity(row.geometry)}")
    else:
        print(f"  Row {idx} ({row['mask_id']}): valid")
print(f"  Total invalid: {invalid_count_m}")

# ---------------------------------------------------------------------------
# 2. CLEAN AND NORMALIZE GEOMETRIES
# ---------------------------------------------------------------------------

def explode_and_clean(gdf, id_col, layer_name):
    """
    Explode MultiPolygons into single-part polygons,
    repair invalid geometries with buffer(0),
    and keep only Polygon/MultiPolygon types.
    """
    print(f"\n--- Cleaning {layer_name} ---")
    
    # Explode multipart
    gdf_exploded = gdf.explode(index_parts=False).reset_index(drop=True)
    print(f"  After explode: {len(gdf_exploded)} rows (was {len(gdf)})")
    
    # Repair invalid geometries with buffer(0)
    repaired_geoms = []
    for idx, row in gdf_exploded.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        if not geom.is_valid:
            repaired = geom.buffer(0)
            repaired_geoms.append(repaired)
        else:
            repaired_geoms.append(geom)
    
    gdf_exploded['geometry'] = repaired_geoms
    
    # Filter to only Polygon or MultiPolygon
    def is_poly_type(g):
        return isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty
    
    mask = gdf_exploded['geometry'].apply(is_poly_type)
    gdf_clean = gdf_exploded[mask].copy().reset_index(drop=True)
    print(f"  After filtering to Polygon/MultiPolygon: {len(gdf_clean)} rows")
    
    # Report geometry types
    geom_types = gdf_clean.geometry.geom_type.unique().tolist()
    print(f"  Geometry types present: {geom_types}")
    
    # Check validity after cleaning
    all_valid = gdf_clean.geometry.apply(lambda g: g.is_valid).all()
    print(f"  All geometries valid: {all_valid}")
    
    return gdf_clean

zones_clean = explode_and_clean(zones_raw, 'source_id', 'zones')
masks_clean = explode_and_clean(masks_raw, 'mask_id', 'masks')

# Ensure both layers share same CRS
if zones_clean.crs != masks_clean.crs:
    print(f"\nReprojecting masks from {masks_clean.crs} to {zones_clean.crs}")
    masks_clean = masks_clean.to_crs(zones_clean.crs)
else:
    print(f"\nBoth layers share CRS: {zones_clean.crs}")

# ---------------------------------------------------------------------------
# 3. PERFORM SPATIAL INTERSECTION
# ---------------------------------------------------------------------------
print("\n--- Performing spatial intersection ---")

# Use GeoPandas overlay with 'intersection' operation
result = gpd.overlay(zones_clean, masks_clean, how='intersection', keep_geom_type=False)
print(f"  Intersection result: {len(result)} rows")

# ---------------------------------------------------------------------------
# 4. PRESERVE ATTRIBUTES
# ---------------------------------------------------------------------------
# overlay automatically preserves columns from both inputs.
# Keep only source_id, mask_id, and geometry
keep_cols = ['source_id', 'mask_id', 'geometry']
# Add any columns that might be present
available_cols = [c for c in keep_cols if c in result.columns]
result = result[available_cols].copy()
print(f"  Output columns: {result.columns.tolist()}")

# ---------------------------------------------------------------------------
# 5. FINAL GEOMETRY VALIDATION
# ---------------------------------------------------------------------------
print("\n--- Final geometry validation ---")

# Re-apply buffer(0) to guarantee validity
result['geometry'] = result['geometry'].apply(lambda g: g.buffer(0) if g is not None else g)

# Filter to keep only valid Polygon/MultiPolygon
def is_valid_poly(g):
    if g is None:
        return False
    if g.is_empty:
        return False
    if not isinstance(g, (Polygon, MultiPolygon)):
        return False
    return g.is_valid

result = result[result['geometry'].apply(is_valid_poly)].copy().reset_index(drop=True)
print(f"  After final validation: {len(result)} rows")
print(f"  Geometry types: {result.geometry.geom_type.unique().tolist()}")
print(f"  All valid: {result.geometry.apply(lambda g: g.is_valid).all()}")

# ---------------------------------------------------------------------------
# 6. SAVE OUTPUT
# ---------------------------------------------------------------------------
output_path = os.path.join(WORKING_DIRECTORY, 'data', 'overlap_result.gpkg')
print(f"\n--- Saving to {output_path} ---")

# Ensure CRS is set
if result.crs is None:
    result = result.set_crs(zones_clean.crs)

result.to_file(output_path, layer='overlap_result', driver='GPKG')
print(f"  Saved {len(result)} features to {output_path}")

# ---------------------------------------------------------------------------
# 7. VERIFY OUTPUT
# ---------------------------------------------------------------------------
print("\n--- Verifying output ---")

# Read back
verify = gpd.read_file(output_path)
print(f"  File exists: {os.path.exists(output_path)}")
print(f"  Number of rows: {len(verify)}")
print(f"  CRS: {verify.crs}")
print(f"  Geometry types: {verify.geometry.geom_type.unique().tolist()}")
print(f"  Columns: {verify.columns.tolist()}")
print(f"  All geometries valid: {verify.geometry.apply(lambda g: g.is_valid).all()}")

# Spot-check records
print("\n--- Spot check ---")
for idx, row in verify.iterrows():
    g_type = row.geometry.geom_type
    is_valid = row.geometry.is_valid
    area = round(row.geometry.area, 4)
    print(f"  Row {idx}: source_id={row['source_id']}, mask_id={row['mask_id']}, "
          f"type={g_type}, valid={is_valid}, area={area}")

print("\n" + "=" * 60)
print("Intersection workflow completed successfully!")
print("=" * 60)
