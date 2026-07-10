import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
import matplotlib.pyplot as plt

def direct_solution():
    """
    Create a point layer for South Carolina hospitals and overlay it on the SC ZIP boundary map.
    - Inputs:
        - SC ZIP boundary shapefile (WGS84, zipped): F:\\...\\sc_zip_boundary.zip
        - SC hospital CSV with columns 'lat_x' (latitude) and 'lon_y' (longitude)
    - Outputs:
        - axis_order_hospitals_map.png : map showing hospitals over ZIP boundaries
        - axis_order_hospitals_points.geojson : hospital point GeoJSON
    - Returns: count of hospitals inside the union of SC ZIP boundaries
    """
    # 1. Read ZIP boundaries (zipped shapefile)
    zip_path = r"<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\axis_order_sc_hospitals\sc_zip_boundary.zip"
    sc_zip = gpd.read_file(zip_path)
    # Ensure WGS84 (EPSG:4326)
    if sc_zip.crs is not None and sc_zip.crs.to_epsg() != 4326:
        sc_zip = sc_zip.to_crs(epsg=4326)

    # 2. Read hospital CSV
    csv_path = r"<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\axis_order_sc_hospitals\SC_hospitals_axis_confusing.csv"
    df = pd.read_csv(csv_path)
    # Drop rows with missing coordinates
    df.dropna(subset=['lat_x', 'lon_y'], inplace=True)
    # Ensure numeric (in case of strings)
    df['lat_x'] = pd.to_numeric(df['lat_x'], errors='coerce')
    df['lon_y'] = pd.to_numeric(df['lon_y'], errors='coerce')
    df.dropna(subset=['lat_x', 'lon_y'], inplace=True)

    # 3. Build point geometries: x = lon_y, y = lat_x
    geometry = [Point(xy) for xy in zip(df['lon_y'], df['lat_x'])]
    hospitals_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # 4. Compute union of all ZIP polygons
    union_geom = unary_union(sc_zip.geometry.values)

    # 5. Count hospitals inside the union
    inside_mask = hospitals_gdf.geometry.intersects(union_geom)
    count_inside = inside_mask.sum()
    print(f"Number of hospital points inside SC ZIP boundary union: {count_inside}")

    # 6. Save hospital points as GeoJSON
    hospitals_gdf.to_file("axis_order_hospitals_points.geojson", driver="GeoJSON")

    # 7. Create map: ZIP boundaries + hospitals
    fig, ax = plt.subplots(figsize=(15, 10))
    sc_zip.plot(ax=ax, facecolor='lightgrey', edgecolor='black', linewidth=0.5,
                label='SC ZIP Boundaries')
    hospitals_gdf.plot(ax=ax, color='red', markersize=10, alpha=0.7,
                       label='Hospitals')
    plt.title("South Carolina Hospitals and ZIP Code Boundaries")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.tight_layout()
    plt.savefig("axis_order_hospitals_map.png", dpi=150)
    plt.close()

    return count_inside

# Execute the solution
direct_solution()