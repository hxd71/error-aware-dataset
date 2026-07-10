import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"street_image": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_view_image\\street_image\\street_image.shp"}''')
current_step_assets_by_id = json.loads(r'''{"street_image": {"asset_id": "street_image", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_view_image\\street_image\\street_image.shp", "role": "subject", "format": "shp", "crs": "EPSG:4326", "metadata": {"feature_count": 7959, "columns": ["image_widt", "image_heig", "tile_width", "tile_heigh", "image_date", "imagery_ty", "projection", "pano_yaw_d", "tilt_yaw_d", "tilt_pitch", "panoId", "zoomLevels", "lat", "lng", "original_l", "original_1", "elevation_", "descriptio", "streetRang", "region", "country", "elevatio_1", "links_cnt", "link_forwa", "link_f_pan", "link_f_roa", "link_f_des", "link_backw", "link_b_pan", "link_b_roa", "link_b_des", "link_other", "year"], "geometry_types": ["Point"], "field_types": {"image_widt": "int64", "image_heig": "int64", "tile_width": "int64", "tile_heigh": "int64", "image_date": "str", "imagery_ty": "int64", "projection": "str", "pano_yaw_d": "float64", "tilt_yaw_d": "float64", "tilt_pitch": "float64", "panoId": "str", "zoomLevels": "float64", "lat": "float64", "lng": "float64", "original_l": "float64", "original_1": "float64", "elevation_": "float64", "descriptio": "str", "streetRang": "float64", "region": "str", "country": "str", "elevatio_1": "float64", "links_cnt": "float64", "link_forwa": "float64", "link_f_pan": "str", "link_f_roa": "float64", "link_f_des": "str", "link_backw": "float64", "link_b_pan": "str", "link_b_roa": "float64", "link_b_des": "str", "link_other": "str", "year": "int32"}, "sample_rows": [{"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 182.9423980712891, "tilt_yaw_d": 88.7552719116211, "tilt_pitch": 0.832933723926544, "panoId": "5b9gMwpqVNvBTRryCLZYpw", "zoomLevels": NaN, "lat": 34.00084698505906, "lng": -81.00533150636781, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "828 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 93.14770507812499, "links_cnt": 2.0, "link_forwa": 185.1232604980469, "link_f_pan": "5TiuLOLcYyCKAxWRe0K-sg", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.124769687652588, "link_b_pan": "NYP6vcGQ_cLKiBI6Ycea8g", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 184.2658996582031, "tilt_yaw_d": 88.7352066040039, "tilt_pitch": 0.80227267742157, "panoId": "5TiuLOLcYyCKAxWRe0K-sg", "zoomLevels": NaN, "lat": 34.00075797525222, "lng": -81.00533900842878, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "828 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 92.95042419433594, "links_cnt": 2.0, "link_forwa": 185.0914001464844, "link_f_pan": "P8Sz93OClpo3M5IF7RhiWw", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.123254776000978, "link_b_pan": "5b9gMwpqVNvBTRryCLZYpw", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 185.6534423828125, "tilt_yaw_d": 88.75499725341797, "tilt_pitch": 0.59730589389801, "panoId": "P8Sz93OClpo3M5IF7RhiWw", "zoomLevels": NaN, "lat": 34.000667807799, "lng": -81.00534912356608, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "822 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 92.74822998046876, "links_cnt": 2.0, "link_forwa": 185.1199798583984, "link_f_pan": "WrtBzm6Ll0x-_rHzkwj3rA", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.091405391693116, "link_b_pan": "5TiuLOLcYyCKAxWRe0K-sg", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-81.01085594896888, 33.97913492079225, -80.98747947168117, 34.00084698505906]}}}''')
artifact_paths_by_name = json.loads(r'''{"pano_graph.json": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_01\\pano_graph.json"}''')
current_step_artifacts_by_name = json.loads(r'''{"pano_graph.json": {"name": "pano_graph.json", "path": "[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_01\\pano_graph.json", "artifact_type": "json", "description": ""}}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_02\\street_paths.geojson"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_02\\street_paths.geojson"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

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