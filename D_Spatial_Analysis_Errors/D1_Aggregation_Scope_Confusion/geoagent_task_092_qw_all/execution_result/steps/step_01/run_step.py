import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"pacounties": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp", "pa_data_epsg4326": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PA_Data_EPSG4326\\PA_Data_EPSG4326.shp"}''')
current_step_assets_by_id = json.loads(r'''{"pa_data_epsg4326": {"asset_id": "pa_data_epsg4326", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PA_Data_EPSG4326\\PA_Data_EPSG4326.shp", "role": "reference", "format": "shp", "crs": "EPSG:4326", "metadata": {"feature_count": 3179, "columns": ["OID_", "GEOID", "STATEFP", "COUNTYFP", "TRACTFP", "Geoid_data", "cX", "cY", "latitude", "longitude", "Coronary_h", "ratio_seni", "ratio_whit", "ratio_blac", "ratio_hisp", "ratio_asia", "ratio_pove", "ratio_high", "ratio_unin", "ratio_unem", "ratio_rent", "ratio_mort", "median_hou", "Beer_Wine_", "Tobacco_St", "Drinking_P", "Supermarke", "Fruit_and_", "Limited_Se", "Convenienc", "Fitness_an", "Nature_Par", "Sports_Tea"], "geometry_types": ["Point"], "field_types": {"OID_": "str", "GEOID": "str", "STATEFP": "str", "COUNTYFP": "str", "TRACTFP": "str", "Geoid_data": "str", "cX": "float64", "cY": "float64", "latitude": "float64", "longitude": "float64", "Coronary_h": "float64", "ratio_seni": "float64", "ratio_whit": "float64", "ratio_blac": "float64", "ratio_hisp": "float64", "ratio_asia": "float64", "ratio_pove": "float64", "ratio_high": "float64", "ratio_unin": "float64", "ratio_unem": "float64", "ratio_rent": "float64", "ratio_mort": "float64", "median_hou": "int64", "Beer_Wine_": "float64", "Tobacco_St": "float64", "Drinking_P": "float64", "Supermarke": "float64", "Fruit_and_": "float64", "Limited_Se": "float64", "Convenienc": "float64", "Fitness_an": "float64", "Nature_Par": "float64", "Sports_Tea": "float64"}, "sample_rows": [{"OID_": "51999", "GEOID": "42001030101", "STATEFP": "42", "COUNTYFP": "42001", "TRACTFP": "42001030101", "Geoid_data": "14000US42001030101", "cX": 1509446.375, "cY": 152760.5625, "latitude": 40.0146129, "longitude": -77.0916161, "Coronary_h": 5.900000095, "ratio_seni": 0.169207884, "ratio_whit": 0.907772406, "ratio_blac": 0.013015991, "ratio_hisp": 0.104499814, "ratio_asia": 0.0, "ratio_pove": 0.082930457, "ratio_high": 0.30749354, "ratio_unin": 0.102268501, "ratio_unem": 0.00974026, "ratio_rent": 0.338888889, "ratio_mort": 0.171912833, "median_hou": 79000, "Beer_Wine_": 1.347854, "Tobacco_St": 3.084934, "Drinking_P": 2.310864, "Supermarke": 10.082684, "Fruit_and_": 0.59454, "Limited_Se": 27.495018, "Convenienc": 2.769971, "Fitness_an": 5.076358, "Nature_Par": 8.701002, "Sports_Tea": 0.664756}, {"OID_": "52000", "GEOID": "42001030102", "STATEFP": "42", "COUNTYFP": "42001", "TRACTFP": "42001030102", "Geoid_data": "14000US42001030102", "cX": 1515056.5, "cY": 146218.2188, "latitude": 39.9508164, "longitude": -77.039371, "Coronary_h": 5.199999809, "ratio_seni": 0.143907024, "ratio_whit": 0.981028884, "ratio_blac": 0.003418219, "ratio_hisp": 0.083575457, "ratio_asia": 0.0, "ratio_pove": 0.045659082, "ratio_high": 0.370742542, "ratio_unin": 0.075029909, "ratio_unem": 0.024843253, "ratio_rent": 0.647400091, "ratio_mort": 0.108140401, "median_hou": 82095, "Beer_Wine_": 1.755359, "Tobacco_St": 2.52167, "Drinking_P": 2.661344, "Supermarke": 13.660641, "Fruit_and_": 0.418724, "Limited_Se": 29.403538, "Convenienc": 4.483199, "Fitness_an": 4.648795, "Nature_Par": 12.527472, "Sports_Tea": 0.830142}, {"OID_": "52001", "GEOID": "42001030200", "STATEFP": "42", "COUNTYFP": "42001", "TRACTFP": "42001030200", "Geoid_data": "14000US42001030200", "cX": 1506564.625, "cY": 147039.3125, "latitude": 39.9719049, "longitude": -77.1408392, "Coronary_h": 6.400000095, "ratio_seni": 0.144932801, "ratio_whit": 0.883036687, "ratio_blac": 0.007991282, "ratio_hisp": 0.189611333, "ratio_asia": 0.009262623, "ratio_pove": 0.159291664, "ratio_high": 0.403995168, "ratio_unin": 0.111151471, "ratio_unem": 0.048466332, "ratio_rent": 0.432302929, "ratio_mort": 0.165569686, "median_hou": 58990, "Beer_Wine_": 1.256992, "Tobacco_St": 1.931531, "Drinking_P": 1.867773, "Supermarke": 13.92909, "Fruit_and_": 0.710385, "Limited_Se": 25.002107, "Convenienc": 3.488864, "Fitness_an": 4.876587, "Nature_Par": 5.335616, "Sports_Tea": 0.700591}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-80.5157807, 39.7300457, -74.6996707, 42.2294089]}}, "pacounties": {"asset_id": "pacounties", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Pennsylvania\\PACounties\\PACounties.shp", "role": "subject", "format": "shp", "crs": "EPSG:4269", "metadata": {"feature_count": 67, "columns": ["STATEFP", "COUNTYFP", "COUNTYNS", "AFFGEOID", "GEOID", "NAME", "NAMELSAD", "STUSPS", "STATE_NAME", "LSAD", "ALAND", "AWATER"], "geometry_types": ["MultiPolygon", "Polygon"], "field_types": {"STATEFP": "str", "COUNTYFP": "str", "COUNTYNS": "str", "AFFGEOID": "str", "GEOID": "str", "NAME": "str", "NAMELSAD": "str", "STUSPS": "str", "STATE_NAME": "str", "LSAD": "str", "ALAND": "int64", "AWATER": "int64"}, "sample_rows": [{"STATEFP": "42", "COUNTYFP": "129", "COUNTYNS": "01209191", "AFFGEOID": "0500000US42129", "GEOID": "42129", "NAME": "Westmoreland", "NAMELSAD": "Westmoreland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2661762744, "AWATER": 21294228}, {"STATEFP": "42", "COUNTYFP": "111", "COUNTYNS": "01209188", "AFFGEOID": "0500000US42111", "GEOID": "42111", "NAME": "Somerset", "NAMELSAD": "Somerset County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 2784357763, "AWATER": 17118618}, {"STATEFP": "42", "COUNTYFP": "097", "COUNTYNS": "01209186", "AFFGEOID": "0500000US42097", "GEOID": "42097", "NAME": "Northumberland", "NAMELSAD": "Northumberland County", "STUSPS": "PA", "STATE_NAME": "Pennsylvania", "LSAD": "06", "ALAND": 1185344304, "AWATER": 50674892}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [-80.519891, 39.7198, -74.689516, 42.26986]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_01\\pa_counties_point_counts.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\runs\\eval-from-geo-agent-20260419T172139Z-88a9e18e-092-geoagent_092-try01\\steps\\step_01\\pa_counties_point_counts.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import geopandas as gpd
import json

counties_path = asset_paths_by_id['pacounties']
points_path = asset_paths_by_id['pa_data_epsg4326']
output_path = output_paths[0]

counties = gpd.read_file(counties_path)
points = gpd.read_file(points_path)

# Handle CRS difference: reproject points to match counties
points = points.to_crs(counties.crs)

# Spatial join using 'within' predicate (points within counties)
joined = gpd.sjoin(points, counties, predicate='within')

# Aggregate counts per county
point_counts = joined.groupby('index_right').size().rename('point_count')

# Merge counts back to original county dataframe
counties = counties.join(point_counts)
counties['point_count'] = counties['point_count'].fillna(0).astype(int)

# Write output
counties.to_file(output_path)

print(json.dumps({"status": "success", "output": output_path, "feature_count": len(counties)}))