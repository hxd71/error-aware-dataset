from pathlib import Path
import geopandas as gpd
import json

# Input path from runtime binding (use asset_paths_by_id)
input_path = r"[SECONDARY_RUN_WORKSPACE]\data\from_geo_agent\datasets\Street_tree\Richland_downtown_street_view_image_location_EPSG6569\Richland_downtown_street_view_image_location_EPSG6569.shp"

# Output path from runtime binding (use output_paths exactly as written)
output_path = r"[SECONDARY_RUN_WORKSPACE]\outputs\evaluations\from_geo_agent\eval-from-geo-agent-20260420T112719Z-2446843a\runs\eval-from-geo-agent-20260420T112719Z-2446843a-088-geoagent_088-try01\steps\step_01\filtered_points_2013_onward.shp"

# Read the source vector data
print(f"Reading input: {input_path}")
gdf = gpd.read_file(input_path)
print(f"Total features loaded: {len(gdf)}")

# Extract year from image_date (format is 'YYYY-M' like '2022-9')
# The year is the first 4 characters of the string
def extract_year(date_str):
    return int(str(date_str)[:4])

gdf['_extracted_year'] = gdf['image_date'].apply(extract_year)

# Explicit filtering predicate: year >= 2013
MINIMUM_YEAR = 2013
filtered_gdf = gdf[gdf['_extracted_year'] >= MINIMUM_YEAR].copy()

# Drop the temporary year column to preserve original attribute schema
filtered_gdf.drop(columns=['_extracted_year'], inplace=True)

print(f"Filtered features (year >= {MINIMUM_YEAR}): {len(filtered_gdf)}")

# Write the filtered result
filtered_gdf.to_file(output_path, driver='ESRI Shapefile')
print(f"Output written: {output_path}")

# Print execution summary as JSON
summary = {
    "step_id": "step_01",
    "input_features": int(len(gdf)),
    "output_features": int(len(filtered_gdf)),
    "filter_rule": "image_date year >= 2013",
    "output_path": output_path
}
print(json.dumps(summary))