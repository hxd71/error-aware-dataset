# -*- coding: utf-8 -*-
"""
Create a distance buffer for each polygon feature in area.shp.
All original attribute fields are preserved in the output.
"""

import os
import geopandas as gpd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()
INPUT_SHP = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'area.shp')
OUTPUT_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
OUTPUT_SHP = os.path.join(OUTPUT_DIR, 'area_buffer.shp')

BUFFER_DISTANCE = 500  # <<< Adjust this value to your desired buffer distance

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Read the input shapefile
    print(f"Reading: {INPUT_SHP}")
    gdf = gpd.read_file(INPUT_SHP)
    print(f"  Features: {len(gdf)}")
    print(f"  Geometry type: {gdf.geom_type.unique().tolist()}")
    print(f"  CRS: {gdf.crs}")
    print(f"  Columns: {list(gdf.columns)}")

    # 2. Create buffer (preserves all attribute fields automatically)
    print(f"\nBuffering with distance = {BUFFER_DISTANCE} ...")
    gdf_buffered = gdf.copy()
    gdf_buffered['geometry'] = gdf.geometry.buffer(BUFFER_DISTANCE)
    print(f"  Buffered geometry type: {gdf_buffered.geom_type.unique().tolist()}")

    # 3. Save to new shapefile
    print(f"\nSaving to: {OUTPUT_SHP}")
    gdf_buffered.to_file(OUTPUT_SHP, encoding='utf-8')
    print("Done! Output shapefile created successfully.")

if __name__ == '__main__':
    main()
