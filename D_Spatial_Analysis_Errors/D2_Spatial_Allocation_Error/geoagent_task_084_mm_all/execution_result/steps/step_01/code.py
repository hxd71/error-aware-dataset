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