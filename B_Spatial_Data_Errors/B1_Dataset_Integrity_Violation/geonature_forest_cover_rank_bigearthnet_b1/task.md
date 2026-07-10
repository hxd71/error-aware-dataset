# GeoNatureAgent BigEarthNet Forest Cover Rank

- 任务编号：gn_v5_62_forest_cover_rank_bigearthnet
- 论文/项目任务编号：V5_62_list_layers_habitat_years
- LLM 配置：deepseek-v4-pro
- 推理配置：direct request；thinking 开关未单列记录
- 来源项目：GeoNatureAgent Benchmark
- 难度：hard
- 空间方法：categorical LULC aggregation and ranking

## 任务描述

Create a chart ranking Beja, Faro, Lisboa, and Portalegre by their total forest cover (coniferous + broadleaf) using the BigEarthNet data.

## 本地输入数据

- `bigearthnet_portugal_stats.json`

## 任务要求输出

- `forest_cover_rank.csv`
- `forest_cover_rank.json`
- `forest_cover_rank_chart.png`
