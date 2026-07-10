# GeoBenchX Earthquake Population Heatmap

- 任务编号：geobenchx_task_367674
- GeoBenchX 任务编号：TASK_250309_135125_367674
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX published trace）
- 来源项目：GeoBenchX
- 难度：hard
- 空间方法：raster-to-point extraction and weighted heatmap visualization

## 任务描述

Make a heatmap showing population concentration in earthquake-affected zones.

## 本地输入数据

- `GeoData/earthquakes_30_days_Feb142025.cpg`
- `GeoData/earthquakes_30_days_Feb142025.dbf`
- `GeoData/earthquakes_30_days_Feb142025.prj`
- `GeoData/earthquakes_30_days_Feb142025.qmd`
- `GeoData/earthquakes_30_days_Feb142025.shp`
- `GeoData/earthquakes_30_days_Feb142025.shx`
- `GeoData/usa_ppp_2020_1km_Aggregated_UNadj.tif`

## 任务要求输出

- `earthquake_population_reference_samples.csv`
- `generated_earthquake_magnitude_map.png`
- `earthquake_population_heatmap_reference.png`
