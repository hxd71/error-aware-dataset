
# -*- coding: utf-8 -*-
import os
import geopandas as gpd

WORKING_DIRECTORY = os.getcwd()

# Read US Counties
us_counties_path = os.path.join(WORKING_DIRECTORY, 'data', 'US_Counties.shp')
print(f"Reading: {us_counties_path}")

counties = gpd.read_file(us_counties_path)
print(f"Total features: {len(counties)}")
print(f"\nColumns ({len(counties.columns)}):")
for i, col in enumerate(counties.columns):
    dtype = counties[col].dtype
    sample = counties[col].iloc[0] if len(counties) > 0 else 'N/A'
    print(f"  [{i}] {col}  (dtype={dtype})  sample={sample!r}")

print(f"\nCRS: {counties.crs}")
print(f"\nGeometry type: {counties.geometry.geom_type.unique()}")

# Print first 5 rows of all columns
print("\n=== First 5 rows ===")
print(counties.head(5).to_string())

# Search for "Laramie" or "laramie" in all string columns
print("\n=== Searching for 'Laramie' ===")
for col in counties.columns:
    if counties[col].dtype == 'object':
        mask = counties[col].astype(str).str.contains('Laramie', case=False, na=False)
        if mask.any():
            print(f"\nFound in column '{col}':")
            print(counties[mask].to_string())

# Also search for "WY" or "Wyoming"
print("\n=== Searching for Wyoming/WY ===")
for col in counties.columns:
    if counties[col].dtype == 'object':
        mask = counties[col].astype(str).str.upper().isin(['WY', 'WYOMING', '56'])
        if mask.any():
            print(f"\nWyoming found in column '{col}', count={mask.sum()}")
            wy_data = counties[mask]
            print(wy_data.head(3).to_string())
