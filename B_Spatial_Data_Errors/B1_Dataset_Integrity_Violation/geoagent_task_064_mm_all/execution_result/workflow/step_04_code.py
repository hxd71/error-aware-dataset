import json
import geopandas as gpd

# Use runtime bindings for input and output paths
input_path = artifact_paths_by_name["roads_with_length.shp"]
output_path = output_paths[0]

# Load the shapefile
gdf = gpd.read_file(input_path)

# Filter roads where METERS < 100
short_roads = gdf[gdf["METERS"] < 100]
short_roads_count = len(short_roads)

# Build the report
report = {
    "step_id": "step_03",
    "description": "Count of road features where Length < 100 meters",
    "filter_field": "METERS",
    "filter_threshold": 100,
    "filter_unit": "meters",
    "short_roads_count": short_roads_count,
    "total_roads": len(gdf),
    "percentage_short": round(short_roads_count / len(gdf) * 100, 2) if len(gdf) > 0 else 0
}

# Write the JSON report
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

# Print execution summary
print(json.dumps({"step_id": "step_03", "status": "success", "short_roads_count": short_roads_count, "output_path": output_path}))