import json
import geopandas as gpd
import rasterio

# Input paths from runtime bindings
checkpoint_path = asset_paths_by_id["checkpoints_columbia"]
raster_path = asset_paths_by_id["idw_output"]
output_path = output_paths[0]

# Load checkpoint points
print(f"Loading checkpoints from: {checkpoint_path}")
gdf = gpd.read_file(checkpoint_path)
print(f"Loaded {len(gdf)} checkpoint points (CRS: {gdf.crs})")

# Sample raster values at each point location
print(f"Sampling raster: {raster_path}")
with rasterio.open(raster_path) as src:
    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    sampled = list(src.sample(coords))

# Extract values and add to dataframe
gdf['elevation'] = [val[0] for val in sampled]

# Export to CSV with required columns using pandas directly
print(f"Exporting to CSV: {output_path}")
gdf[['id', 'elevation']].to_csv(output_path, index=False)

print(json.dumps({
    "step_id": "step_01",
    "operation": "raster_point_sampling",
    "samples_extracted": len(gdf),
    "output": output_path
}))
