import geopandas as gpd
import json

buffer_path = artifact_paths_by_name["coffee_shops_buffer_600ft.shp"]
stops_path = asset_paths_by_id["bus_metro_stop_epsg6535"]
out_path = output_paths[0]

buffers = gpd.read_file(buffer_path)
stops = gpd.read_file(stops_path)

if buffers.crs != stops.crs:
    stops = stops.to_crs(buffers.crs)

inner_join = gpd.sjoin(stops, buffers, how="inner", predicate="intersects")
counts = inner_join.groupby("index_right").size().reset_index(name="stop_count")

result = buffers.merge(counts, left_index=True, right_on="index_right", how="left")
result["stop_count"] = result["stop_count"].fillna(0).astype(int)
result.drop(columns=["index_right"], errors="ignore", inplace=True)

result.to_file(out_path)
print(json.dumps({"status": "success", "output": out_path, "features": len(result)}))