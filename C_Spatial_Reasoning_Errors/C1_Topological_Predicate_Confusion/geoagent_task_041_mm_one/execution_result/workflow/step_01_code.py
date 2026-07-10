import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import json

# Read the circle polygon dataset
input_path = r"[SECONDARY_RUN_WORKSPACE]\data\from_geo_agent\datasets\Circle\Circle.shp"
gdf = gpd.read_file(input_path)

# Total points to generate
total_points = 20

# Calculate area for each polygon feature to distribute points proportionally
areas = gdf.geometry.area.values
total_area = areas.sum()

# Generate random points uniformly distributed within the polygon(s)
points = []
for idx, row in gdf.iterrows():
    polygon = row.geometry
    
    # Calculate number of points for this polygon (proportional to area)
    n_points = max(1, int(round(total_points * areas[idx] / total_area)))
    
    # Get the bounding box of the polygon
    minx, miny, maxx, maxy = polygon.bounds
    
    # Generate random points within bounding box and filter to polygon
    generated = 0
    max_attempts = n_points * 1000  # Prevent infinite loops
    attempts = 0
    
    while generated < n_points and attempts < max_attempts:
        attempts += 1
        # Uniform random point within bounding box
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        point = Point(x, y)
        
        if polygon.contains(point):
            points.append(point)
            generated += 1

# Create GeoDataFrame with the generated points
points_gdf = gpd.GeoDataFrame(geometry=points, crs=gdf.crs)

# Write output to the expected path
output_path = r"[SECONDARY_RUN_WORKSPACE]\outputs\runs\eval-from-geo-agent-20260423T184016Z-95a56beb-041-geoagent_041-try01\steps\step_01\random_points_in_circle.shp"
points_gdf.to_file(output_path)

# Print execution summary
summary = {
    "step_id": "step_01",
    "input_features": len(gdf),
    "output_points": len(points_gdf),
    "output_crs": str(gdf.crs),
    "output_path": output_path
}
print(json.dumps(summary))