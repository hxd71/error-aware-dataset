import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

def direct_solution():
    """
    For each zipcode area in South Carolina (SC), calculate the distance from the centroid of
    the zipcode area to its nearest hospital, and then create a choropleth map of zipcode area
    polygons coloured by distance (unit: km). Hospital locations are also shown.

    Inputs
    ------
    sc_zip_boundary.zip : path
        Zipped shapefile of SC zipcode boundaries (WGS84, EPSG:4326).
    SC_hospitals_with_emergency_room_cleaned.csv : path
        CSV file containing hospital locations with columns 'Longitude' and 'Latitude'.

    Outputs
    -------
    sc_hospital_distance_map.png : file
        Saved choropleth map (15x10 inches) showing zipcode distances to nearest hospital and
        hospital locations.
    """
    # File paths
    zip_boundary_path = (
        r"<LOCAL_REPO_ROOT>/external_task_runs/"
        r"data/llm_geo/hospital_accessibility_sc/sc_zip_boundary.zip"
    )
    hospital_csv_path = (
        r"<LOCAL_REPO_ROOT>/external_task_runs/"
        r"data/llm_geo/hospital_accessibility_sc/"
        r"SC_hospitals_with_emergency_room_cleaned.csv"
    )

    # Load zipcode polygons (WGS84)
    gdf_zip = gpd.read_file(zip_boundary_path)
    # Ensure CRS is set; if not, assume EPSG:4326
    if gdf_zip.crs is None:
        gdf_zip = gdf_zip.set_crs("EPSG:4326")

    # Load hospital data
    df_hosp = pd.read_csv(hospital_csv_path)
    # Drop rows with missing coordinates
    df_hosp = df_hosp.dropna(subset=['Longitude', 'Latitude'])
    # Create GeoDataFrame of hospitals
    gdf_hosp = gpd.GeoDataFrame(
        df_hosp,
        geometry=gpd.points_from_xy(df_hosp['Longitude'], df_hosp['Latitude']),
        crs="EPSG:4326"
    )

    # Reproject to a projected CRS suitable for distance measurement (NAD83 Conus Albers, meters)
    proj_crs = "EPSG:5070"
    gdf_zip_proj = gdf_zip.to_crs(proj_crs)
    gdf_hosp_proj = gdf_hosp.to_crs(proj_crs)

    # Create centroids of zipcode areas (as a separate geometry column)
    gdf_centroids = gdf_zip_proj.copy()
    gdf_centroids['centroid'] = gdf_centroids.geometry.centroid
    gdf_centroids = gdf_centroids.set_geometry('centroid')

    # Find nearest hospital for each centroid using nearest spatial join
    gdf_nearest = gpd.sjoin_nearest(
        gdf_centroids,
        gdf_hosp_proj,
        distance_col="dist_m"
    )
    # For ties, keep the minimum distance per centroid
    nearest_dist = gdf_nearest.groupby(gdf_nearest.index)['dist_m'].min()

    # Attach distance to original projected zipcode layer (units: meters)
    gdf_zip_proj['dist_km'] = nearest_dist / 1000.0

    # --- Map creation ---
    fig, ax = plt.subplots(figsize=(15, 10))
    # Plot zipcode polygons with distance choropleth
    gdf_zip_proj.plot(
        column='dist_km',
        ax=ax,
        legend=True,
        legend_kwds={'label': "Distance to Nearest Hospital (km)"},
        cmap='YlOrRd',
        edgecolor='black',
        linewidth=0.3,
        missing_kwds={'color': 'lightgrey', 'label': 'No hospital'}
    )
    # Overlay hospital points
    gdf_hosp_proj.plot(
        ax=ax,
        marker='+',
        color='blue',
        markersize=50,
        label='Hospital'
    )
    # Set map extent to SC zipcode bounds
    minx, miny, maxx, maxy = gdf_zip_proj.total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect('equal')
    ax.set_title("Distance from Zipcode Centroid to Nearest Hospital (South Carolina)", fontsize=14)
    ax.legend()
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig("sc_hospital_distance_map.png", dpi=300, bbox_inches='tight')
    plt.close()

# Execute the function
direct_solution()