import json
from pathlib import Path

analysis_crs = json.loads(r'''null''')
asset_paths_by_id = json.loads(r'''{"rolla_building_footprints": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_building_footprints\\Rolla_building_footprints.shp", "rolla_downtown_block_groups_2019": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_downtown_block_groups_2019\\Rolla_downtown_block_groups_2019.shp"}''')
current_step_assets_by_id = json.loads(r'''{"rolla_building_footprints": {"asset_id": "rolla_building_footprints", "asset_type": "vector", "path": "[SECONDARY_RUN_WORKSPACE]\\data\\from_geo_agent\\datasets\\Rolla_watershed\\Rolla_building_footprints\\Rolla_building_footprints.shp", "role": "subject", "format": "shp", "crs": "PROJCS[\"NAD83(2011) / Missouri Central\",GEOGCS[\"NAD83(2011)\",DATUM[\"NAD83_National_Spatial_Reference_System_2011\",SPHEROID[\"GRS 1980\",6378137,298.257222101,AUTHORITY[\"EPSG\",\"7019\"]],AUTHORITY[\"EPSG\",\"1116\"]],PRIMEM[\"Greenwich\",0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",35.8333333333333],PARAMETER[\"central_meridian\",-92.5],PARAMETER[\"scale_factor\",0.999933333333333],PARAMETER[\"false_easting\",500000],PARAMETER[\"false_northing\",0],UNIT[\"metre\",1,AUTHORITY[\"EPSG\",\"9001\"]],AXIS[\"Easting\",EAST],AXIS[\"Northing\",NORTH]]", "metadata": {"feature_count": 6909, "columns": ["Join_Count", "TARGET_FID", "release", "capture_da", "GEOID", "NAME", "fd_id", "bid", "cbfips", "st_damcat", "occtype", "bldgtype", "num_story", "sqft", "found_type", "found_ht", "med_yr_blt", "val_struct", "val_cont", "val_vehic", "ftprntid", "ftprntsrc", "source", "students", "pop2amu65", "pop2amo65", "pop2pmu65", "pop2pmo65", "o65disable", "u65disable", "x", "y", "firmzone", "grnd_elv_m", "ground_elv", "prediction", "probabilit", "id", "DS", "height"], "geometry_types": ["Polygon"], "field_types": {"Join_Count": "int64", "TARGET_FID": "int64", "release": "int64", "capture_da": "str", "GEOID": "str", "NAME": "str", "fd_id": "int64", "bid": "str", "cbfips": "str", "st_damcat": "str", "occtype": "str", "bldgtype": "str", "num_story": "float64", "sqft": "float64", "found_type": "str", "found_ht": "float64", "med_yr_blt": "int64", "val_struct": "float64", "val_cont": "float64", "val_vehic": "float64", "ftprntid": "str", "ftprntsrc": "str", "source": "str", "students": "int64", "pop2amu65": "int64", "pop2amo65": "int64", "pop2pmu65": "int64", "pop2pmo65": "int64", "o65disable": "float64", "u65disable": "float64", "x": "float64", "y": "float64", "firmzone": "str", "grnd_elv_m": "float64", "ground_elv": "float64", "prediction": "str", "probabilit": "float64", "id": "int64", "DS": "int32", "height": "float64"}, "sample_rows": [{"Join_Count": 1, "TARGET_FID": 0, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538971516, "bid": "869CX75R+RCR-3-3-4-3", "cbfips": "291618910003033", "st_damcat": "RES", "occtype": "RES1-1SWB", "bldgtype": "W", "num_story": 1.0, "sqft": 3096.0, "found_type": "B", "found_ht": 2.0, "med_yr_blt": 1988, "val_struct": 476871.911, "val_cont": 238435.955, "val_vehic": 27000.0, "ftprntid": "29161_8228", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 0, "pop2pmu65": 1, "pop2pmo65": 0, "o65disable": 0.23, "u65disable": 0.06, "x": -91.70897375, "y": 37.95960392, "firmzone": NaN, "grnd_elv_m": 314.29296875, "ground_elv": 1031.14494359, "prediction": "gabled", "probabilit": 1.0, "id": 538971516, "DS": 0, "height": 5.0}, {"Join_Count": 1, "TARGET_FID": 1, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538973408, "bid": "869CW7MQ+MWQ-4-3-4-5", "cbfips": "291618910003073", "st_damcat": "RES", "occtype": "RES1-1SWB", "bldgtype": "W", "num_story": 1.0, "sqft": 2272.0, "found_type": "B", "found_ht": 2.0, "med_yr_blt": 1988, "val_struct": 387801.085, "val_cont": 193900.542, "val_vehic": 27000.0, "ftprntid": "29161_8485", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 1, "pop2pmu65": 1, "pop2pmo65": 1, "o65disable": 0.23, "u65disable": 0.06, "x": -91.71015477, "y": 37.93420081, "firmzone": NaN, "grnd_elv_m": 292.69400024, "ground_elv": 960.28218376, "prediction": "gabled", "probabilit": 0.99995601177, "id": 538973408, "DS": 0, "height": 5.0}, {"Join_Count": 1, "TARGET_FID": 2, "release": 2, "capture_da": "10/1/2019-2/16/2020", "GEOID": "29161", "NAME": "Phelps", "fd_id": 538973499, "bid": "869CX78Q+XR6-6-5-6-4", "cbfips": "291618910003041", "st_damcat": "RES", "occtype": "RES1-2SNB", "bldgtype": "W", "num_story": 2.0, "sqft": 4182.0, "found_type": "S", "found_ht": 0.5, "med_yr_blt": 1988, "val_struct": 322883.871, "val_cont": 161441.935, "val_vehic": 27000.0, "ftprntid": "29161_8621", "ftprntsrc": "Bing", "source": "P", "students": 0, "pop2amu65": 3, "pop2amo65": 1, "pop2pmu65": 1, "pop2pmo65": 1, "o65disable": 0.23, "u65disable": 0.06, "x": -91.71047344, "y": 37.96740599, "firmzone": NaN, "grnd_elv_m": 342.06069946, "ground_elv": 1122.24642523, "prediction": "gabled", "probabilit": 0.99999797344, "id": 538973499, "DS": 2, "height": 6.5}], "invalid_geometry_count": 0, "null_geometry_count": 0, "bounds": [560604.3650931215, 230872.61726600296, 569561.8081928248, 240021.9514177997]}}}''')
artifact_paths_by_name = json.loads(r'''{}''')
current_step_artifacts_by_name = json.loads(r'''{}''')
output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_01\\bg_population_totals.csv"]''')
expected_output_paths = json.loads(r'''["[SECONDARY_RUN_WORKSPACE]\\outputs\\evaluations\\from_geo_agent\\eval-from-geo-agent-20260419T165504Z-57ef3a68\\runs\\eval-from-geo-agent-20260419T165504Z-57ef3a68-084-geoagent_084-try01\\steps\\step_01\\bg_population_totals.csv"]''')
step_output_dir = Path(__file__).resolve().parent
step_output_dir.mkdir(parents=True, exist_ok=True)

import geopandas as gpd
import pandas as pd

# Load buildings dataset
buildings_path = asset_paths_by_id["rolla_building_footprints"]
gdf = gpd.read_file(buildings_path)

# Define population fields to sum
pop_columns = ["pop2amu65", "pop2amo65", "pop2pmu65", "pop2pmo65"]

# Group by cbfips and sum all population fields
bg_pop = gdf.groupby("cbfips")[pop_columns].sum().reset_index()

# Compute total population per block group
bg_pop["total_population"] = bg_pop[pop_columns].sum(axis=1)

# Prepare output with cbfips and total
output_df = bg_pop[["cbfips", "total_population"]].copy()

# Write to CSV
output_df.to_csv(output_paths[0], index=False)

# Execution summary
result = {
    "step_id": "step_01",
    "status": "success",
    "block_groups_processed": len(output_df),
    "total_population_sum": int(output_df["total_population"].sum()),
    "population_fields": pop_columns,
    "output_path": str(output_paths[0])
}
print(json.dumps(result))