
# -*- coding: utf-8 -*-
"""
Generate bounded Voronoi (Tyson) polygons for building features.

Steps:
1. Read buildings Shapefile
2. Convert building polygons to centroid points
3. Generate Voronoi diagram with a bounding envelope (all polygons bounded)
4. Overlay Voronoi polygons with original building polygons
5. Save results
"""

import os
import sys
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPoint, box, MultiPolygon
from shapely.ops import voronoi_diagram, unary_union

# ── Paths ──────────────────────────────────────────────────────────────
WORKING_DIRECTORY = os.getcwd()
INPUT_SHP = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'buildings.shp')
OUTPUT_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_VORONOI = os.path.join(OUTPUT_DIR, 'voronoi_polygons.shp')
OUTPUT_FINAL  = os.path.join(OUTPUT_DIR, 'final_result.shp')

print("=" * 65)
print("VORONOI POLYGON GENERATION FOR BUILDING FEATURES")
print("=" * 65)

# ── 1. Read building Shapefile ─────────────────────────────────────────
print("\n[1] Reading buildings shapefile...")
gdf_buildings = gpd.read_file(INPUT_SHP)
print(f"    → {len(gdf_buildings)} building polygons loaded.")
print(f"    → CRS: {gdf_buildings.crs}")
print(f"    → Columns: {list(gdf_buildings.columns)}")

# ── 2. Convert building polygons to centroid points ────────────────────
print("\n[2] Converting building polygons to centroid points...")
gdf_buildings['centroid_geom'] = gdf_buildings.geometry.centroid
gdf_points = gpd.GeoDataFrame(
    gdf_buildings.drop(columns=['geometry']),
    geometry='centroid_geom',
    crs=gdf_buildings.crs
)
print(f"    → {len(gdf_points)} centroid points created.")

# ── 3. Generate Voronoi diagram with shapely ───────────────────────────
print("\n[3] Generating Voronoi diagram (all polygons bounded)...")

# Build MultiPoint from all centroids
coords_list = [(p.x, p.y) for p in gdf_points.geometry]
multi_point = MultiPoint(coords_list)

# Compute bounding envelope: expand the point extent by 10%
all_x = [c[0] for c in coords_list]
all_y = [c[1] for c in coords_list]
minx, maxx = min(all_x), max(all_x)
miny, maxy = min(all_y), max(all_y)
dx = maxx - minx
dy = maxy - miny
pad_x = max(dx * 0.10, 50.0)
pad_y = max(dy * 0.10, 50.0)

envelope = box(minx - pad_x, miny - pad_y, maxx + pad_x, maxy + pad_y)
print(f"    → Envelope: ({minx-pad_x:.1f}, {miny-pad_y:.1f}) → ({maxx+pad_x:.1f}, {maxy+pad_y:.1f})")

# Generate Voronoi diagram — all polygons clipped to envelope
vor_diagram = voronoi_diagram(multi_point, envelope=envelope, tolerance=0.0, edges=False)
print(f"    → Raw voronoi_diagram type: {vor_diagram.geom_type}")

# Extract individual Voronoi polygons
if vor_diagram.geom_type == 'GeometryCollection':
    voronoi_polys = [g for g in vor_diagram.geoms if g.geom_type == 'Polygon']
elif vor_diagram.geom_type == 'MultiPolygon':
    voronoi_polys = list(vor_diagram.geoms)
elif vor_diagram.geom_type == 'Polygon':
    voronoi_polys = [vor_diagram]
else:
    raise RuntimeError(f"Unexpected voronoi_diagram output: {vor_diagram.geom_type}")

print(f"    → {len(voronoi_polys)} bounded Voronoi polygons extracted.")

# ── 4. Build Voronoi GeoDataFrame ──────────────────────────────────────
print("\n[4] Building Voronoi GeoDataFrame...")
gdf_voronoi = gpd.GeoDataFrame(
    {'voronoi_id': list(range(len(voronoi_polys)))},
    geometry=voronoi_polys,
    crs=gdf_buildings.crs
)

# ── Clean: make sure all geometries are valid ──────────────────────────
invalid_mask = ~gdf_voronoi.is_valid
if invalid_mask.any():
    print(f"    → Fixing {invalid_mask.sum()} invalid Voronoi geometries...")
    gdf_voronoi.geometry = gdf_voronoi.geometry.buffer(0)

print(f"    → {len(gdf_voronoi)} valid Voronoi polygons ready.")
gdf_voronoi.to_file(OUTPUT_VORONOI)
print(f"    → Saved: {OUTPUT_VORONOI}")

# ── 5. Overlay analysis ────────────────────────────────────────────────
print("\n[5] Overlay analysis: Voronoi × Building polygons...")

# Strategy: spatial join each building (by centroid) to its Voronoi cell,
# then compute intersection area to enrich the Voronoi polygons.
gdf_bldg_pt = gdf_buildings.copy()
gdf_bldg_pt['_centroid'] = gdf_bldg_pt.geometry.centroid
gdf_bldg_pt.geometry = gdf_bldg_pt['_centroid']

# Spatial join: which Voronoi polygon does each building centroid fall into?
joined = gpd.sjoin(gdf_bldg_pt, gdf_voronoi, how='left', predicate='within')
print(f"    → Spatial join: {len(joined)} buildings assigned to Voronoi cells.")

# Enrich voronoi with building stats
gdf_voronoi['building_count'] = 0
gdf_voronoi['building_area'] = 0.0
gdf_voronoi['building_ids'] = ''

# Also compute actual overlay intersection geometries
overlay_records = []

for vor_id in gdf_voronoi['voronoi_id']:
    vor_poly = gdf_voronoi.loc[gdf_voronoi['voronoi_id'] == vor_id, 'geometry'].values[0]

    # Buildings assigned to this voronoi cell
    bldgs_in_cell = joined[joined['voronoi_id'] == vor_id]

    if len(bldgs_in_cell) > 0:
        ids = []
        total_area = 0.0
        for _, bldg_row in bldgs_in_cell.iterrows():
            bldg_geom = gdf_buildings.loc[bldg_row.name, 'geometry']
            bldg_id = bldg_row.get('Id', bldg_row.name)

            try:
                intersection = vor_poly.intersection(bldg_geom)
                if not intersection.is_empty:
                    if intersection.geom_type in ('Polygon', 'MultiPolygon'):
                        overlay_records.append({
                            'voronoi_id': vor_id,
                            'building_id': bldg_id,
                            'geometry': intersection
                        })
                        total_area += intersection.area
                    elif intersection.geom_type == 'GeometryCollection':
                        for g in intersection.geoms:
                            if g.geom_type in ('Polygon', 'MultiPolygon'):
                                overlay_records.append({
                                    'voronoi_id': vor_id,
                                    'building_id': bldg_id,
                                    'geometry': g
                                })
                                total_area += g.area
            except Exception as exc:
                print(f"    ⚠ Intersection failed for voronoi={vor_id}, building={bldg_id}: {exc}")

            ids.append(str(bldg_id))

        gdf_voronoi.loc[gdf_voronoi['voronoi_id'] == vor_id, 'building_count'] = len(bldgs_in_cell)
        gdf_voronoi.loc[gdf_voronoi['voronoi_id'] == vor_id, 'building_area'] = total_area
        gdf_voronoi.loc[gdf_voronoi['voronoi_id'] == vor_id, 'building_ids'] = ','.join(ids)

print(f"    → {len(overlay_records)} overlay intersection features generated.")

# ── 6. Save final results ──────────────────────────────────────────────
print("\n[6] Saving final results...")

# Final Voronoi with building statistics
gdf_voronoi.to_file(OUTPUT_FINAL)
print(f"    → Final Voronoi (with stats): {OUTPUT_FINAL}")
print(f"       Columns: {list(gdf_voronoi.columns)}")

# ── Summary ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"  Input buildings:           {len(gdf_buildings)}")
print(f"  Voronoi polygons:          {len(gdf_voronoi)}")
print(f"  Overlay intersections:     {len(overlay_records)}")
print(f"  Buildings matched to cells:{joined['voronoi_id'].notna().sum()} / {len(joined)}")
print(f"\n  Output files:")
print(f"    {OUTPUT_VORONOI}")
print(f"    {OUTPUT_FINAL}")
print("=" * 65)
print("DONE")
