
# -*- coding: utf-8 -*-
"""
Split polygon(s) by a line and save the resulting polygons as a new shapefile.

Inputs:
    - data/input/line.shp   : LineString used as the splitter
    - data/input/parcel.shp : Polygon(s) to be split

Output:
    - coder/subtask_1/split_parcels.shp : Resulting split polygons
"""

import os
import geopandas as gpd
from shapely.ops import split
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection

# ---------------------------------------------------------------------------
# 1. Define paths
# ---------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()

line_path = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'line.shp')
parcel_path = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'parcel.shp')
output_dir = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
output_path = os.path.join(output_dir, 'split_parcels.shp')

os.makedirs(output_dir, exist_ok=True)

# ---------------------------------------------------------------------------
# 2. Read input data
# ---------------------------------------------------------------------------
line_gdf = gpd.read_file(line_path)
parcel_gdf = gpd.read_file(parcel_path)

print(f"Line features : {len(line_gdf)}")
print(f"Parcel features: {len(parcel_gdf)}")

# ---------------------------------------------------------------------------
# 3. Collect the splitting line geometry (union all lines into one MultiLineString)
# ---------------------------------------------------------------------------
splitter_geom = line_gdf.geometry.unary_union
print(f"Splitter geometry type: {splitter_geom.geom_type}")

# ---------------------------------------------------------------------------
# 4. Split each polygon by the line
# ---------------------------------------------------------------------------
rows = []
for idx, row in parcel_gdf.iterrows():
    poly = row.geometry
    print(f"\nProcessing parcel Id={row['Id']}, TYPE={row['TYPE']}")

    # Only split if the line actually intersects this polygon
    if not splitter_geom.intersects(poly):
        print("  -- No intersection, keeping original polygon.")
        rows.append({
            'Id': row['Id'],
            'TYPE': row['TYPE'],
            'fragment': 1,
            'geometry': poly
        })
        continue

    # Perform the split
    result = split(poly, splitter_geom)

    # Extract all polygon parts from the result
    fragments = []
    if result.geom_type == 'GeometryCollection':
        for geom in result.geoms:
            if geom.geom_type in ('Polygon', 'MultiPolygon'):
                # Further unpack MultiPolygon
                if geom.geom_type == 'MultiPolygon':
                    fragments.extend(list(geom.geoms))
                else:
                    fragments.append(geom)
    elif result.geom_type == 'MultiPolygon':
        fragments = list(result.geoms)
    elif result.geom_type == 'Polygon':
        fragments = [result]

    print(f"  -- Produced {len(fragments)} fragment(s).")

    for frag_idx, frag in enumerate(fragments, start=1):
        rows.append({
            'Id': row['Id'],
            'TYPE': row['TYPE'],
            'fragment': frag_idx,
            'geometry': frag
        })

# ---------------------------------------------------------------------------
# 5. Build output GeoDataFrame and save
# ---------------------------------------------------------------------------
result_gdf = gpd.GeoDataFrame(rows, crs=parcel_gdf.crs)
result_gdf.to_file(output_path, encoding='UTF-8')

print(f"\nDone. Saved {len(result_gdf)} polygon feature(s) to:")
print(f"  {output_path}")
