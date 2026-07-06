import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"street_image": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_view_image\\street_image\\street_image.shp"}''')
current_step_assets_by_id = json.loads(r'''{"street_image": {"asset_id": "street_image", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_view_image\\street_image\\street_image.shp", "role": "subject", "format": "shp", "crs": "EPSG:4326", "metadata": {"feature_count": 7959, "columns": ["image_widt", "image_heig", "tile_width", "tile_heigh", "image_date", "imagery_ty", "projection", "pano_yaw_d", "tilt_yaw_d", "tilt_pitch", "panoId", "zoomLevels", "lat", "lng", "original_l", "original_1", "elevation_", "descriptio", "streetRang", "region", "country", "elevatio_1", "links_cnt", "link_forwa", "link_f_pan", "link_f_roa", "link_f_des", "link_backw", "link_b_pan", "link_b_roa", "link_b_des", "link_other", "year"], "geometry_types": ["Point"], "field_types": {"image_widt": "int64", "image_heig": "int64", "tile_width": "int64", "tile_heigh": "int64", "image_date": "str", "imagery_ty": "int64", "projection": "str", "pano_yaw_d": "float64", "tilt_yaw_d": "float64", "tilt_pitch": "float64", "panoId": "str", "zoomLevels": "float64", "lat": "float64", "lng": "float64", "original_l": "float64", "original_1": "float64", "elevation_": "float64", "descriptio": "str", "streetRang": "float64", "region": "str", "country": "str", "elevatio_1": "float64", "links_cnt": "float64", "link_forwa": "float64", "link_f_pan": "str", "link_f_roa": "float64", "link_f_des": "str", "link_backw": "float64", "link_b_pan": "str", "link_b_roa": "float64", "link_b_des": "str", "link_other": "str", "year": "int32"}, "sample_rows": [{"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 182.9423980712891, "tilt_yaw_d": 88.7552719116211, "tilt_pitch": 0.832933723926544, "panoId": "5b9gMwpqVNvBTRryCLZYpw", "zoomLevels": NaN, "lat": 34.00084698505906, "lng": -81.00533150636781, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "828 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 93.14770507812499, "links_cnt": 2.0, "link_forwa": 185.1232604980469, "link_f_pan": "5TiuLOLcYyCKAxWRe0K-sg", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.124769687652588, "link_b_pan": "NYP6vcGQ_cLKiBI6Ycea8g", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 184.2658996582031, "tilt_yaw_d": 88.7352066040039, "tilt_pitch": 0.80227267742157, "panoId": "5TiuLOLcYyCKAxWRe0K-sg", "zoomLevels": NaN, "lat": 34.00075797525222, "lng": -81.00533900842878, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "828 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 92.95042419433594, "links_cnt": 2.0, "link_forwa": 185.0914001464844, "link_f_pan": "P8Sz93OClpo3M5IF7RhiWw", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.123254776000978, "link_b_pan": "5b9gMwpqVNvBTRryCLZYpw", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2023-1", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 185.6534423828125, "tilt_yaw_d": 88.75499725341797, "tilt_pitch": 0.59730589389801, "panoId": "P8Sz93OClpo3M5IF7RhiWw", "zoomLevels": NaN, "lat": 34.000667807799, "lng": -81.00534912356608, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "822 Woodrow St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 92.74822998046876, "links_cnt": 2.0, "link_forwa": 185.1199798583984, "link_f_pan": "WrtBzm6Ll0x-_rHzkwj3rA", "link_f_roa": NaN, "link_f_des": "Woodrow St", "link_backw": 5.091405391693116, "link_b_pan": "5TiuLOLcYyCKAxWRe0K-sg", "link_b_roa": NaN, "link_b_des": "Woodrow St", "link_other": NaN, "year": 2023}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-81.01085594896888, 33.97913492079225, -80.98747947168117, 34.00084698505906]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_01\\pano_graph.json"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260423T184016Z-95a56beb-082-geoagent_082-try01\\steps\\step_01\\pano_graph.json"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

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