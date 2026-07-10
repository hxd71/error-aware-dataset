# GeoBenchX Rural Population Percentages

- 任务编号：geobenchx_task_748943
- GeoBenchX 任务编号：TASK_250309_135125_748943
- LLM 配置：claude-3-5-haiku-20241022（GeoBenchX published trace）
- 来源项目：GeoBenchX
- 难度：medium
- 空间方法：statistical variable derivation and choropleth mapping

## 任务描述

Show rural population percentages worldwide.

## 本地输入数据

- `StatData/API_SP.RUR.TOTL_DS2_en_csv_v2_6835.zip`
- `StatData/API_SP.POP.TOTL_DS2_en_csv_v2_56.zip`
- `GeoData/WB_countries_Admin0_10m.cpg`
- `GeoData/WB_countries_Admin0_10m.dbf`
- `GeoData/WB_countries_Admin0_10m.prj`
- `GeoData/WB_countries_Admin0_10m.shp`
- `GeoData/WB_countries_Admin0_10m.shp.xml`
- `GeoData/WB_countries_Admin0_10m.shx`

## 任务要求输出

- `rural_percentage_reference_table.csv`
- `generated_raw_rural_population_table.csv`
- `rural_percentage_reference_map.png`
- `generated_raw_rural_population_map.png`
