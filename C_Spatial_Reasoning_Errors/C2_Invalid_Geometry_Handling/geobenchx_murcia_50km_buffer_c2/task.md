# GeoBenchX/GeoNature Murcia 50km Buffer

- 任务编号：gbx_port_murcia_50km_buffer_intersections
- 论文/项目任务编号：GeoBenchX-style spatial relationship task
- LLM 配置：deepseek-v4-pro
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：GeoBenchX tools ported in GeoNatureAgent Benchmark
- 难度：medium
- 空间方法：metric buffering and topological predicate selection

## 任务描述

Create a 50 km buffer around the province of Murcia and list all Spanish provinces whose geometry intersects that buffer. Save the buffer and selected provinces.

## 本地输入数据

- `spain_provinces.geojson`

## 任务要求输出

- `murcia_50km_buffer.geojson`
- `murcia_50km_intersecting_provinces.csv`
- `murcia_50km_intersections_map.png`
