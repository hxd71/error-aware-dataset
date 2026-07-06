import geopandas as gpd
import rasterstats
import json

# Read input vector layer
vector_path = asset_paths_by_id['pa_fastfoods']
gdf = gpd.read_file(vector_path)

# Extract X/Y coordinates from point geometries (EPSG:4326: X=lon, Y=lat)
gdf['lon'] = gdf.geometry.x
gdf['lat'] = gdf.geometry.y

# Sample elevation from DEM raster at each point location
dem_path = asset_paths_by_id['pa_dem']
elevations = rasterstats.point_query(gdf.geometry.values, dem_path)
gdf['elevation'] = elevations

# Keep only original columns plus new lat, lon, elevation fields
original_cols = ['name', 'osm_id', 'type', 'geometry']
enriched_cols = original_cols + ['lat', 'lon', 'elevation']
gdf = gdf[enriched_cols]

# Write enriched vector output
output_path = output_paths[0]
gdf.to_file(output_path)

# Print execution summary
print(json.dumps({
    'step_id': 'step_01',
    'status': 'complete',
    'features_processed': len(gdf),
    'output_path': str(output_path)
}))