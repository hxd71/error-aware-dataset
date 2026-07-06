import geopandas as gpd
import pandas as pd
import json

diff_path = artifact_paths_by_name["generated_polygon_diff.shp"]
counties_path = asset_paths_by_id["pacounties"]
output_path = output_paths[0]

gdf_diff = gpd.read_file(diff_path)
gdf_counties = gpd.read_file(counties_path)

merged_df = pd.concat([gdf_diff, gdf_counties], ignore_index=True)
merged_gdf = gpd.GeoDataFrame(merged_df, geometry="geometry")
merged_gdf.crs = "EPSG:4269"

merged_gdf.to_file(output_path)

print(json.dumps({"status": "success", "output": output_path, "feature_count": len(merged_gdf)}))