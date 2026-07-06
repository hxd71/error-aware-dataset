import json
import rasterio

input_path = asset_paths_by_id["richland_dem"]
output_path = output_paths[0]

with rasterio.open(input_path) as src:
    profile = src.profile.copy()
    profile["crs"] = "EPSG:6569"
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(src.read())

print(json.dumps({"status": "success", "output": output_path, "crs": "EPSG:6569"}))