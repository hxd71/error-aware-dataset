# Self-built GIS Task C2-01

- LLM：DeepSeek V4 Pro
- 推理配置：thinking 关闭
- 运行次数：第 1 次

## 任务描述

Intersect zones.geojson with masks.geojson. Preserve source_id and mask_id for every polygonal overlap, including all valid parts from multipart and problematic source geometries. The final layer must contain only valid polygon geometries. Save it as overlap_result.gpkg.
