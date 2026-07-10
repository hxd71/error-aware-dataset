import geopandas as gpd
import shapely
import json

# Load the input vector
input_path = asset_paths_by_id["pacounties"]
gdf = gpd.read_file(input_path)

# Calculate geodesic boundary length using shapely's geodesic measurement
# Works directly on geographic coordinates (EPSG:4269 / NAD83)
def calculate_boundary_km(geometry):
    """Calculate geodesic boundary length in kilometers using shapely."""
    total_length = 0.0
    
    # Handle exterior boundary
    if hasattr(geometry, 'exterior') and geometry.exterior is not None:
        exterior_coords = list(geometry.exterior.coords)
        if len(exterior_coords) > 1:
            # Use shapely's geodesic length for the ring
            total_length += shapely.length(geometry.exterior)
    
    # Handle interior rings (holes)
    if hasattr(geometry, 'interiors'):
        for interior in geometry.interiors:
            if interior is not None:
                total_length += shapely.length(interior)
    
    return round(total_length / 1000.0, 3)

# Calculate geodesic boundary length for each feature
gdf["boundary_km"] = gdf["geometry"].apply(calculate_boundary_km)

# Verify all 67 features have valid lengths
valid_count = gdf["boundary_km"].notna().sum()
assert valid_count == 67, f"Expected 67 valid boundary lengths, got {valid_count}"

# Write output
output_path = output_paths[0]
gdf.to_file(output_path, driver="GPKG")

print(json.dumps({
    "step_id": "step_01",
    "input_features": len(gdf),
    "output_path": output_path,
    "boundary_km_min": float(gdf["boundary_km"].min()),
    "boundary_km_max": float(gdf["boundary_km"].max()),
    "new_field": "boundary_km"
}))
