import json
import rasterio
import numpy as np

input_path = asset_paths_by_id['elevation_mask_nodata']
output_path = output_paths[0]

with rasterio.open(input_path) as src:
    data = src.read(1)
    meta = src.meta.copy()
    src_nodata = src.nodata

mask = np.zeros(data.shape, dtype=np.uint8)
valid = np.ones(data.shape, dtype=bool)
if src_nodata is not None:
    valid &= (data != src_nodata)

mask[valid & (data == 0.0)] = 1

meta.update(dtype='uint8', count=1)
if 'nodata' in meta:
    del meta['nodata']

with rasterio.open(output_path, 'w', **meta) as dst:
    dst.write(mask, 1)

print(json.dumps({'step': 'step_01', 'status': 'success', 'output': str(output_path)}))