# GIS 错误证据：GeoAgent Task 119

- 主标签：D3 空间统计误判
- LLM：MiniMax-M2.7-highspeed（minimax）
- 推理配置：thinking 开关未单列记录
- 视觉审查：未启用视觉审查

## 1. 任务目标

请对提供的Shapefile中聚类的点要素进行空间分析。对于每个聚类，计算并描述其空间分布，包括聚类的中心、形状、方向和范围。结果应存储在新的Shapefile中，其中每个聚类的空间特征（中心坐标、标准差和拟合椭圆几何）应清晰表示。

## 2. 任务执行工作流

1. 按聚类编号分组输入点。
2. 计算各组中心、主轴方向和主轴标准差。
3. 根据统计参数生成标准差椭圆并写出。

## 3. 错误发生位置

错误出在标准差椭圆参数计算。任务要求表达每个聚类的中心、形状、方向和范围，运行中的主轴方向或轴长错误。

## 4. 错误机制与结果影响

`cluster_ellipses.shp` 的椭圆几何不能描述聚类真实空间分布。

## 5. 具体错误证据

- `execution_result/workflow/step_01_code.py` 用协方差矩阵特征向量计算 `rotation_rad`，再以 `eigenvalues[0]` 和 `eigenvalues[1]` 生成半轴。
- 当 `semi_major < semi_minor` 时，代码交换了 `semi_major` 与 `semi_minor`，并只更新 `rotation_deg = (rotation_deg + 90.0) % 360.0`。
- 后续生成椭圆坐标时仍使用交换前的 `rotation_rad`，没有同步加 90 度；量化指标显示主轴方向误差约 88–89 度。

## 6. 任务执行结果预览

下图由错误运行写出的最终成果生成。图层或表格内容以原文件为准，错误判定依据上述处理逻辑和数值证据。

![任务执行结果预览](../execution_result/previews/cluster_ellipses.png)

## 7. 解决错误后 GIS 任务应有的结果预览

下图来自同一任务的正确运行，展示在修正“标准差椭圆的主轴方向或轴长计算错误”后应得到的最终成果。

![GIS 任务应有的结果预览](reference.png)

## 8. 可视化判读说明

本任务的预览图只能呈现成果外观。判读重点是第 5 节列出的函数调用、字段选择、输出元数据和日志参数；这些材料说明错误如何进入 CRS、transform、bounds、像元大小、NoData、字段或 Shapefile 组件。
