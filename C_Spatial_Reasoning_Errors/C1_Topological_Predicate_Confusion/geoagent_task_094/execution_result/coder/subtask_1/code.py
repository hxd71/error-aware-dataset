# -*- coding: utf-8 -*-
"""
Find all roads from tl_2019_42_prisecroads.shp that cross Centre County,
and save them as a new shapefile in coder/subtask_1/.
"""

import os
import geopandas as gpd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()

ROADS_PATH = os.path.join(
    WORKING_DIRECTORY,
    'data', 'tl_2019_42_prisecroads', 'tl_2019_42_prisecroads.shp'
)
COUNTIES_PATH = os.path.join(
    WORKING_DIRECTORY,
    'data', 'PennsylvaniaCounties', 'PennsylvaniaCounties.shp'
)
OUTPUT_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'centre_county_roads.shp')

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Load Pennsylvania counties and isolate Centre County
# ---------------------------------------------------------------------------
print("Loading Pennsylvania counties...")
counties = gpd.read_file(COUNTIES_PATH)
print(f"  Found {len(counties)} county/ies. Columns: {list(counties.columns)}")

# Look for Centre County – the field name might vary (NAME, COUNTY_NAM, etc.)
# Let's inspect and find the correct column
centre_mask = None
for col in counties.columns:
    # Try a case-insensitive match
    sample_vals = counties[col].astype(str).str.strip().str.lower().unique()
    if 'centre' in sample_vals:
        centre_mask = counties[col].astype(str).str.strip().str.lower() == 'centre'
        print(f"  Found 'Centre' in column '{col}'")
        break

if centre_mask is None:
    # Fallback: print all unique values to help diagnose
    print("  Could not find 'Centre' by name search. Printing all columns and unique values:")
    for col in counties.columns:
        print(f"    {col}: {list(counties[col].unique()[:20])}")
    raise ValueError("Could not locate Centre County in the counties shapefile.")

centre_county = counties[centre_mask].copy()
print(f"  Centre County selected: {len(centre_county)} polygon(s)")

# ---------------------------------------------------------------------------
# 2. Load the roads shapefile
# ---------------------------------------------------------------------------
print("Loading tl_2019_42_prisecroads...")
roads = gpd.read_file(ROADS_PATH)
print(f"  Found {len(roads)} road segments. CRS: {roads.crs}")

# ---------------------------------------------------------------------------
# 3. Align CRS if needed
# ---------------------------------------------------------------------------
if roads.crs != centre_county.crs:
    print(f"  Reprojecting Centre County from {centre_county.crs} to {roads.crs}...")
    centre_county = centre_county.to_crs(roads.crs)

# ---------------------------------------------------------------------------
# 4. Spatial intersection – roads that cross Centre County
# ---------------------------------------------------------------------------
print("Performing spatial intersection...")
# Use 'intersects' which includes crossing, touching, and overlapping
centre_roads = gpd.sjoin(
    roads,
    centre_county[['geometry']],
    how='inner',
    predicate='intersects'
)

# Drop the index_right column added by sjoin
if 'index_right' in centre_roads.columns:
    centre_roads = centre_roads.drop(columns=['index_right'])

# Also drop any duplicate geometries that may result from multi-polygon joins
centre_roads = centre_roads.drop_duplicates(subset=['LINEARID'])

print(f"  {len(centre_roads)} road segments intersect Centre County.")

# ---------------------------------------------------------------------------
# 5. Save to shapefile
# ---------------------------------------------------------------------------
print(f"Saving to {OUTPUT_PATH}...")
centre_roads.to_file(OUTPUT_PATH, driver='ESRI Shapefile', encoding='utf-8')
print("Done!")
