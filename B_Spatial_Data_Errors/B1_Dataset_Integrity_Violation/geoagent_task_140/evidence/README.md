# GIS 错误证据：GeoAgent Task 140

- 主标签：B1 数据集完整性破坏
- LLM：DeepSeek V4 Pro（DeepSeek thinking 开启）
- 视觉审查：Qwen3-VL（thinking 关闭）

## 1. 任务目标

在每个面要素中找到距线要素最近的顶点，保留面属性并输出点 Shapefile。

## 2. 任务执行工作流

1. 读取面和线图层。
2. 遍历面顶点并计算其到最近线的距离。
3. 提取最近顶点并写入 `nearest_vertices.shp`。

## 3. 错误发生位置

错误发生在距离计算前的 CRS 与单位校验阶段：参与运算的图层均无 `.prj`。

## 4. 错误机制与结果影响

最近顶点结果及参与运算的输入均缺少 `.prj`，距离关系没有可核验的空间参考。

最近距离建立在未定义的坐标空间中，距离单位和距离关系无法核验，输出点也继续缺少空间参考。

## 5. 具体错误证据

- `area.shp` 与 `line.shp` 均无 `.prj`。
- `nearest_vertices.shp` 也无 `.prj`。
- 最近关系受坐标系和单位约束，而代码未做相关校验。

## 6. 任务执行结果预览

下图是 LLM 提取的最近顶点。点位反映了程序在当前坐标数值下得到的结果，但参与距离计算的输入和输出均没有 CRS，距离关系缺少可核验的空间参考。

### 最终成果：nearest_vertices.shp

- 源成果文件：`coder/subtask_1/nearest_vertices.shp`
- 说明：`nearest_vertices.shp` 中提取的最近顶点几何预览。

![最终成果预览](../execution_result/previews/nearest_vertices.png)

## 7. 解决错误后 GIS 任务应有的结果预览

参考图展示在统一、适合距离计算的 CRS 下应提取的最终最近顶点。

![GIS 任务应有的结果预览](reference.png)

## 8. 可视化判读说明

预览图只能显示几何外观，不能直接呈现 Shapefile 组件完整性。本类错误的审查入口是样本数据包中的 `.prj`、`.dbf`、`.shx` 等组件，`execution_result/file_metadata.json`，以及 `run_log/run.log` 中的输出写入记录。
