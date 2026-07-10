import json
from pathlib import Path
from src.tools.vector_tools import reproject_vector, add_geometry_fields

# Step 1: Reproject building polygons from EPSG:4326 to EPSG:2272 (NAD83 Pennsylvania State Plane South, US feet)
# EPSG:2272 is appropriate for accurate area calculation in Pennsylvania
reproject_summary = reproject_vector(
    asset_paths_by_id["penn_state_buildings"],
    output_path=output_paths[0],
    target_crs="EPSG:2272"
)

# Step 2: Add planar area field using the projected CRS for accurate metric/imperial area calculation
add_geometry_summary = add_geometry_fields(
    output_paths[0],
    output_path=output_paths[0],
    area_field="planar_area",
    target_crs="EPSG:2272"
)

# Print execution summary
summary = {
    "step_id": "step_01",
    "operation": "reproject_and_calculate_area",
    "source_crs": "EPSG:4326",
    "target_crs": "EPSG:2272",
    "area_field": "planar_area",
    "reproject_result": reproject_summary,
    "geometry_fields_result": add_geometry_summary,
    "output_path": str(output_paths[0])
}
print(json.dumps(summary))