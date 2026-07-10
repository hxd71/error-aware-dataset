import json
import geopandas as gpd
import pandas as pd

vector_path = current_step_assets_by_id["rolla_downtown_block_groups_2021"]["path"]
csv_path = current_step_artifacts_by_name["rolla_2021_population_block_group_with_fips.csv"]["path"]
output_path = output_paths[0]

gdf = gpd.read_file(vector_path)
df = pd.read_csv(csv_path)

fips_col = "FIPS"
if fips_col not in df.columns:
    fips_col = next((c for c in df.columns if "fips" in c.lower()), df.columns[0])

gdf["GEOID"] = gdf["GEOID"].astype(str)
df[fips_col] = df[fips_col].astype(str)

joined_gdf = gdf.merge(df, left_on="GEOID", right_on=fips_col, how="left")
joined_gdf.to_file(output_path, driver="ESRI Shapefile")

print(json.dumps({"status": "success", "output": output_path, "features": len(joined_gdf)}))