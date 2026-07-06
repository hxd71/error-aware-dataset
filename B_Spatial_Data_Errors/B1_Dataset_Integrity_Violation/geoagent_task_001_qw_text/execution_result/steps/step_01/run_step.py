import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"columbia_roads": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Columbia_school_walkability\\Columbia_road\\Columbia_roads.shp"}''')
current_step_assets_by_id = json.loads(r'''{"columbia_roads": {"asset_id": "columbia_roads", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Columbia_school_walkability\\Columbia_road\\Columbia_roads.shp", "role": "subject", "format": "shp", "crs": "EPSG:4326", "metadata": {"feature_count": 1349, "columns": ["fid", "type", "id", "bounds", "nodes", "tags"], "geometry_types": ["LineString"], "field_types": {"fid": "float64", "type": "str", "id": "str", "bounds": "str", "nodes": "str", "tags": "str"}, "sample_rows": [{"fid": 20.0, "type": "way", "id": "12508864", "bounds": "{'minlat': 33.999792, 'minlon': -81.0391124, 'maxlat': 34.001073, 'maxlon': -81.0385405}", "nodes": "113926532, 6848845064, 6848845065, 5020598255", "tags": "{'highway': 'tertiary', 'name': 'Lincoln Street', 'surface': 'paving_stones', 'tiger:cfcc': 'A41', 'tiger:county': 'Richland, SC', 'tiger:name_base': 'Lincoln', 'tiger:name_type': 'St', 'tiger:zip_left': '29201', 'tiger:zip_right': '29201'}"}, {"fid": 21.0, "type": "way", "id": "12508868", "bounds": "{'minlat': 33.9848053, 'minlon': -81.0318054, 'maxlat': 33.984987, 'maxlon': -81.0317191}", "nodes": "113926545, 1744552960", "tags": "{'highway': 'tertiary', 'name': 'Lincoln Street', 'oneway': 'yes', 'tiger:cfcc': 'A41', 'tiger:county': 'Richland, SC', 'tiger:name_base': 'Lincoln', 'tiger:name_type': 'St', 'tiger:reviewed': 'no', 'tiger:zip_left': '29201', 'tiger:zip_right': '29201'}"}, {"fid": 87.0, "type": "way", "id": "12510215", "bounds": "{'minlat': 33.9852327, 'minlon': -80.9847892, 'maxlat': 33.9855499, 'maxlon': -80.9831164}", "nodes": "113947093, 2959881852, 11047126249, 11047126248, 11047126247, 11047126246, 11047126245, 2959881851, 11047126244, 11047126243, 11047126242, 11047126256, 11047126255, 11047126254, 11047126253, 11047126252, 11047126257, 11047126251, 11047126250, 113947097,", "tags": "{'highway': 'residential', 'tiger:cfcc': 'A41', 'tiger:county': 'Richland, SC', 'tiger:reviewed': 'no'}"}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-81.0531543, 33.9712588, -80.9624157, 34.0290702]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260422T115149Z-1e0672b1-001-geoagent_001-try01\\steps\\step_01\\columbia_residential_roads.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260422T115149Z-1e0672b1-001-geoagent_001-try01\\steps\\step_01\\columbia_residential_roads.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import geopandas as gpd
import json
from pathlib import Path

input_path = asset_paths_by_id["columbia_roads"]
output_path = output_paths[0]

gdf = gpd.read_file(input_path)

def extract_highway(tag_str):
    try:
        d = json.loads(tag_str.replace("'", '"'))
        return d.get("highway")
    except (json.JSONDecodeError, AttributeError):
        return None

gdf["_highway"] = gdf["tags"].apply(extract_highway)
filtered_gdf = gdf[gdf["_highway"] == "residential"].drop(columns=["_highway"]).copy()

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
filtered_gdf.to_file(output_path)

print(json.dumps({
    "step": "step_01",
    "status": "success",
    "input_features": int(len(gdf)),
    "output_features": int(len(filtered_gdf)),
    "output_path": output_path
}))