# GIS 错误证据：GeoAgent Task 70

- 主标签：B1 数据集完整性破坏
- LLM：qwen3.6-plus（dashscope）
- 推理配置：thinking 开关未单列记录
- 视觉审查：至少审查一项可视化成果

## 1. 任务目标

将尼日利亚铁路投影到EPSG:26392地图坐标系，将结果保存为Shapefile，然后计算总长度，并将总长度保存到文本文件中。

## 2. 任务执行工作流

1. 从 Nigeria 道路数据中筛选铁路要素。
2. 把铁路重投影到 EPSG:26392。
3. 计算总长度并分别输出 Shapefile 和文本结果。

## 3. 错误发生位置

错误出在铁路要素筛选阶段。任务要求投影并统计尼日利亚铁路，运行中没有从道路数据中筛出铁路要素。

## 4. 错误机制与结果影响

`total_length.txt` 统计了错误要素集合的长度，不是铁路总长度。

## 5. 具体错误证据

- `execution_result/workflow/step_01_code.py、execution_result/workflow/step_02_code.py` 读取交通线数据后直接写出长度结果。
- 代码没有在长度求和前用 railway/railroad 等铁路属性筛出铁路要素。
- `total_length.txt` 的统计对象因此不是任务要求的铁路集合。

## 6. 任务执行结果预览

下图由错误运行写出的最终成果生成。图层或表格内容以原文件为准，错误判定依据上述处理逻辑和数值证据。

![任务执行结果预览](../execution_result/previews/total_length.png)

## 7. 解决错误后 GIS 任务应有的结果预览

下图来自同一任务的正确运行，展示在修正“未筛选铁路要素而把全部道路写入结果”后应得到的最终成果。

![GIS 任务应有的结果预览](reference.png)

## 8. 可视化判读说明

本任务的预览图只能呈现成果外观。判读重点是第 5 节列出的函数调用、字段选择、输出元数据和日志参数；这些材料说明错误如何进入 CRS、transform、bounds、像元大小、NoData、字段或 Shapefile 组件。
