import json
import pandas as pd
import os

# Path to the input data file
input_file = r"<LOCAL_REPO_ROOT>\external_task_runs\data\geonature\province_rankings.json"

# Output file names (saved in current working directory)
output_csv = "co2_eligible_gt70.csv"
output_json = "co2_eligible_gt70.json"

# Read the JSON file
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# If the JSON is a list of records, convert to DataFrame directly
# Otherwise adjust based on structure (assumed list of dicts)
if isinstance(data, list):
    df = pd.DataFrame(data)
elif isinstance(data, dict) and 'data' in data:  # possible nested structure
    df = pd.DataFrame(data['data'])
else:
    # Fallback: assume the top-level keys are records
    df = pd.DataFrame.from_dict(data, orient='index')
    if 'eligible_pct' not in df.columns:
        raise ValueError("Could not locate 'eligible_pct' column in the data.")

# Ensure eligible_pct column exists
if 'eligible_pct' not in df.columns:
    raise KeyError("Column 'eligible_pct' not found in the JSON data.")

# Strict greater-than 70% filter
df_gt70 = df[df['eligible_pct'] > 70].copy()

# Save to CSV
df_gt70.to_csv(output_csv, index=False, encoding='utf-8')

# Save to JSON as a list of records
json_output = df_gt70.to_dict(orient='records')
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"Filtered {len(df_gt70)} provinces. Files saved: {output_csv}, {output_json}")