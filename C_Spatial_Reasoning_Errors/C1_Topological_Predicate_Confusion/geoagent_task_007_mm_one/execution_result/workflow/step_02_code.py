import geopandas as gpd
import pandas as pd
from pathlib import Path

# Read the spatially joined houses GeoJSON from step_01
input_path = Path(r"[SECONDARY_RUN_WORKSPACE]\outputs\runs\eval-from-geo-agent-20260423T184016Z-95a56beb-007-geoagent_007-try01\steps\step_01\houses_in_saf_zone.geojson")
output_path = Path(r"[SECONDARY_RUN_WORKSPACE]\outputs\runs\eval-from-geo-agent-20260423T184016Z-95a56beb-007-geoagent_007-try01\steps\step_02\damaged_houses_saf_zone_count.csv")

# Load the GeoJSON and count features
gdf = gpd.read_file(input_path)
house_count = len(gdf)

# Write count to CSV with a single row containing the count value
df = pd.DataFrame({"damaged_house_count": [house_count]})
df.to_csv(output_path, index=False)

print(df.to_json())
