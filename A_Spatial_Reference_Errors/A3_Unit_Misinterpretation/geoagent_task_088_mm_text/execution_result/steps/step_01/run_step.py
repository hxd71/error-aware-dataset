import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"richland_downtown_street_view_image_location_epsg6569": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_tree\\Richland_downtown_street_view_image_location_EPSG6569\\Richland_downtown_street_view_image_location_EPSG6569.shp"}''')
current_step_assets_by_id = json.loads(r'''{"richland_downtown_street_view_image_location_epsg6569": {"asset_id": "richland_downtown_street_view_image_location_epsg6569", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Street_tree\\Richland_downtown_street_view_image_location_EPSG6569\\Richland_downtown_street_view_image_location_EPSG6569.shp", "role": "subject", "format": "shp", "crs": "EPSG:6569", "metadata": {"feature_count": 19257, "columns": ["image_widt", "image_heig", "tile_width", "tile_heigh", "image_date", "imagery_ty", "projection", "pano_yaw_d", "tilt_yaw_d", "tilt_pitch", "panoId", "zoomLevels", "lat", "lng", "original_l", "original_1", "elevation_", "descriptio", "streetRang", "region", "country", "elevatio_1", "links_cnt", "link_forwa", "link_f_pan", "link_f_roa", "link_f_des", "link_backw", "link_b_pan", "link_b_roa", "link_b_des", "link_other"], "geometry_types": ["Point"], "field_types": {"image_widt": "int64", "image_heig": "int64", "tile_width": "int64", "tile_heigh": "int64", "image_date": "str", "imagery_ty": "int64", "projection": "str", "pano_yaw_d": "float64", "tilt_yaw_d": "float64", "tilt_pitch": "float64", "panoId": "str", "zoomLevels": "float64", "lat": "float64", "lng": "float64", "original_l": "float64", "original_1": "float64", "elevation_": "float64", "descriptio": "str", "streetRang": "float64", "region": "str", "country": "str", "elevatio_1": "float64", "links_cnt": "float64", "link_forwa": "float64", "link_f_pan": "str", "link_f_roa": "float64", "link_f_des": "str", "link_backw": "float64", "link_b_pan": "str", "link_b_roa": "float64", "link_b_des": "str", "link_other": "str"}, "sample_rows": [{"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2022-9", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 159.52497863769534, "tilt_yaw_d": 91.84159088134767, "tilt_pitch": 1.972998380661011, "panoId": "jOD0Nf9F6UACkaegTKM9pQ", "zoomLevels": NaN, "lat": 34.00507521555492, "lng": -81.01689698278686, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "1020 Pine St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 88.53287506103516, "links_cnt": 2.0, "link_forwa": 159.2644348144531, "link_f_pan": "ApQsPKfMvy-41DtESyA4ig", "link_f_roa": NaN, "link_f_des": "Pine St", "link_backw": 339.2740478515625, "link_b_pan": "PUzLORoTNYtS3QQp-UzHyQ", "link_b_roa": NaN, "link_b_des": "Pine St", "link_other": NaN}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2022-9", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 161.2086639404297, "tilt_yaw_d": 91.5710906982422, "tilt_pitch": 2.62404990196228, "panoId": "ApQsPKfMvy-41DtESyA4ig", "zoomLevels": NaN, "lat": 34.00498921918825, "lng": -81.01686158498303, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "1018 Pine St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 88.84321594238281, "links_cnt": 2.0, "link_forwa": 159.2247314453125, "link_f_pan": "62_GoeXORHvVrbP94XIuiA", "link_f_roa": NaN, "link_f_des": "Pine St", "link_backw": 339.2644348144531, "link_b_pan": "jOD0Nf9F6UACkaegTKM9pQ", "link_b_roa": NaN, "link_b_des": "Pine St", "link_other": NaN}, {"image_widt": 16384, "image_heig": 8192, "tile_width": 512, "tile_heigh": 512, "image_date": "2022-9", "imagery_ty": 1, "projection": "spherical", "pano_yaw_d": 341.6531982421875, "tilt_yaw_d": 88.20294952392578, "tilt_pitch": 358.7576599121094, "panoId": "62_GoeXORHvVrbP94XIuiA", "zoomLevels": NaN, "lat": 34.00490448849011, "lng": -81.01681008957817, "original_l": NaN, "original_1": NaN, "elevation_": NaN, "descriptio": "1016 Pine St", "streetRang": NaN, "region": "Columbia; South Carolina", "country": "US", "elevatio_1": 89.19318389892578, "links_cnt": 2.0, "link_forwa": 339.2247314453125, "link_f_pan": "ApQsPKfMvy-41DtESyA4ig", "link_f_roa": NaN, "link_f_des": "Pine St", "link_backw": 159.2934265136719, "link_b_pan": "cpO9PmsyL4rj4d44H8wA3g", "link_b_roa": NaN, "link_b_des": "Pine St", "link_other": NaN}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [607111.3516507, 237963.2003492626, 611687.0184570934, 240842.8520857328]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260420T112719Z-2446843a\\runs\\eval-from-geo-agent-20260420T112719Z-2446843a-088-geoagent_088-try01\\steps\\step_01\\filtered_points_2013_onward.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260420T112719Z-2446843a\\runs\\eval-from-geo-agent-20260420T112719Z-2446843a-088-geoagent_088-try01\\steps\\step_01\\filtered_points_2013_onward.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

from pathlib import Path
import geopandas as gpd
import json

# Input path from runtime binding (use asset_paths_by_id)
input_path = r"[SECONDARY_RUN_WORKSPACE]\data\from_geo_agent\datasets\Street_tree\Richland_downtown_street_view_image_location_EPSG6569\Richland_downtown_street_view_image_location_EPSG6569.shp"

# Output path from runtime binding (use output_paths exactly as written)
output_path = r"[SECONDARY_RUN_WORKSPACE]\outputs\evaluations\from_geo_agent\eval-from-geo-agent-20260420T112719Z-2446843a\runs\eval-from-geo-agent-20260420T112719Z-2446843a-088-geoagent_088-try01\steps\step_01\filtered_points_2013_onward.shp"

# Read the source vector data
print(f"Reading input: {input_path}")
gdf = gpd.read_file(input_path)
print(f"Total features loaded: {len(gdf)}")

# Extract year from image_date (format is 'YYYY-M' like '2022-9')
# The year is the first 4 characters of the string
def extract_year(date_str):
    return int(str(date_str)[:4])

gdf['_extracted_year'] = gdf['image_date'].apply(extract_year)

# Explicit filtering predicate: year >= 2013
MINIMUM_YEAR = 2013
filtered_gdf = gdf[gdf['_extracted_year'] >= MINIMUM_YEAR].copy()

# Drop the temporary year column to preserve original attribute schema
filtered_gdf.drop(columns=['_extracted_year'], inplace=True)

print(f"Filtered features (year >= {MINIMUM_YEAR}): {len(filtered_gdf)}")

# Write the filtered result
filtered_gdf.to_file(output_path, driver='ESRI Shapefile')
print(f"Output written: {output_path}")

# Print execution summary as JSON
summary = {
    "step_id": "step_01",
    "input_features": int(len(gdf)),
    "output_features": int(len(filtered_gdf)),
    "filter_rule": "image_date year >= 2013",
    "output_path": output_path
}
print(json.dumps(summary))