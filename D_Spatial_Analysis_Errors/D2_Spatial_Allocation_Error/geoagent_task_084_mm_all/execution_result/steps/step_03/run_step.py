import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"rolla_building_footprints": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_building_footprints\\Rolla_building_footprints.shp", "rolla_downtown_block_groups_2019": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_downtown_block_groups_2019\\Rolla_downtown_block_groups_2019.shp"}''')
current_step_assets_by_id = json.loads(r'''{}''')
artifact_paths_by_name = json.loads(r'''{"bg_population_totals.csv": "[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_01\\bg_population_totals.csv", "buildings_with_bg_totals.shp": "[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_02\\buildings_with_bg_totals.shp"}''')
current_step_artifacts_by_name = json.loads(r'''{"buildings_with_bg_totals.shp": {"name": "buildings_with_bg_totals.shp", "path": "[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_02\\buildings_with_bg_totals.shp", "artifact_type": "vector", "description": ""}}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_03\\pop_rolla_buildings.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_03\\pop_rolla_buildings.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import json
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Read input buildings with block group totals
input_path = artifact_paths_by_name["buildings_with_bg_totals.shp"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)
print(f"Loaded {len(gdf)} buildings")
print(f"Columns: {gdf.columns.tolist()}")

# Identify block group ID column (cbfips appears to be the full block group GEOID)
# and sqft field for building area
# Find population total column (should be present from step_02 join)

bg_id_col = 'cbfips'
area_col = 'sqft'

# Find population total column - look for common patterns
pop_col = None
for col in gdf.columns:
    col_lower = col.lower()
    if 'pop' in col_lower and 'total' in col_lower:
        pop_col = col
        break
    elif col_lower == 'total_pop' or col_lower == 'bg_population' or col_lower == 'population':
        pop_col = col
        break

if pop_col is None:
    # Try to find column added by join that might contain population
    for col in gdf.columns:
        if 'pop' in col.lower() and gdf[col].dtype in ['int64', 'float64']:
            # Check if it varies by block group
            if gdf[col].std() > 0:
                pop_col = col
                break

if pop_col is None:
    raise ValueError(f"Could not identify population total column. Available numeric columns: {[c for c in gdf.columns if gdf[c].dtype in ['int64', 'float64']]}")

print(f"Using block_group_id column: {bg_id_col}")
print(f"Using area column: {area_col}")
print(f"Using population column: {pop_col}")

# Calculate sum of sqft per block group
bg_sums = gdf.groupby(bg_id_col)[area_col].sum().rename('bg_sum_sqft')
print(f"Found {len(bg_sums)} block groups")

# Merge sum back to buildings
gdf = gdf.merge(bg_sums, left_on=bg_id_col, right_index=True, how='left')

# Compute area-proportional population
# population = (building_sqft / sum_sqft_in_block_group) * total_population_in_block_group
gdf['population'] = (gdf[area_col] / gdf['bg_sum_sqft']) * gdf[pop_col]

# Prepare output with required fields
output_gdf = gdf.copy()
output_gdf['block_group_id'] = output_gdf[bg_id_col]
output_gdf['building_area'] = output_gdf[area_col]

# Keep essential columns plus computed population
keep_cols = ['block_group_id', 'building_area', 'population', 'geometry']
# Add any other columns that might be useful
for col in output_gdf.columns:
    if col not in keep_cols and col not in ['bg_sum_sqft']:
        keep_cols.append(col)

output_gdf = output_gdf[keep_cols]

# Write output
output_gdf.to_file(output_path)
print(f"Wrote {len(output_gdf)} features to {output_path}")
print(f"Population range: {output_gdf['population'].min():.2f} to {output_gdf['population'].max():.2f}")
print(f"Total population: {output_gdf['population'].sum():.2f}")

summary = {
    "step_id": "step_03",
    "operation": "area_proportional_population",
    "input_features": len(gdf),
    "output_features": len(output_gdf),
    "block_groups": len(bg_sums),
    "output_path": str(output_path)
}
print(json.dumps(summary, indent=2))
