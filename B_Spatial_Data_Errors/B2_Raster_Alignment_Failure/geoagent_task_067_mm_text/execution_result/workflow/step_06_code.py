from src.tools.raster_tools import terrain_derivative

# Compute Terrain Ruggedness Index (TRI) from merged DEM
# TRI = sqrt of sum of squared differences between each cell and its 8 neighbors
# Source DEM nodata: -32767.0 (preserved from source tiles)

dem_path = artifact_paths_by_name["merged_dem_richland.tif"]
tri_output = output_paths[0]

summary = terrain_derivative(
    input_raster=dem_path,
    output_path=tri_output,
    derivative="tri",
    band=1,
    nodata=-32767.0
)

print(json.dumps({
    "step_id": "step_05",
    "operation": "terrain_derivative",
    "derivative": "tri",
    "input": dem_path,
    "output": tri_output,
    "nodata_handled": -32767.0,
    "summary": summary
}, indent=2))