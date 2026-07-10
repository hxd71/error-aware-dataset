# GeoAgent Task 105

- 任务编号：105
- LLM：DeepSeek V4 Pro
- 推理配置：DeepSeek thinking 开启
- 任务难度：advanced

## 任务描述

Please analyze the provided DEM and road data to identify areas suitable for camping based on the following criteria: (1) Calculate the terrain aspect from the DEM, and include areas where the aspect value is greater than 100 degrees. (2) Compute the distance of each point in the DEM to the closest road using the provided road shapefile, and retain areas within 1000 meters of a road. (3) Combine these two conditions to save the output as a raster file and generate a suitability map.
