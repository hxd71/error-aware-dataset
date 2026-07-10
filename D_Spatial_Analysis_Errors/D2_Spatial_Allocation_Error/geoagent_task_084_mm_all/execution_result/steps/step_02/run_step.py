import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"rolla_building_footprints": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_building_footprints\\Rolla_building_footprints.shp", "rolla_downtown_block_groups_2019": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_downtown_block_groups_2019\\Rolla_downtown_block_groups_2019.shp"}''')
current_step_assets_by_id = json.loads(r'''{"rolla_building_footprints": {"asset_id": "rolla_building_footprints", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_building_footprints\\Rolla_building_footprints.shp", "role": "subject", "format": "shp", "crs": "PROJCS[\"NAD83(2011) / Missouri Central\",GEOGCS[\"NAD83(2011)\",DATUM[\"NAD83_National_Spatial_Reference_System_2011\",SPHEROID[\"GRS 1980\",6378137,298.257222101,AUTHORITY[\"EPSG\",\"7019\"]],AUTHORITY[\"EPSG\",\"1116\"]],PRIMEM[\"Greenwich\",0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",35.8333333333333],PARAMETER[\"central_meridian\",-92.5],PARAMETER[\"scale_factor\",0.999933333333333],PARAMETER[\"false_easting\",500000],PARAMETER[\"false_northing\",0],UNIT[\"metre\",1,AUTHORITY[\"EPSG\",\"9001\"]],AXIS[\"Easting\",EAST],AXIS[\"Northing\",NORTH]]", "metadata": {"feature_count": 6909, "columns": ["Join_Count", "TARGET_FID", "release", "capture_da", "GEOID", "NAME", "fd_id", "bid", "cbfips", "st_damcat", "occtype", "bldgtype", "num_story", "sqft", "found_type", "found_ht", "med_yr_blt", "val_struct", "val_cont", "val_vehic", "ftprntid", "ftprntsrc", "source", "students", "pop2amu65", "pop2amo65", "pop2pmu65", "pop2pmo65", "o65disable", "u65disable", "x", "y", "firmzone", "grnd_elv_m", "ground_elv", "prediction", "probabilit", "id", "DS", "height"], "geometry_types": ["Polygon"], "field_types": {"Join_Count": "int64", "TARGET_FID": "int64", "release": "int64", "capture_da": "str", "GEOID": "str", "NAME": "str", "fd_id": "int64", "bid": "str", "cbfips": "str", "st_damcat": "str", "occtype": "str", "bldgtype": "str", "num_story": "float64", "sqft": "float64", "found_type": "str", "found_ht": "float64", "med_yr_blt": "int64", "val_struct": "float64", "val_cont": "float64", "val_vehic": "float64", "ftprntid": "str", "ftprntsrc": "str", "source": "str", "students": "int64", "pop2amu65": "int64", "pop2amo65": "int64", "pop2pmu65": "int64", "pop2pmo65": "int64", "o65disable": "float64", "u65disable": "float64", "x": "float64", "y": "float64", "firmzone": "str", "grnd_elv_m": "float64", "ground_elv": "float64", "prediction": "str", "probabilit": "float64", "id": "int64", "DS": "int32", "height": "float64"}, "sample_rows": [{"Join_Count": 1, "TARGET_FID": 0, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538971516, "bid": "869CX75R+RCR-3-3-4-3", "cbfips": "291618910003033", "st_damcat": "RES", "occtype": "RES1-1SWB", "bldgtype": "W", "num_story": 1.0, "sqft": 3096.0, "found_type": "B", "found_ht": 2.0, "med_yr_blt": 1988, "val_struct": 476871.911, "val_cont": 238435.955, "val_vehic": 27000.0, "ftprntid": "29161_8228", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 0, "pop2pmu65": 1, "pop2pmo65": 0, "o65disable": 0.23, "u65disable": 0.06, "x": -91.70897375, "y": 37.95960392, "firmzone": NaN, "grnd_elv_m": 314.29296875, "ground_elv": 1031.14494359, "prediction": "gabled", "probabilit": 1.0, "id": 538971516, "DS": 0, "height": 5.0}, {"Join_Count": 1, "TARGET_FID": 1, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538973408, "bid": "869CW7MQ+MWQ-4-3-4-5", "cbfips": "291618910003073", "st_damcat": "RES", "occtype": "RES1-1SWB", "bldgtype": "W", "num_story": 1.0, "sqft": 2272.0, "found_type": "B", "found_ht": 2.0, "med_yr_blt": 1988, "val_struct": 387801.085, "val_cont": 193900.542, "val_vehic": 27000.0, "ftprntid": "29161_8485", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 1, "pop2pmu65": 1, "pop2pmo65": 1, "o65disable": 0.23, "u65disable": 0.06, "x": -91.71015477, "y": 37.93420081, "firmzone": NaN, "grnd_elv_m": 292.69400024, "ground_elv": 960.28218376, "prediction": "gabled", "probabilit": 0.99995601177, "id": 538973408, "DS": 0, "height": 5.0}, {"Join_Count": 1, "TARGET_FID": 2, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538973499, "bid": "869CX78Q+XR6-6-5-6-4", "cbfips": "291618910003041", "st_damcat": "RES", "occtype": "RES1-2SNB", "bldgtype": "W", "num_story": 2.0, "sqft": 4182.0, "found_type": "S", "found_ht": 0.5, "med_yr_blt": 1988, "val_struct": 322883.871, "val_cont": 161441.935, "val_vehic": 27000.0, "ftprntid": "29161_8621", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 1, "pop2pmu65": 1, "pop2pmo65": 1, "o65disable": 0.23, "u65disable": 0.06, "x": -91.71047344, "y": 37.96740599, "firmzone": NaN, "grnd_elv_m": 342.06069946, "ground_elv": 1122.24642523, "prediction": "gabled", "probabilit": 0.99999797344, "id": 538973499, "DS": 2, "height": 6.5}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [560604.3650931215, 230872.61726600296, 569561.8081928248, 240021.9514177997]}}}''')
artifact_paths_by_name = json.loads(r'''{"bg_population_totals.csv": "[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_01\\bg_population_totals.csv"}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_02\\buildings_with_bg_totals.shp"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_02\\buildings_with_bg_totals.shp"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import json
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Read building footprints
buildings_path = asset_paths_by_id["rolla_building_footprints"]
buildings = gpd.read_file(buildings_path)

# Read block group population totals from step 01 artifact
bg_pop_path = artifact_paths_by_name["bg_population_totals.csv"]
bg_pop = pd.read_csv(bg_pop_path)

# Verify join columns exist
print(f"Buildings cbfips sample: {buildings['cbfips'].head(3).tolist()}")
print(f"BG GEOID sample: {bg_pop['GEOID'].head(3).tolist() if 'GEOID' in bg_pop.columns else 'N/A'}")
print(f"BG columns: {list(bg_pop.columns)}")

# Compute building area in current CRS (NAD83(2011) / Missouri Central - meters)
buildings["bldg_area"] = buildings.geometry.area

# Aggregate building area by cbfips
bg_area = buildings.groupby("cbfips")["bldg_area"].sum().reset_index()
bg_area.columns = ["cbfips", "bg_total_area"]

# Merge buildings with their block group area
buildings = buildings.merge(bg_area, on="cbfips", how="left")

# Join with population totals - use the join column that matches cbfips
join_col = "GEOID" if "GEOID" in bg_pop.columns else None
if join_col:
    buildings = buildings.merge(bg_pop, left_on="cbfips", right_on=join_col, how="left")
    print(f"Population column found in CSV: {[c for c in bg_pop.columns if 'pop' in c.lower()]}")

# Reproject to EPSG:4269 to match block group CRS
target_crs = "EPSG:4269"
buildings_geo = buildings.to_crs(target_crs)

# Write output
output_path = output_paths[0]
buildings_geo.to_file(output_path, driver="ESRI Shapefile")

# Summary
print(f"Output written: {output_path}")
print(f"Features: {len(buildings_geo)}")
print(f"CRS: {buildings_geo.crs}")
print(f"Columns: {list(buildings_geo.columns)}")

# Execution summary
summary = {
    "step_id": "step_02",
    "operation": "join_population_to_buildings",
    "input_features": len(buildings),
    "output_features": len(buildings_geo),
    "output_crs": str(buildings_geo.crs),
    "output_path": output_path
}
print(json.dumps(summary))