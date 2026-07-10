import json
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Read the street view shapefile using runtime binding
input_path = Path(asset_paths_by_id["street_image"])
gdf = gpd.read_file(input_path)

# Build neighbor graph: map each panoId to its forward and backward neighbors
adjacency = {}
for _, row in gdf.iterrows():
    pano_id = row["panoId"]
    fwd = row["link_f_pan"] if pd.notna(row["link_f_pan"]) and row["link_f_pan"] else None
    bwd = row["link_b_pan"] if pd.notna(row["link_b_pan"]) and row["link_b_pan"] else None
    adjacency[pano_id] = {"forward": fwd, "backward": bwd}

# Write the graph to JSON using runtime output binding
output_path = step_output_dir / "pano_graph.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(adjacency, f, indent=2, ensure_ascii=False)

print(json.dumps({"step_id": "step_01", "status": "success", "nodes": len(adjacency), "output": str(output_path)}))