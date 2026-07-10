from src.tools.raster_tools import terrain_derivative

dem_path = artifact_paths_by_name["merged_dem_richland.tif"]
output_path = output_paths[0]

summary = terrain_derivative(
    input_raster=dem_path,
    output_path=output_path,
    derivative="tpi",
    nodata=-32767.0
)

print(json.dumps({
    "step_id": "step_06",
    "operation": "terrain_derivative",
    "derivative": "tpi",
    "input": dem_path,
    "output": output_path,
    "nodata": -32767.0,
    "summary": summary
}))