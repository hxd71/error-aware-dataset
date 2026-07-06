import pandas as pd
import json

input_path = current_step_assets_by_id["rolla_2021_population_block_group"]["path"]
output_path = output_paths[0]

df = pd.read_csv(input_path)

df["full_fips"] = (
    df["state_fips"].astype(str).str.zfill(2) +
    df["county_fips"].astype(str).str.zfill(3) +
    df["tract_fips"].astype(str).str.zfill(5) +
    df["block_group_fips"].astype(str).str.zfill(1)
)

df.to_csv(output_path, index=False)

print(json.dumps({"step_id": "step_01", "status": "success", "rows_processed": len(df), "output_path": output_path}))