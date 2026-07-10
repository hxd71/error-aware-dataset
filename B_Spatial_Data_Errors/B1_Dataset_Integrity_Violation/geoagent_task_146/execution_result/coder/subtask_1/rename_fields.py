# -*- coding: utf-8 -*-
import os
import geopandas as gpd

WORKING_DIRECTORY = os.getcwd()
SUBTASK_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')

# Input
input_shp = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'point.shp')

# Output
output_shp = os.path.join(SUBTASK_DIR, 'point_chinese.shp')

# Read the shapefile
gdf = gpd.read_file(input_shp)

print("Original fields:", list(gdf.columns))

# Rename fields to Chinese
rename_map = {
    'AREA': '面积',
    'PERIMETER': '周长',
    'WELLS_ID': '井编号',
    'DEPTH': '深度',
    'TYPE': '类型',
}

gdf.rename(columns=rename_map, inplace=True)

print("Renamed fields:", list(gdf.columns))

# Save as new shapefile
gdf.to_file(output_shp, encoding='utf-8')

print(f"Saved to: {output_shp}")
