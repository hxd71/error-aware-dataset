import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
from pathlib import Path

# Load the street panorama points shapefile
input_path = asset_paths_by_id["street_image"]
gdf = gpd.read_file(input_path)
print(f"Loaded {len(gdf)} points from street_image")

# Build lookup dictionaries: panoId -> row data
pano_data = {}  # panoId -> (lng, lat)
forward_links = {}  # panoId -> forward neighbor panoId
backward_links = {}  # panoId -> backward neighbor panoId
forward_streets = {}  # panoId -> forward street name
backward_streets = {}  # panoId -> backward street name

for _, row in gdf.iterrows():
    pano_id = row["panoId"]
    if not pano_id or (isinstance(pano_id, float) and pd.isna(pano_id)):
        continue
    
    lat = row["lat"]
    lng = row["lng"]
    
    if pd.isna(lat) or pd.isna(lng):
        continue
    
    pano_data[pano_id] = (lng, lat)  # (x=lng, y=lat) for LineString
    
    # Forward link
    f_pan = row["link_f_pan"]
    if f_pan and not (isinstance(f_pan, float) and pd.isna(f_pan)):
        forward_links[pano_id] = f_pan
        f_des = row["link_f_des"]
        if f_des and not (isinstance(f_des, float) and pd.isna(f_des)):
            forward_streets[pano_id] = f_des
    
    # Backward link
    b_pan = row["link_b_pan"]
    if b_pan and not (isinstance(b_pan, float) and pd.isna(b_pan)):
        backward_links[pano_id] = b_pan
        b_des = row["link_b_des"]
        if b_des and not (isinstance(b_des, float) and pd.isna(b_des)):
            backward_streets[pano_id] = b_des

print(f"Built graph with {len(pano_data)} nodes")

MAX_PATH_LENGTH = 10000  # Safety cap

def trace_forward(start_id, forward_links, backward_links, pano_data, path_visited):
    """Trace forward from start through link_f_pan until dead-end."""
    coords = []
    current = start_id
    iteration = 0
    
    while current and current in forward_links and iteration < MAX_PATH_LENGTH:
        next_id = forward_links[current]
        
        # Cycle detection - stop if we've seen this node in this path
        if next_id in path_visited:
            break
        
        if next_id not in pano_data:
            break
        
        path_visited.add(next_id)
        coords.append(pano_data[next_id])
        
        # Cycle detection - stop if backward link points back into our path
        if current in backward_links and backward_links[current] in path_visited:
            break
        
        current = next_id
        iteration += 1
    
    return coords, current

def trace_backward(start_id, forward_links, backward_links, pano_data, path_visited):
    """Trace backward from start through link_b_pan until dead-end."""
    coords = []
    current = start_id
    iteration = 0
    
    while current and current in backward_links and iteration < MAX_PATH_LENGTH:
        prev_id = backward_links[current]
        
        # Cycle detection - stop if we've seen this node in this path
        if prev_id in path_visited:
            break
        
        if prev_id not in pano_data:
            break
        
        path_visited.add(prev_id)
        coords.append(pano_data[prev_id])
        
        # Cycle detection - stop if forward link points back into our path
        if current in forward_links and forward_links[current] in path_visited:
            break
        
        current = prev_id
        iteration += 1
    
    return coords, current

def build_path(start_id, forward_links, backward_links, pano_data):
    """Build complete path by tracing forward then backward. Returns (coords, path_visited)."""
    # Get start coordinate
    if start_id not in pano_data:
        return None, set()
    
    # Create a path-specific visited set for cycle detection
    path_visited = {start_id}
    
    # Start with start point
    start_coords = [pano_data[start_id]]
    
    # Trace forward
    forward_coords, forward_end = trace_forward(start_id, forward_links, backward_links, pano_data, path_visited)
    
    # Trace backward from forward end
    backward_coords, _ = trace_backward(forward_end, forward_links, backward_links, pano_data, path_visited)
    
    # Combine: backward (reversed) + start + forward
    full_coords = list(reversed(backward_coords)) + start_coords + forward_coords
    
    # Remove duplicates that might occur at junction points
    if len(full_coords) >= 2:
        cleaned = [full_coords[0]]
        for coord in full_coords[1:]:
            if coord != cleaned[-1]:
                cleaned.append(coord)
        full_coords = cleaned
    
    return full_coords, path_visited

# Trace all paths
visited = set()
paths = []
path_count = 0
total_iterations = 0
MAX_TOTAL_ITERATIONS = 200000  # Safety cap for outer loop

for pano_id in list(pano_data.keys()):
    total_iterations += 1
    if total_iterations > MAX_TOTAL_ITERATIONS:
        print(f"Reached max iterations cap, stopping traversal")
        break
    
    if pano_id in visited:
        continue
    
    # Check if this node has any connections
    has_forward = pano_id in forward_links and forward_links[pano_id] in pano_data
    has_backward = pano_id in backward_links and backward_links[pano_id] in pano_data
    
    if not has_forward and not has_backward:
        # Isolated point - skip
        visited.add(pano_id)  # Mark to avoid reprocessing
        continue
    
    # Build path
    coords, path_visited = build_path(pano_id, forward_links, backward_links, pano_data)
    
    if coords and len(coords) >= 2:
        path_count += 1
        
        # Determine dominant street name
        street_name = None
        for node in list(path_visited)[:20]:
            if node in forward_streets:
                street_name = forward_streets[node]
                break
            if node in backward_streets:
                street_name = backward_streets[node]
                break
        
        paths.append({
            "street_name": street_name,
            "node_count": len(coords),
            "start_pano": pano_id,
            "_path_visited": path_visited  # Temporary for marking
        })
    
    # Mark all visited nodes
    visited.update(path_visited)
    
    if path_count % 100 == 0 and path_count > 0:
        print(f"Processed {total_iterations} nodes, found {path_count} paths")

print(f"Found {path_count} connected paths from {total_iterations} iterations")

# Create GeoDataFrame with LineStrings
output_path = output_paths[0]

# Clean up temporary field
for p in paths:
    del p["_path_visited"]

if paths:
    geometries = []
    
    for path_info in paths:
        start_id = path_info["start_pano"]
        coords, _ = build_path(start_id, forward_links, backward_links, pano_data)
        if coords and len(coords) >= 2:
            geometries.append(LineString(coords))
        else:
            # Fallback - should not happen but safety check
            geometries.append(LineString([pano_data[start_id], pano_data[start_id]]))
    
    result_gdf = gpd.GeoDataFrame(paths, geometry=geometries, crs="EPSG:4326")
    result_gdf = result_gdf[["street_name", "node_count", "start_pano", "geometry"]]
    result_gdf.to_file(output_path, driver="GeoJSON")
    print(f"Wrote {len(result_gdf)} street paths to {output_path}")
else:
    # Create empty result
    result_gdf = gpd.GeoDataFrame(columns=["street_name", "node_count", "start_pano", "geometry"], geometry="geometry", crs="EPSG:4326")
    result_gdf.to_file(output_path, driver="GeoJSON")
    print(f"No paths found - wrote empty GeoJSON to {output_path}")

print(json.dumps({
    "step_id": "step_02",
    "input_points": len(gdf),
    "graph_nodes": len(pano_data),
    "paths_created": path_count,
    "total_iterations": total_iterations,
    "output_path": output_path
}))