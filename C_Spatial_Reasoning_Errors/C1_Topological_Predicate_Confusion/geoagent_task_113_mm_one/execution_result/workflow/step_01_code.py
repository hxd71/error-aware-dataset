import json
from pathlib import Path
from src.tools.vector_tools import minimum_bounding_geometry, create_voronoi_polygons

# Input and output paths from runtime bindings
input_points = asset_paths_by_id["points"]
output_voronoi = output_paths[0]

# Create intermediate convex hull path in step output directory
step_dir = Path(step_output_dir)
convex_hull_path = step_dir / "convex_hull_boundary.shp"

# Step 1: Create convex hull boundary from input points
hull_summary = minimum_bounding_geometry(
    input_points,
    output_path=str(convex_hull_path),
    geometry_type="convex_hull"
)
print(json.dumps({"step": "convex_hull", "status": "success", "details": hull_summary}))

# Step 2: Create Voronoi polygons bounded by the convex hull
voronoi_summary = create_voronoi_polygons(
    input_points,
    output_path=output_voronoi,
    boundary_vector=str(convex_hull_path),
    target_crs=None
)
print(json.dumps({"step": "voronoi_polygons", "status": "success", "details": voronoi_summary}))

print(json.dumps({"step_id": "step_01", "status": "completed", "output_paths": [output_voronoi]}))