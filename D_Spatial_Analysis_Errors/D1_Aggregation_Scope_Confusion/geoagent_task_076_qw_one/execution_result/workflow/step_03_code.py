import json
import geopandas as gpd
import pandas as pd

input_path = artifact_paths_by_name["coffee_shops_stop_counts.shp"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

# Ensure stop_count is numeric for correct descending sort
gdf["stop_count"] = pd.to_numeric(gdf["stop_count"], errors="coerce")

# Explicit filtering rule: retain the 20 features with the highest stop_count values
top20_gdf = gdf.sort_values(by="stop_count", ascending=False).head(20)

top20_gdf.to_file(output_path)

print(json.dumps({"step_id": "step_03", "status": "success", "input_features": len(gdf), "output_features": len(top20_gdf)}))