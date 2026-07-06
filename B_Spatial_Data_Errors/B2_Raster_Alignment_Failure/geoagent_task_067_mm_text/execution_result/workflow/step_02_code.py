from src.tools.raster_tools import mosaic_rasters
import json

# Gather the four DEM tile paths from the asset catalog
raster_paths = [
    asset_paths_by_id["n33_w081_1arc_v3"],
    asset_paths_by_id["n33_w082_1arc_v3"],
    asset_paths_by_id["n34_w081_1arc_v3"],
    asset_paths_by_id["n34_w082_1arc_v3"]
]

# Mosaic adjacent tiles into a single merged raster
result = mosaic_rasters(
    raster_paths=raster_paths,
    output_path=output_paths[0],
    nodata=-32767
)

# Print execution summary
print(json.dumps({
    "step_id": "step_01",
    "operation": "mosaic_rasters",
    "input_count": len(raster_paths),
    "output_path": output_paths[0],
    "nodata": -32767
}, indent=2))