import geopandas as gpd
import json

input_path = artifact_paths_by_name["building_centroids_with_elev.shp"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

# Identify columns
id_col = "id"
elev_col = "elevation" if "elevation" in gdf.columns else [c for c in gdf.columns if "elev" in c.lower() or c.lower() == "z"][0]

# Filter out nulls and DEM nodata (0.0)
mask = gdf[elev_col].notna() & (gdf[elev_col] != 0.0)
result = gdf.loc[mask, [id_col, elev_col]].copy()

result.to_csv(output_path, index=False)

print(json.dumps({"status": "success", "exported_rows": len(result), "output_path": output_path}))