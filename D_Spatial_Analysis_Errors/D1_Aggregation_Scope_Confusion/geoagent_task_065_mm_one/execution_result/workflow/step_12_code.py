import json
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Paths from runtime bindings
counties_path = asset_paths_by_id["pennsylvaniacounties"]
csv_path = artifact_paths_by_name["county_tri_stats.csv"]
output_path = output_paths[0]

# Load counties shapefile
counties_gdf = gpd.read_file(counties_path)
print(f"Loaded {len(counties_gdf)} county features")
print(f"Counties CRS: {counties_gdf.crs}")
print(f"COUNTYFP dtype: {counties_gdf['COUNTYFP'].dtype}")

# Load TRI statistics CSV
tri_stats = pd.read_csv(csv_path)
print(f"Loaded {len(tri_stats)} TRI statistics rows")
print(f"CSV columns: {tri_stats.columns.tolist()}")
print(f"Sample join key values: {tri_stats['COUNTYFP'].head().tolist()}")

# Ensure join key types match (both should be string for reliable join)
counties_gdf['COUNTYFP'] = counties_gdf['COUNTYFP'].astype(str)
tri_stats['COUNTYFP'] = tri_stats['COUNTYFP'].astype(str)

# Perform attribute join on COUNTYFP
merged_gdf = counties_gdf.merge(tri_stats, on='COUNTYFP', how='left')
print(f"Merged features: {len(merged_gdf)}")
print(f"New columns added: {[c for c in merged_gdf.columns if c in ['mean_TRI', 'min_TRI', 'max_TRI', 'std_TRI']]}")

# Verify TRI statistics were joined
tri_fields = ['mean_TRI', 'min_TRI', 'max_TRI', 'std_TRI']
for field in tri_fields:
    if field in merged_gdf.columns:
        non_null = merged_gdf[field].notna().sum()
        print(f"  {field}: {non_null} non-null values")
    else:
        print(f"  WARNING: {field} not found in merged data")

# Export to Shapefile
merged_gdf.to_file(output_path)
print(f"Exported to: {output_path}")

# Summary
summary = {
    "step_id": "step_03",
    "operation": "attribute_join",
    "input_counties": len(counties_gdf),
    "input_csv_rows": len(tri_stats),
    "output_features": len(merged_gdf),
    "join_key": "COUNTYFP",
    "new_fields": tri_fields,
    "output_path": output_path
}
print(json.dumps(summary))