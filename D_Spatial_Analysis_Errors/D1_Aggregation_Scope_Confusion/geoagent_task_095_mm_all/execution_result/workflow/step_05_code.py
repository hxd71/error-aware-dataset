import geopandas as gpd
import pandas as pd
import json

# Read the spatial join result from step_01 artifacts
input_path = artifact_paths_by_name["stations_by_county.shp"]
gdf = gpd.read_file(input_path)

# Columns from spatial join: NAME_left (station), NAME_right (county), GEOID (county FIPS)
county_col = 'GEOID'
station_col = 'NAME_left'
county_name_col = 'NAME_right'

# Group by county (GEOID) and aggregate station names (pipe-separated)
grouped = gdf.groupby(county_col)[station_col].apply(lambda x: '|'.join(x.unique())).reset_index()

# Add county name for readability
geo_names = gdf[[county_col, county_name_col]].drop_duplicates()
grouped = grouped.merge(geo_names, on=county_col, how='left')

# Rename and reorder columns for output
grouped = grouped[[county_col, county_name_col, station_col]]
grouped.columns = ['county_geoid', 'county_name', 'station_names']

# Write summary CSV
output_path = output_paths[0]
grouped.to_csv(output_path, index=False)

# Print execution summary
summary = {
    'step_id': 'step_02',
    'status': 'success',
    'counties_processed': len(grouped),
    'total_stations': len(gdf),
    'output_file': output_path
}
print(json.dumps(summary))