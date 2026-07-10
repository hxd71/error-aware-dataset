# LLM-Geo Population_equal_interval_NC

- 任务编号：population_equal_interval_nc
- LLM 配置：deepseek-v4-pro
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：LLM-Geo

## 任务描述

Join North Carolina Census tract population attributes to tract polygons and create a choropleth map of `TotalPopulation`. Use exactly five equal-interval classes, not quantiles and not natural breaks. Save the map as `nc_population_equal_interval_map.png` and save a CSV named `nc_population_equal_interval_class_counts.csv` with one row per class showing the class label and number of tracts in that class.
