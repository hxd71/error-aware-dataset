# LLM-Geo Axis_order_SC_hospitals

- 任务编号：axis_order_sc_hospitals
- LLM 配置：deepseek-v4-pro
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：LLM-Geo

## 任务描述

Create a point layer for South Carolina hospitals and overlay it on the South Carolina ZIP boundary map. The hospital CSV intentionally uses confusing column names: `lat_x` is latitude in degrees north, and `lon_y` is longitude in degrees west/east. Use x = longitude and y = latitude when constructing point geometry. Count how many hospital points fall inside the South Carolina ZIP boundary union. Save a map named `axis_order_hospitals_map.png` and a GeoJSON point layer named `axis_order_hospitals_points.geojson`.
