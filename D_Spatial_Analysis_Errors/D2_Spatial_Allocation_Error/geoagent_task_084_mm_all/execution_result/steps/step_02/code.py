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