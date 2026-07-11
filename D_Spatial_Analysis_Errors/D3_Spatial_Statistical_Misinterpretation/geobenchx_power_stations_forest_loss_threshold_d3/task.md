# GeoBenchX Power Stations Forest Loss Threshold

- 任务编号：geobenchx_task_932053
- GeoBenchX 任务编号：TASK_250309_135125_932053
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX published trace）
- 来源项目：GeoBenchX
- 难度：hard
- 空间方法：spatial statistical thresholding and point-in-polygon selection

## 任务描述

How many African power stations are located in countries with significant forest loss?

## 本地输入数据

- `StatData/API_AG.LND.FRST.K2_DS2_en_csv_v2_2627.zip`
- `GeoData/Africa Power Stations.cpg`
- `GeoData/Africa Power Stations.dbf`
- `GeoData/Africa Power Stations.prj`
- `GeoData/Africa Power Stations.qmd`
- `GeoData/Africa Power Stations.shp`
- `GeoData/Africa Power Stations.shx`
- `GeoData/WB_countries_Admin0_10m.cpg`
- `GeoData/WB_countries_Admin0_10m.dbf`
- `GeoData/WB_countries_Admin0_10m.prj`
- `GeoData/WB_countries_Admin0_10m.shp`
- `GeoData/WB_countries_Admin0_10m.shp.xml`
- `GeoData/WB_countries_Admin0_10m.shx`

## 任务要求输出

- `forest_loss_reference_countries.csv`
- `generated_forest_loss_map_table.csv`
- `power_station_forest_loss_reference_selection.geojson`
- `forest_loss_threshold_audit.json`
- `forest_loss_workflow_audit.csv`
- `generated_forest_loss_choropleth.png`
- `power_stations_forest_loss_selection_reference.png`
