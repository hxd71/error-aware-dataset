import geopandas as gpd
import pandas as pd
import json

level3_path = asset_paths_by_id["level3_30"]
suitable_path = artifact_paths_by_name["suitable_counties.shp"]
output_csv = output_paths[0]

df_total = gpd.read_file(level3_path)
df_suitable = gpd.read_file(suitable_path)

total_area = float(df_total["ALAND"].sum())
total_count = len(df_total)

if "ALAND" in df_suitable.columns:
    suitable_area = float(df_suitable["ALAND"].sum())
else:
    suitable_area = float(df_suitable.to_crs(epsg=3857).geometry.area.sum())

suitable_count = len(df_suitable)
suitable_percentage = (suitable_area / total_area) * 100.0 if total_area > 0 else 0.0

summary_df = pd.DataFrame([{
    "suitable_count": suitable_count,
    "total_count": total_count,
    "suitable_area": suitable_area,
    "total_area": total_area,
    "suitable_percentage": suitable_percentage
}])

summary_df.to_csv(output_csv, index=False)

print(json.dumps({
    "status": "success",
    "suitable_count": suitable_count,
    "total_count": total_count,
    "suitable_area": suitable_area,
    "total_area": total_area,
    "suitable_percentage": round(suitable_percentage, 2)
}))