# Fallback Plan

## 1. Task Overview
- **Task Description**: Please analyze the provided DEM and road data to identify areas suitable for camping based on the following criteria: (1) Calculate the terrain aspect from the DEM, and include areas where the aspect value is greater than 100 degrees. (2) Compute the distance of each point in the DEM to the closest road using the provided road shapefile, and retain areas within 1000 meters of a road. (3) Combine these two conditions to save the output as a raster file and generate a suitability map., Data files are stored under WORKING_DIRECTORY/data/.../...

## 2. SubTask 1: Execute User GIS Task
- **SubTask Description**: Please analyze the provided DEM and road data to identify areas suitable for camping based on the following criteria: (1) Calculate the terrain aspect from the DEM, and include areas where the aspect value is greater than 100 degrees. (2) Compute the distance of each point in the DEM to the closest road using the provided road shapefile, and retain areas within 1000 meters of a road. (3) Combine these two conditions to save the output as a raster file and generate a suitability map., Data files are stored under WORKING_DIRECTORY/data/.../...

### 2.1 Execution Steps:
1. Locate required input data from WORKING_DIRECTORY/data.
2. Implement and run Python GIS code to complete the user task directly.
3. Save outputs under the current subtask directory and verify results.

### 2.2 Method and Rationale:
- **Method**: Use planner and coder roles to execute the requested GIS workflow end-to-end.
- **Rationale**: A single concrete subtask reduces dispatch drift when planner LLM is unavailable.
