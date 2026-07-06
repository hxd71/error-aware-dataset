import rasterio
import numpy as np
import pandas as pd
import json

input_raster = asset_paths_by_id["sc_dem"]
output_csv = output_paths[0]

with rasterio.open(input_raster) as src:
    data = src.read(1)
    valid_data = data[data != 0.0]
    
    if len(valid_data) > 0:
        counts, bin_edges = np.histogram(valid_data, bins=50)
        bin_ranges = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]
        df = pd.DataFrame({"bin_range": bin_ranges, "count": counts})
    else:
        df = pd.DataFrame(columns=["bin_range", "count"])

df.to_csv(output_csv, index=False)

print(json.dumps({"status": "success", "output": output_csv, "valid_pixels": int(len(valid_data)), "bins": len(df)}))