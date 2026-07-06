# -*- coding: utf-8 -*-
import os
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points
import fiona

# --------------------------------------------------------------------------
# 0. Paths
# --------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()
AREA_SHP   = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'area.shp')
LINE_SHP   = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'line.shp')
OUTPUT_DIR  = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
OUTPUT_SHP  = os.path.join(OUTPUT_DIR, 'nearest_vertices.shp')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# 1. Read the single reference line geometry
# --------------------------------------------------------------------------
with fiona.open(LINE_SHP, 'r') as line_src:
    line_crs  = line_src.crs
    line_feats = list(line_src)          # only 1 feature expected
    if not line_feats:
        raise RuntimeError('line.shp contains no features')

line_geom = LineString(line_feats[0]['geometry']['coordinates'])

# --------------------------------------------------------------------------
# 2. Read polygon features and their attributes
# --------------------------------------------------------------------------
with fiona.open(AREA_SHP, 'r') as poly_src:
    poly_crs   = poly_src.crs
    poly_schema = poly_src.schema
    poly_feats = list(poly_src)

# Use line CRS if polygon CRS is missing, else polygon CRS
out_crs = poly_crs if poly_crs else line_crs

# --------------------------------------------------------------------------
# 3. For each polygon, find the vertex closest to the line
# --------------------------------------------------------------------------
output_records = []

for feat in poly_feats:
    props = feat['properties']
    coords = feat['geometry']['coordinates']

    # Polygon may have exterior + interior rings (holes).
    # We consider ALL vertices – exterior + all interior rings.
    min_dist = float('inf')
    best_vertex = None

    for ring_coords in coords:
        for x, y in ring_coords:
            pt = Point(x, y)
            dist = pt.distance(line_geom)
            if dist < min_dist:
                min_dist = dist
                best_vertex = (x, y)

    if best_vertex is None:
        continue   # degenerate polygon (no vertices)

    # Build output record
    rec_props = dict(props)        # copy original polygon attributes
    rec_props['min_dist'] = float(min_dist)

    output_records.append({
        'geometry': {
            'type': 'Point',
            'coordinates': best_vertex,
        },
        'properties': rec_props,
    })

# --------------------------------------------------------------------------
# 4. Define output schema – keep all original polygon fields + add min_dist
# --------------------------------------------------------------------------
# Get original polygon schema properties
poly_props_schema = poly_schema['properties']
out_props = dict(poly_props_schema)
out_props['min_dist'] = 'float'

out_schema = {
    'geometry': 'Point',
    'properties': out_props,
}

# --------------------------------------------------------------------------
# 5. Write output shapefile
# --------------------------------------------------------------------------
with fiona.open(
    OUTPUT_SHP,
    'w',
    driver='ESRI Shapefile',
    schema=out_schema,
    crs=out_crs,
    encoding='utf-8',
) as dst:
    for rec in output_records:
        dst.write(rec)

print(f'Done. {len(output_records)} nearest-vertex points written to:')
print(f'  {OUTPUT_SHP}')
