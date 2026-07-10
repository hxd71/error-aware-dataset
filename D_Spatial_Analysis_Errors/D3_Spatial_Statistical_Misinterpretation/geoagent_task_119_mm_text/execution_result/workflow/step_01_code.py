import json
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

# Load input points
input_path = asset_paths_by_id["points"]
gdf = gpd.read_file(input_path)

# Get CRS from input
input_crs = gdf.crs

# Group by Type field (cluster identifier)
clusters = gdf.groupby("Type")

# Prepare list to collect ellipse features
ellipse_records = []

for cluster_id, group in clusters:
    # Extract coordinates
    coords = np.array([(geom.x, geom.y) for geom in group.geometry])
    
    # Mean center
    cx = np.mean(coords[:, 0])
    cy = np.mean(coords[:, 1])
    
    # Standard deviations
    std_x = np.std(coords[:, 0])
    std_y = np.std(coords[:, 1])
    
    # Compute covariance matrix
    cov = np.cov(coords[:, 0], coords[:, 1])
    
    # Eigenvalues and eigenvectors for rotation angle
    eigenvalues, eigenvectors = np.linalg.eig(cov)
    
    # Rotation angle (angle of the major axis from x-axis)
    rotation_rad = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])
    rotation_deg = np.degrees(rotation_rad)
    
    # Semi-major and semi-minor axes (1-standard deviation ellipse)
    semi_major = np.sqrt(eigenvalues[0])
    semi_minor = np.sqrt(eigenvalues[1])
    
    # Ensure semi_major >= semi_minor
    if semi_major < semi_minor:
        semi_major, semi_minor = semi_minor, semi_major
        rotation_deg = (rotation_deg + 90.0) % 360.0
    
    # Generate ellipse polygon
    num_points = 72  # 5-degree increments
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    
    ellipse_x = cx + semi_major * np.cos(angles) * np.cos(rotation_rad) - semi_minor * np.sin(angles) * np.sin(rotation_rad)
    ellipse_y = cy + semi_major * np.cos(angles) * np.sin(rotation_rad) + semi_minor * np.sin(angles) * np.cos(rotation_rad)
    
    ellipse_coords = list(zip(ellipse_x, ellipse_y))
    ellipse_geom = Polygon(ellipse_coords)
    
    # Record with attributes
    ellipse_records.append({
        "cluster_id": int(cluster_id),
        "center_x": float(cx),
        "center_y": float(cy),
        "std_x": float(std_x),
        "std_y": float(std_y),
        "semi_major": float(semi_major),
        "semi_minor": float(semi_minor),
        "rotation_deg": float(rotation_deg),
        "geometry": ellipse_geom
    })

# Create GeoDataFrame with output
ellipse_gdf = gpd.GeoDataFrame(ellipse_records, crs=input_crs)

# Write output
output_path = output_paths[0]
ellipse_gdf.to_file(output_path)

# Execution summary
summary = {
    "step_id": "step_01",
    "ellipses_written": len(ellipse_gdf),
    "clusters_processed": len(list(clusters)),
    "output_crs": str(input_crs)
}
print(json.dumps(summary))