import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# Provided functions (adapted to avoid undefined default args)
# ------------------------------------------------------------

def load_zipcodes(zip_shp_path=r'<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\hospital_accessibility_sc\sc_zip_boundary.zip'):
    """
    Load SC zipcode shapefile into a GeoDataFrame.
    """
    zipcodes_gdf = gpd.read_file(zip_shp_path)
    return zipcodes_gdf


def load_hospitals_as_gdf(hospitals_csv_path=r'<LOCAL_REPO_ROOT>\external_task_runs\data\llm_geo\hospital_accessibility_sc\SC_hospitals_with_emergency_room_cleaned.csv'):
    """
    Load hospitals CSV, create GeoDataFrame with point geometry from Longitude/Latitude.
    """
    df = pd.read_csv(hospitals_csv_path)
    df = df.dropna(subset=['Longitude', 'Latitude'])
    hospitals_gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
        crs='EPSG:4326'
    )
    return hospitals_gdf


def reproject_zipcodes(zipcodes_gdf):
    """
    Reproject zipcodes to NAD83 / South Carolina (EPSG:32133) for accurate distance calculation.
    """
    zipcodes_proj = zipcodes_gdf.to_crs(epsg=32133)
    return zipcodes_proj


def reproject_hospitals(hospitals_gdf):
    """
    Reproject hospitals to NAD83 / South Carolina (EPSG:32133)
    """
    hospitals_proj = hospitals_gdf.to_crs('EPSG:32133')
    return hospitals_proj


def compute_centroids(zipcodes_proj):
    """
    Create a GeoDataFrame of zipcode centroids, retaining all attributes.
    """
    centroids_gdf = zipcodes_proj.copy()
    centroids_gdf['geometry'] = centroids_gdf['geometry'].centroid
    return centroids_gdf


def sjoin_nearest_hospital(hospitals_proj, centroids_gdf):
    """
    For each centroid, find nearest hospital and calculate distance in kilometers.
    Returns centroids GeoDataFrame with 'dist_km' column.
    """
    # Nearest spatial join (distance in meters, CRS EPSG:32133)
    nearest = gpd.sjoin_nearest(
        centroids_gdf,
        hospitals_proj,
        distance_col="dist",
        lsuffix="centroid",
        rsuffix="hospital"
    )
    # Keep minimum distance per centroid (in case of ties)
    nearest_dist_m = nearest.groupby(nearest.index)['dist'].min()
    nearest_dist_km = nearest_dist_m / 1000.0

    centroids_with_distance_km = centroids_gdf.copy()
    centroids_with_distance_km['dist_km'] = centroids_with_distance_km.index.map(nearest_dist_km)
    return centroids_with_distance_km


def merge_dist_to_zipcodes(zipcodes_proj, centroids_with_distance_km):
    """
    Join the computed distance (by ZIPCODE) to the projected zipcode polygons.
    """
    dist_map = centroids_with_distance_km.set_index('ZIPCODE')['dist_km']
    zipcodes_with_dist = zipcodes_proj.copy()
    zipcodes_with_dist['dist_km'] = zipcodes_with_dist['ZIPCODE'].map(dist_map)
    zipcodes_with_dist = zipcodes_with_dist.dropna(subset=['dist_km']).reset_index(drop=True)
    return zipcodes_with_dist


def plot_map(hospitals_proj, zipcodes_with_dist):
    """
    Create choropleth map of distance (km) to nearest hospital, with hospital points overlaid.
    Returns the figure.
    """
    plot_gdf = zipcodes_with_dist.dropna(subset=['dist_km']).copy()
    fig, ax = plt.subplots(figsize=(15, 10))
    plot_gdf.plot(
        column='dist_km',
        cmap='viridis',
        legend=True,
        legend_kwds={'label': 'Distance (km)', 'orientation': 'vertical'},
        ax=ax,
        edgecolor='black',
        linewidth=0.3
    )
    hospitals_proj.plot(
        ax=ax,
        color='red',
        markersize=20,
        marker='o',
        label='Hospital',
        zorder=5
    )
    ax.legend(loc='lower right', fontsize=10)
    ax.set_title('Distance to Nearest Hospital (km)\nSouth Carolina Zipcode Areas', fontsize=16, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    return fig


# ------------------------------------------------------------
# Main solution function
# ------------------------------------------------------------

def assembely_solution():
    # Step 1: Load data
    zipcodes_gdf = load_zipcodes()
    hospitals_gdf = load_hospitals_as_gdf()

    # Step 2: Reproject to a projected CRS (meters)
    zipcodes_proj = reproject_zipcodes(zipcodes_gdf)
    hospitals_proj = reproject_hospitals(hospitals_gdf)

    # Step 3: Compute centroids of zipcode areas
    centroids_gdf = compute_centroids(zipcodes_proj)

    # Step 4: Find distance to nearest hospital for each centroid
    centroids_with_dist = sjoin_nearest_hospital(hospitals_proj, centroids_gdf)

    # Step 5: Attach distances to the original projected polygons
    zipcodes_with_dist = merge_dist_to_zipcodes(zipcodes_proj, centroids_with_dist)

    # Step 6: Create the choropleth map
    fig = plot_map(hospitals_proj, zipcodes_with_dist)

    # Step 7: Save the final map
    plt.savefig('distance_to_nearest_hospital_map.png')
    # Optionally close the figure to free memory
    plt.close(fig)


# Execute the solution
assembely_solution()