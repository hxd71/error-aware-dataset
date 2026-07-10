from src.tools.vector_tools import spatial_join_vectors
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Use the provided asset paths directly
counties_path = asset_paths_by_id["pennsylvaniacounties"]
fastfoods_path = asset_paths_by_id["pa_fastfoods"]
output_path = Path(output_paths[0])

# Step 1: Spatial join to find which fast food points fall within county polygons
# Using predicate 'within' since we want points that are contained by polygons
temp_joined = step_output_dir / "temp_spatial_join.geojson"
join_summary = spatial_join_vectors(
    counties_path,
    fastfoods_path,
    output_path=temp_joined,
    predicate="within"
)

# Step 2: Load joined result and count fast foods per county
joined_gdf = gpd.read_file(temp_joined)

# Count fast foods per county (using the county identifier field)
county_counts = (
    joined_gdf.groupby("NAME")
    .size()
    .reset_index(name="fastfood_count")
)

# Step 3: Merge counts back to original county polygons to preserve all counties
counties_gdf = gpd.read_file(counties_path)
counties_with_counts = counties_gdf.merge(
    county_counts,
    on="NAME",
    how="left"
)
counties_with_counts["fastfood_count"] = counties_with_counts["fastfood_count"].fillna(0).astype(int)

# Step 4: Write output with geometry preserved
counties_with_counts.to_file(output_path, driver="GeoJSON")

# Clean up temp file
temp_joined.unlink(missing_ok=True)

# Print execution summary
print(json.dumps({
    "step_id": "step_01",
    "operation": "spatial_join_count",
    "predicate": "within",
    "subject": "pennsylvaniacounties",
    "reference": "pa_fastfoods",
    "counties_processed": len(counties_with_counts),
    "fastfoods_joined": int(joined_gdf.shape[0]),
    "output_features": output_path.name,
    "count_field": "fastfood_count"
}, indent=2))