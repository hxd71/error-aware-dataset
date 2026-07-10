import geopandas as gpd
import json

counties_path = asset_paths_by_id['pacounties']
points_path = asset_paths_by_id['pa_data_epsg4326']
output_path = output_paths[0]

counties = gpd.read_file(counties_path)
points = gpd.read_file(points_path)

# Handle CRS difference: reproject points to match counties
points = points.to_crs(counties.crs)

# Spatial join using 'within' predicate (points within counties)
joined = gpd.sjoin(points, counties, predicate='within')

# Aggregate counts per county
point_counts = joined.groupby('index_right').size().rename('point_count')

# Merge counts back to original county dataframe
counties = counties.join(point_counts)
counties['point_count'] = counties['point_count'].fillna(0).astype(int)

# Write output
counties.to_file(output_path)

print(json.dumps({"status": "success", "output": output_path, "feature_count": len(counties)}))