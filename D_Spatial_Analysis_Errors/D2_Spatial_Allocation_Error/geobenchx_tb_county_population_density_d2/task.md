# GeoBenchX TB County Population Density Heatmap

- 任务编号：geobenchx_task_419069
- GeoBenchX 任务编号：TASK_250309_135125_419069
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX published trace）
- 来源项目：GeoBenchX
- 难度：hard
- 空间方法：county-level raster allocation and centroid heatmap visualization

## 任务描述

Generate a heatmap of USA population density in counties with reported tuberculosis cases.

## 本地输入数据

- `StatData/Incidence of Tuberculosis Disease 2023 Massachusetts Counties.csv`
- `StatData/NYS TB cases 2023.csv`
- `ma_ny_counties_generated_scope.geojson`
- `population_raster_metadata.json`

## 任务要求输出

- `tb_county_population_density_reference.csv`
- `generated_county_area_heatmap_inputs.csv`
- `tb_county_join_audit.csv`
- `ma_ny_counties_generated_scope.geojson`
- `tb_reported_county_density_reference.geojson`
- `population_raster_metadata.json`
- `generated_county_area_centroid_heatmap.png`
- `tb_county_population_density_reference.png`
