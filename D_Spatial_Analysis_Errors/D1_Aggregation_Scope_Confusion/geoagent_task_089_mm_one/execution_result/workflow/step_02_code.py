from pathlib import Path
import geopandas as gpd
import pandas as pd

# Input paths from runtime bindings
buffer_path = artifact_paths_by_name["street_buffers_20m.geojson"]
tree_path = asset_paths_by_id["street_tree_epsg6852_subset"]

# Output paths
output_geojson = output_paths[0]
output_csv = output_paths[1]

# Read inputs
buffers = gpd.read_file(buffer_path)
trees = gpd.read_file(tree_path)

# Ensure both are in the same CRS (buffers may inherit CRS from GeoJSON, trees are EPSG:6852)
if buffers.crs is None:
    buffers = buffers.set_crs(trees.crs, allow_override=True)
elif buffers.crs != trees.crs:
    buffers = buffers.to_crs(trees.crs)

# Spatial join: count trees that intersect each buffer polygon
# Using predicate 'within' from tree perspective (points within polygons)
joined = gpd.sjoin(trees, buffers, how="left", predicate="within")

# Count trees per buffer index and merge back
tree_counts = joined.groupby("index_right").size().reset_index(name="tree_count")

# Get original buffer geometries and merge counts
buffers_enriched = buffers.copy()
buffers_enriched = buffers_enriched.reset_index(drop=True)
buffers_enriched["tree_count"] = 0  # Initialize

# Map counts back to buffers by position
for _, row in tree_counts.iterrows():
    idx = int(row["index_right"])
    buffers_enriched.loc[idx, "tree_count"] = int(row["tree_count"])

# Keep only the 'id' field from original buffers plus tree_count
# Drop 'index_right' if it exists from the sjoin operation
cols_to_keep = [c for c in buffers_enriched.columns if c not in ["index_right", "index_left"]]
buffers_final = buffers_enriched[cols_to_keep]

# Write outputs
buffers_final.to_file(output_geojson, driver="GeoJSON")
buffers_final.drop(columns="geometry").to_csv(output_csv, index=False)

print(json.dumps({
    "step_id": "step_02",
    "status": "success",
    "buffers_enriched": len(buffers_final),
    "total_trees_counted": int(buffers_final["tree_count"].sum()),
    "outputs": [output_geojson, output_csv]
}))