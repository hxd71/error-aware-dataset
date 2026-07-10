import geopandas as gpd
import json

input_path = asset_paths_by_id["street_image"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

# Extract year from image_date (format 'YYYY-M')
gdf["year"] = gdf["image_date"].str.split("-").str[0].astype("Int32")

# Explicit filtering rule: retain only features with a successfully parsed year
gdf = gdf[gdf["year"].notna()].copy()
gdf["year"] = gdf["year"].astype(int)

gdf.to_file(output_path, driver="GeoJSON")

print(json.dumps({"status": "success", "output": output_path, "features": len(gdf)}))