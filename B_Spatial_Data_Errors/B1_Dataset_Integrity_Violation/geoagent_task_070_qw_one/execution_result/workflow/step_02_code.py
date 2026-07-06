import geopandas as gpd
import json
from pathlib import Path

input_path = artifact_paths_by_name["nigeria_major_roads_26392.shp"]
output_path = Path(output_paths[0])

gdf = gpd.read_file(input_path)
total_length = float(gdf.geometry.length.sum())

output_path.write_text(str(total_length))

print(json.dumps({"status": "success", "total_length_meters": total_length}))