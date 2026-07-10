import pandas as pd
import numpy as np
from pathlib import Path

# Read the two CSV files containing extracted DEM values
idw_csv = artifact_paths_by_name["idw_checkpoints.csv"]
richland_csv = artifact_paths_by_name["richland_checkpoints.csv"]

idw_df = pd.read_csv(idw_csv)
richland_df = pd.read_csv(richland_csv)

# Determine the ID column name from the data
idw_id_col = 'id' if 'id' in idw_df.columns else None
richland_id_col = 'id' if 'id' in richland_df.columns else None

# Identify value columns (exclude ID column)
idw_val_col = [c for c in idw_df.columns if c != idw_id_col][0] if idw_id_col else None
richland_val_col = [c for c in richland_df.columns if c != richland_id_col][0] if richland_id_col else None

# Merge on ID to align values
merged = pd.merge(
    idw_df[[idw_id_col, idw_val_col]].rename(columns={idw_id_col: 'id', idw_val_col: 'idw_value'}),
    richland_df[[richland_id_col, richland_val_col]].rename(columns={richland_id_col: 'id', richland_val_col: 'richland_value'}),
    on='id'
)

# Compute RMSE
differences = merged['idw_value'] - merged['richland_value']
squared_diff = differences ** 2
mse = squared_diff.mean()
rmse = np.sqrt(mse)

# Write result to output file
output_path = output_paths[0]
with open(output_path, 'w') as f:
    f.write(f"RMSE: {rmse}\n")
    f.write(f"Sample count: {len(merged)}\n")

print(json.dumps({
    "step_id": "step_03",
    "rmse": float(rmse),
    "sample_count": int(len(merged)),
    "output": str(output_path)
}))