import geopandas as gpd
import pandas as pd
from rasterstats import point_query
import json

# Read checkpoint points (vector)
checkpoints_path = asset_paths_by_id["checkpoints_columbia"]
gdf = gpd.read_file(checkpoints_path)

# DEM raster path
dem_path = asset_paths_by_id["richland_dem_epsg_6569"]

# Sample raster values at each point location using point_query
elevation_values = point_query(
    gdf.geometry.values,
    dem_path,
    nodata=True
)

# Create result dataframe with id and extracted elevation
result_df = pd.DataFrame({
    "id": gdf["id"].values,
    "elevation": elevation_values
})

# Write output CSV to provided output path
output_path = output_paths[0]
result_df.to_csv(output_path, index=False)

# Print execution summary
print(json.dumps({
    "step_id": "step_02",
    "sampled_points": len(result_df),
    "valid_elevations": int(result_df["elevation"].notna().sum()),
    "output_path": str(output_path)
}))