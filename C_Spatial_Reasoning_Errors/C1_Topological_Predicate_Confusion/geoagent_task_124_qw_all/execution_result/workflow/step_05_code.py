import geopandas as gpd
import json

input_path = current_step_assets_by_id["circles"]["path"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

inter = gpd.overlay(gdf, gdf, how="intersection")

id_cols = [c for c in inter.columns if c.startswith("ID_")]
if len(id_cols) >= 2:
    overlap = inter[inter[id_cols[0]] != inter[id_cols[1]]].copy()
else:
    overlap = inter.copy()

overlap = overlap.drop_duplicates(subset="geometry")

if overlap.crs is None:
    overlap = overlap.set_crs(gdf.crs)

overlap.to_file(output_path)

print(json.dumps({"status": "success", "count": len(overlap), "output": output_path}))