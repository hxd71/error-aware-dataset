
# -*- coding: utf-8 -*-
"""
Intersect zones.geojson with masks.geojson and save the result as overlap_result.gpkg.
Handles invalid bowtie geometries, multipart features, and ensures only valid
polygon geometries in the output.
"""

import os
import sys
import json
import warnings

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# 1. Paths
# ---------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()
DATA_DIR = os.path.join(WORKING_DIRECTORY, "data")

zones_path = os.path.join(DATA_DIR, "zones.geojson")
masks_path = os.path.join(DATA_DIR, "masks.geojson")
output_path = os.path.join(DATA_DIR, "overlap_result.gpkg")

print("=" * 70)
print("STEP 1: Load and inspect both files")
print("=" * 70)

# ---------------------------------------------------------------------------
# 2. Load layers
# ---------------------------------------------------------------------------
zones_raw = gpd.read_file(zones_path)
masks_raw = gpd.read_file(masks_path)

print(f"zones.geojson: {len(zones_raw)} features, CRS={zones_raw.crs}")
print(f"  Columns: {list(zones_raw.columns)}")
print(f"  Geometry types: {zones_raw.geometry.geom_type.unique().tolist()}")
print(f"  Invalid geometries: {(~zones_raw.is_valid).sum()}")

print(f"\nmasks.geojson: {len(masks_raw)} features, CRS={masks_raw.crs}")
print(f"  Columns: {list(masks_raw.columns)}")
print(f"  Geometry types: {masks_raw.geometry.geom_type.unique().tolist()}")
print(f"  Invalid geometries: {(~masks_raw.is_valid).sum()}")

# Confirm ID columns
assert "source_id" in zones_raw.columns, "source_id not found in zones!"
assert "mask_id" in masks_raw.columns, "mask_id not found in masks!"

# ---------------------------------------------------------------------------
# 3. Clean and normalize zones
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 2: Clean and normalize geometries")
print("=" * 70)

# --- Zones ---
# Keep only the needed columns to avoid overlay issues
zones = zones_raw[["source_id", "geometry"]].copy()

# 3a. Explode multipart geometries
print(f"\nZones before explode: {len(zones)} rows")
zones = zones.explode(index_parts=False).reset_index(drop=True)
print(f"Zones after explode: {len(zones)} rows")
print(f"  Geometry types after explode: {zones.geometry.geom_type.unique().tolist()}")

# 3b. Repair invalid geometries with buffer(0)
invalid_before = (~zones.is_valid).sum()
print(f"  Invalid before buffer(0): {invalid_before}")

def safe_buffer(geom):
    """Apply buffer(0) and handle results that may become multi-part."""
    if geom is None:
        return geom
    try:
        result = geom.buffer(0)
        return result
    except Exception as e:
        print(f"  WARNING: buffer(0) failed for geometry: {e}")
        return None

zones["geometry"] = zones["geometry"].apply(safe_buffer)

# Drop any rows that became None
zones = zones[zones["geometry"].notna()].reset_index(drop=True)

invalid_after = (~zones.is_valid).sum()
print(f"  Invalid after buffer(0): {invalid_after}")

# 3c. Filter to keep only Polygon and MultiPolygon
print(f"  Geometry types after buffer(0): {zones.geometry.geom_type.unique().tolist()}")
zones = zones[zones.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].reset_index(drop=True)
print(f"Zones after filtering to Polygon/MultiPolygon only: {len(zones)} rows")

# Re-explode after buffer(0) in case buffer(0) produced MultiPolygons
zones = zones.explode(index_parts=False).reset_index(drop=True)
print(f"Zones after re-explode: {len(zones)} rows")
print(f"  Final geometry types: {zones.geometry.geom_type.unique().tolist()}")

# --- Masks ---
print(f"\nMasks before cleanup: {len(masks_raw)} rows")
masks = masks_raw[["mask_id", "geometry"]].copy()

# Apply buffer(0) for safety
masks["geometry"] = masks["geometry"].apply(safe_buffer)
masks = masks[masks["geometry"].notna()].reset_index(drop=True)
print(f"  Invalid masks after buffer(0): {(~masks.is_valid).sum()}")

# Explode (safe even if no multiparts)
masks = masks.explode(index_parts=False).reset_index(drop=True)

# Filter to Polygon only
masks = masks[masks.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].reset_index(drop=True)
masks = masks.explode(index_parts=False).reset_index(drop=True)
print(f"Masks after cleanup: {len(masks)} rows")
print(f"  Final geometry types: {masks.geometry.geom_type.unique().tolist()}")

# ---------------------------------------------------------------------------
# 4. Ensure same CRS
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 3: Ensure CRS match and perform intersection")
print("=" * 70)

print(f"Zones CRS: {zones.crs}")
print(f"Masks CRS: {masks.crs}")

if zones.crs != masks.crs:
    print("Reprojecting masks to match zones CRS...")
    masks = masks.to_crs(zones.crs)

# ---------------------------------------------------------------------------
# 5. Perform intersection
# ---------------------------------------------------------------------------
print(f"\nPerforming overlay intersection...")
print(f"  Zones: {len(zones)} geometries")
print(f"  Masks: {len(masks)} geometries")

intersection = gpd.overlay(zones, masks, how="intersection", keep_geom_type=False)
print(f"Raw intersection result: {len(intersection)} rows")
print(f"  Geometry types: {intersection.geometry.geom_type.unique().tolist()}")

# ---------------------------------------------------------------------------
# 6. Final geometry validation
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 4: Final geometry validation and filtering")
print("=" * 70)

# Drop any None or empty geometries
intersection = intersection[intersection["geometry"].notna()].reset_index(drop=True)
intersection = intersection[~intersection["geometry"].is_empty].reset_index(drop=True)

print(f"After dropping empty/None: {len(intersection)} rows")

# Keep only Polygon geometries (drop LineStrings, Points, GeometryCollections, MultiPolygons)
print(f"  Types before filtering: {intersection.geometry.geom_type.unique().tolist()}")
intersection = intersection[intersection.geometry.geom_type == "Polygon"].reset_index(drop=True)
print(f"After keeping only Polygon: {len(intersection)} rows")

# Re-validate with buffer(0)
intersection["geometry"] = intersection["geometry"].apply(safe_buffer)
intersection = intersection[intersection["geometry"].notna()].reset_index(drop=True)
intersection = intersection[~intersection["geometry"].is_empty].reset_index(drop=True)

# Explode in case buffer(0) produced MultiPolygons
intersection = intersection.explode(index_parts=False).reset_index(drop=True)
intersection = intersection[intersection.geometry.geom_type == "Polygon"].reset_index(drop=True)

print(f"Final validated count: {len(intersection)} rows")
print(f"  All valid: {intersection.is_valid.all()}")
print(f"  All Polygon: {(intersection.geometry.geom_type == 'Polygon').all()}")

# ---------------------------------------------------------------------------
# 7. Select and order columns
# ---------------------------------------------------------------------------
# Ensure we only have source_id, mask_id, and geometry
final_columns = ["source_id", "mask_id", "geometry"]
intersection = intersection[final_columns]

print(f"\nFinal columns: {list(intersection.columns)}")
print(f"Unique source_ids: {intersection['source_id'].unique().tolist()}")
print(f"Unique mask_ids: {intersection['mask_id'].unique().tolist()}")

# ---------------------------------------------------------------------------
# 8. Save output
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 5: Save output")
print("=" * 70)

intersection.to_file(output_path, layer="overlap_result", driver="GPKG")
print(f"Saved to: {output_path}")

# ---------------------------------------------------------------------------
# 9. Verify output
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("STEP 6: Verify output")
print("=" * 70)

# Confirm file exists
assert os.path.exists(output_path), f"Output file not found: {output_path}"
print(f"File exists: True")
print(f"File size: {os.path.getsize(output_path):,} bytes")

# Re-read
verified = gpd.read_file(output_path)

print(f"\nVerification Report:")
print(f"  Number of rows: {len(verified)}")
print(f"  CRS: {verified.crs}")
print(f"  Geometry types: {verified.geometry.geom_type.unique().tolist()}")
print(f"  Columns: {list(verified.columns)}")
print(f"  All valid: {verified.is_valid.all()}")
print(f"  All Polygon: {(verified.geometry.geom_type == 'Polygon').all()}")

# Spot-check
print(f"\nSpot-check (first 5 rows):")
for idx, row in verified.head(5).iterrows():
    print(f"  Row {idx}: source_id={row['source_id']}, mask_id={row['mask_id']}, "
          f"geom_type={row.geometry.geom_type}, valid={row.geometry.is_valid}, "
          f"area={row.geometry.area:.6f}")

print(f"\nAll unique source_ids in output: {sorted(verified['source_id'].unique())}")
print(f"All unique mask_ids in output: {sorted(verified['mask_id'].unique())}")

print("\n" + "=" * 70)
print("DONE - overlap_result.gpkg created successfully")
print("=" * 70)
