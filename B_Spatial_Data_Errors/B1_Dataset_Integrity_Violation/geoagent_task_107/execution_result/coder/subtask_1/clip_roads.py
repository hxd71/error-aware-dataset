# -*- coding: utf-8 -*-
import os
import geopandas as gpd

# Determine working directory (where this script is executed from)
WORKING_DIRECTORY = os.getcwd()

def main():
    # ----- 1. Define input and output paths -----
    area_path = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'area.shp')
    road_path = os.path.join(WORKING_DIRECTORY, 'data', 'input', 'road.shp')
    output_dir = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
    output_path = os.path.join(output_dir, 'road_clipped.shp')

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # ----- 2. Read the boundary (area) layer -----
    print(f"Reading area boundary from: {area_path}")
    area_gdf = gpd.read_file(area_path)  # UTF-8, single polygon

    # ----- 3. Read the road layer -----
    print(f"Reading road layer from: {road_path}")
    # road.shp uses ISO-8859-1 encoding
    road_gdf = gpd.read_file(road_path, encoding='ISO-8859-1')

    print(f"  Area  CRS: {area_gdf.crs}")
    print(f"  Road  CRS: {road_gdf.crs}")
    print(f"  Area  features: {len(area_gdf)}")
    print(f"  Road  features: {len(road_gdf)}")

    # ----- 4. Align CRS if needed -----
    # Both layers have undefined CRS; if they differ, reproject road to area CRS
    if area_gdf.crs != road_gdf.crs:
        print("CRS mismatch — reprojecting road layer to area CRS ...")
        road_gdf = road_gdf.to_crs(area_gdf.crs)

    # ----- 5. Clip road layer by area boundary -----
    # Use geopandas.clip to keep all original attributes
    print("Clipping roads to area boundary ...")
    clipped_gdf = gpd.clip(road_gdf, area_gdf)

    print(f"  Clipped features: {len(clipped_gdf)}")

    # ----- 6. Save the clipped result -----
    print(f"Saving clipped roads to: {output_path}")
    clipped_gdf.to_file(output_path, encoding='UTF-8')

    print("Done.")
    print(f"Output fields: {list(clipped_gdf.columns)}")

if __name__ == '__main__':
    main()
