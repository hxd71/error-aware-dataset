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
| | **D2. Spatial Allocation Error** | Extensive or intensive variables transferred across zones without valid spatial weighting | MAUP-related errors; assigning polygon-level values to intersecting zones without area-weighted redistribution; sampling a polygon's centroid or using area as a proxy for county-level population density |
| | **D3. Spatial Statistical Misinterpretation** | Spatial dependence, heterogeneity, derived indicators, thresholds, or local/global statistics interpreted incorrectly | Treating spatially autocorrelated samples as independent; confusing local and global spatial statistics; omitting the statistical threshold that defines “significant” spatial change |
| **E. Cartographic Errors** | **E1. Classification Scheme Misuse** | Inappropriate classification method for the data distribution | Using equal interval for heavy-tailed variables where quantile or Jenks classification is needed |
| | **E2. Symbolization Error** | Visual variables inconsistent with data type or semantics | Applying continuous colormaps to categorical land-use classes; misleading ordinal interpretation |
| | **E3. Map Composition Defect** | Missing or defective cartographic elements, required context/thematic layers, or map deliverables needed for interpretation | Missing legend, scale bar, labels, required context layers, or unreadable class breaks; poor layout causing ambiguous map reading |


## Detectability and Observability as Evaluation Dimensions

为避免 taxonomy 与评价指标混杂，将“纯文本模态可检测性”和“可视化后的可观测性”作为分析维度，而不是分类维度。在正文或附表中对每个二级类别补充如下判断：

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

