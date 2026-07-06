# Table X. Taxonomy of GIS-specific Errors in Text-based LLM Agents

## 分类口径

本表仅收录 **GIS domain knowledge errors**，即错误根源来自 GIS 学科本体知识，包括空间参考、空间数据模型、空间推理、空间分析与地图制图。它不把一般性的 agent workflow failures 或 system execution failures 纳入主 taxonomy。

这种处理可以避免将 CRS、拓扑谓词、NoData 语义等 GIS 特异性错误，与 OOM、silent failure、dependency omission 等通用 agent/system 错误放在同一层级。后者可作为辅助分析，放入独立章节 **Agent Workflow Failures Beyond GIS Knowledge**。

## Taxonomy of GIS-specific Errors

| Level-1 Category | Level-2 Category | Typical Manifestation | Error Examples from GIS Agent Workflows |
| :--- | :--- | :--- | :--- |
| **A. Spatial Reference Errors** | **A1. Coordinate Axis Misinterpretation** | Latitude/longitude reversal; x/y or row/column confusion | Instantiating points as `Point(lat, lon)` instead of `Point(lon, lat)`; generated locations shifted to oceans or invalid coordinate ranges |
| | **A2. CRS Inconsistency** | Overlay, join, or distance analysis without explicit reprojection | Running spatial overlay between EPSG:4326 and EPSG:3857 layers without `to_crs()`; empty intersection or CRS mismatch |
| | **A3. Unit Misinterpretation** | Metric operations performed in geographic degree space | Applying `buffer(500)` directly to EPSG:4326 geometries; interpreting degrees as meters |
| **B. Spatial Data Errors** | **B1. Dataset Integrity Violation** | Geospatial data models or file structures treated as ordinary flat files | Copying only `.shp` while omitting `.shx`, `.dbf`, or `.prj`; downstream read failures or attribute loss |
| | **B2. Raster Alignment Failure** | Raster shape, resolution, transform, band, or extent mismatch | Directly adding rasters with different dimensions; missing resampling or alignment before raster algebra |
| | **B3. Missing Data Misinterpretation** | NoData, masks, or background values treated as valid observations | Including `-9999` background pixels in zonal statistics; failing to mask invalid raster cells |
| **C. Spatial Reasoning Errors** | **C1. Topological Predicate Confusion** | Incorrect mapping between natural-language spatial relations and GIS predicates | Using `intersects` for a strict containment task requiring `within`; boundary-touching objects incorrectly included |
| | **C2. Invalid Geometry Handling** | Missing defensive handling for self-intersections or invalid polygons | Running `overlay`, `dissolve`, or `union` without `make_valid()`; `TopologyException` or corrupted output |
| | **C3. Network Connectivity Misinterpretation** | Network topology inferred from geometry appearance rather than graph connectivity | Treating road polylines as already routable; failing to snap origin/destination points to the nearest network nodes |
| **D. Spatial Analysis Errors** | **D1. Aggregation Scope Confusion** | Local analytical constraints collapsed into global computation | Returning one global maximum instead of one maximum per province/county; ignoring administrative grouping |
| | **D2. Spatial Allocation Error** | Extensive or intensive variables transferred across zones without valid spatial weighting | MAUP-related errors; assigning polygon-level values to intersecting zones without area-weighted redistribution |
| | **D3. Spatial Statistical Misinterpretation** | Spatial dependence, heterogeneity, or local/global statistics interpreted incorrectly | Treating spatially autocorrelated samples as independent; confusing local and global spatial statistics |
| **E. Cartographic Errors** | **E1. Classification Scheme Misuse** | Inappropriate classification method for the data distribution | Using equal interval for heavy-tailed variables where quantile or Jenks classification is needed |
| | **E2. Symbolization Error** | Visual variables inconsistent with data type or semantics | Applying continuous colormaps to categorical land-use classes; misleading ordinal interpretation |
| | **E3. Map Composition Defect** | Missing or defective cartographic elements required for interpretation | Missing legend, scale bar, labels, or unreadable class breaks; poor layout causing ambiguous map reading |

## Relationship to the Original Error List

| 原表错误点 | 修订后分类 | 是否属于 GIS-specific taxonomy |
| :--- | :--- | :---: |
| 1.1 尺度与单位混淆 | A3. Unit Misinterpretation | Yes |
| 1.2 坐标轴顺序反转 | A1. Coordinate Axis Misinterpretation | Yes |
| 1.3 缺失显式重投影/对齐 | A2. CRS Inconsistency | Yes |
| 2.1 多文件物理结构遗漏 | B1. Dataset Integrity Violation | Yes |
| 2.2 忽略栅格多维一致性 | B2. Raster Alignment Failure | Yes |
| 2.3 空间无效值 NoData 语义丢失 | B3. Missing Data Misinterpretation | Yes |
| 2.4 密集/广延型变量聚合错误 | D2. Spatial Allocation Error | Yes |
| 3.1 拓扑谓词语义混用 | C1. Topological Predicate Confusion | Yes |
| 3.2 脏数据缺乏拓扑修复 | C2. Invalid Geometry Handling | Yes |
| 3.3 网络拓扑与节点捕捉缺失 | C3. Network Connectivity Misinterpretation | Yes |
| 4.1 数据分段模型错位 | E1. Classification Scheme Misuse | Yes |
| 4.2 符号化与色彩滥用 | E2. Symbolization Error | Yes |
| 4.3 视觉排版与要素缺失 | E3. Map Composition Defect | Yes |
| 5.1 空间操作依赖断裂 | Workflow Dependency Omission | No; agent workflow failure |
| 5.2 局部与全局操作混淆 | D1. Aggregation Scope Confusion | Yes |
| 5.3 级联错误累积 | Error Propagation and Silent Failure | No; agent workflow failure |
| 6.1 空间索引机制遗漏 | Scalability / Indexing Failure | No; system execution failure |
| 6.2 内存外大栅格直接吞吐 | Memory Management Failure | No; system execution failure |

## Detectability and Observability as Evaluation Dimensions

为避免 taxonomy 与评价指标混杂，建议将“纯文本模态可检测性”和“可视化后的可观测性”作为分析维度，而不是分类维度。可在正文或附表中对每个二级类别补充如下判断：

| Level-2 Category | Text-only Detectability | Post-visualization Observability |
| :--- | :---: | :---: |
| A1. Coordinate Axis Misinterpretation | Low | High |
| A2. CRS Inconsistency | High | High |
| A3. Unit Misinterpretation | Low | High |
| B1. Dataset Integrity Violation | High | High |
| B2. Raster Alignment Failure | High | High |
| B3. Missing Data Misinterpretation | Low | Low |
| C1. Topological Predicate Confusion | Low | High |
| C2. Invalid Geometry Handling | High | High |
| C3. Network Connectivity Misinterpretation | Low | High |
| D1. Aggregation Scope Confusion | Low | Low |
| D2. Spatial Allocation Error | Low | Low |
| D3. Spatial Statistical Misinterpretation | Low | Low |
| E1. Classification Scheme Misuse | Low | High |
| E2. Symbolization Error | Low | High |
| E3. Map Composition Defect | Low | High |

## Agent Workflow Failures Beyond GIS Knowledge

The following failures are important in GIS agent workflows but should not be part of the core GIS-specific error taxonomy. They are not unique to GIS and can also occur in machine learning, database, computer vision, or general data-processing agents.

| Category | Subcategory | Typical Manifestation | Why It Is Outside the GIS-specific Taxonomy |
| :--- | :--- | :--- | :--- |
| **Workflow Errors** | **Dependency Omission** | Required preprocessing or intermediate construction steps are skipped, such as calling shortest path before graph construction | The same planning error occurs in non-GIS pipelines, such as evaluating a model before training |
| | **Error Propagation and Silent Failure** | `exit_code=0` but the output is semantically wrong; invalid intermediate products are consumed downstream | This is an agent orchestration and validation failure rather than a GIS knowledge error |
| **System Errors** | **Scalability / Indexing Failure** | Missing spatial index, bounding-box filtering, or chunking causes severe computational inefficiency | Although spatial indexes are common in GIS, the failure mode is a general computational scalability issue |
| | **Memory Management Failure** | Large rasters or vector datasets are loaded into memory at once, causing OOM | OOM is a system-level execution failure and is not specific to GIS domain reasoning |

## Suggested Paper Structure

```text
Section 4. Taxonomy of GIS-specific Errors
  A. Spatial Reference Errors
  B. Spatial Data Errors
  C. Spatial Reasoning Errors
  D. Spatial Analysis Errors
  E. Cartographic Errors

Section 5. Agent Workflow Failures Beyond GIS Knowledge
  Workflow Errors
  System Errors
```

## Suggested Paper Wording

> We define GIS-specific errors as failures rooted in GIS domain knowledge, including spatial reference systems, spatial data models, spatial reasoning, spatial analysis, and cartographic representation. General agent workflow failures, such as dependency omission, silent error propagation, memory exhaustion, and computational scalability failures, are analyzed separately because they are not unique to GIS and may occur in many agentic data-processing pipelines.

这样处理后，主 taxonomy 更接近 Longley、Burrough、Goodchild 等经典 GIS 知识结构，也更容易回应审稿人关于 “Why is OOM a GIS error?” 的质疑。
