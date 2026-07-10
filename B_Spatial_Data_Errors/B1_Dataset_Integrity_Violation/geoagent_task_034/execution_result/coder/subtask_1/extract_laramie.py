
# -*- coding: utf-8 -*-
import os
import geopandas as gpd

# Define working directory
WORKING_DIRECTORY = os.getcwd()

# Paths
us_counties_path = os.path.join(WORKING_DIRECTORY, 'data', 'US_Counties.shp')
output_path = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1', 'Laramie_County.shp')

# Read the US Counties dataset
print(f"Reading US Counties from: {us_counties_path}")
counties = gpd.read_file(us_counties_path)
print(f"Total counties: {len(counties)}")

# Filter for Laramie County, Wyoming
# Using NAME for county and STATE_NAME for state
laramie_mask = (
    (counties['NAME'].str.strip().str.lower() == 'laramie') &
    (counties['STATE_NAME'].str.strip().str.lower() == 'wyoming')
)

laramie_county = counties[laramie_mask]

if len(laramie_county) == 0:
    raise ValueError(
        "Laramie County, Wyoming not found! "
        f"Available NAME values containing 'laramie': "
        f"{counties[counties['NAME'].str.contains('Laramie', case=False, na=False)]['NAME'].unique()}"
    )

print(f"\nExtracted Laramie County feature(s): {len(laramie_county)}")
print(f"Geometry type: {laramie_county.geometry.iloc[0].geom_type}")
print(f"CRS: {laramie_county.crs}")
print(f"Columns: {list(laramie_county.columns)}")

# Save to individual shapefile
os.makedirs(os.path.dirname(output_path), exist_ok=True)
laramie_county.to_file(output_path, encoding='utf-8')
print(f"\nSaved Laramie County boundary to: {output_path}")
print("Done!")
