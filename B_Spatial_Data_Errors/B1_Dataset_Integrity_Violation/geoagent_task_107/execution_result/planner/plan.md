# Fallback Plan

## 1. Task Overview
- **Task Description**: Please clip the uploaded target Shapefile layer (road.shp) according to the provided boundaries (area.shp) . Ensure that the clipped results include all original attribute fields and save it as a new Shapefile., Data files are stored under WORKING_DIRECTORY/data/.../...

## 2. SubTask 1: Execute User GIS Task
- **SubTask Description**: Please clip the uploaded target Shapefile layer (road.shp) according to the provided boundaries (area.shp) . Ensure that the clipped results include all original attribute fields and save it as a new Shapefile., Data files are stored under WORKING_DIRECTORY/data/.../...

### 2.1 Execution Steps:
1. Locate required input data from WORKING_DIRECTORY/data.
2. Implement and run Python GIS code to complete the user task directly.
3. Save outputs under the current subtask directory and verify results.

### 2.2 Method and Rationale:
- **Method**: Use planner and coder roles to execute the requested GIS workflow end-to-end.
- **Rationale**: A single concrete subtask reduces dispatch drift when planner LLM is unavailable.
