
# -*- coding: utf-8 -*-
import os
import geopandas as gpd
import pandas as pd

# Use __file__ to reliably locate the project root (WORKING_DIRECTORY)
# Script is at: WORKING_DIRECTORY/coder/subtask_1/aggregate_obesity.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
SUBTASK_DIR = os.path.dirname(os.path.abspath(__file__))  # coder/subtask_1

print(f"Working directory: {WORKING_DIRECTORY}")
print(f"Subtask directory: {SUBTASK_DIR}")

# Load the shapefile - resolve from WORKING_DIRECTORY/data
shp_path = os.path.join(WORKING_DIRECTORY, 'data', 'US_Counties', 'US_Counties.shp')
print(f"Reading shapefile from: {shp_path}")

if not os.path.exists(shp_path):
    raise FileNotFoundError(f"Shapefile not found at: {shp_path}")

gdf = gpd.read_file(shp_path)

print(f"Loaded {len(gdf)} features.")
print(f"Columns: {list(gdf.columns)}")

# Convert Obesity and Population from strings to numeric
gdf['Obesity_num'] = pd.to_numeric(gdf['Obesity'], errors='coerce')
gdf['Population_num'] = pd.to_numeric(gdf['Population'], errors='coerce')

# Report any conversion issues
obesity_nan = gdf['Obesity_num'].isna().sum()
pop_nan = gdf['Population_num'].isna().sum()
print(f"Obesity missing after conversion: {obesity_nan}")
print(f"Population missing after conversion: {pop_nan}")

# Drop rows where either Obesity or Population is missing
gdf_clean = gdf.dropna(subset=['Obesity_num', 'Population_num']).copy()
print(f"Rows after dropping NaNs: {len(gdf_clean)}")

# Compute obese population per county: (Obesity% / 100) * Population
gdf_clean['Obese_Population'] = (gdf_clean['Obesity_num'] / 100.0) * gdf_clean['Population_num']

# Aggregate by State
state_agg = gdf_clean.groupby('State').agg(
    Total_Population=('Population_num', 'sum'),
    Total_Obese_Population=('Obese_Population', 'sum'),
    County_Count=('State', 'count'),
    Avg_Obesity_Pct=('Obesity_num', 'mean')
).reset_index()

# Round for readability
state_agg['Total_Population'] = state_agg['Total_Population'].round(0).astype(int)
state_agg['Total_Obese_Population'] = state_agg['Total_Obese_Population'].round(0).astype(int)
state_agg['Avg_Obesity_Pct'] = state_agg['Avg_Obesity_Pct'].round(2)

# Sort by state name
state_agg = state_agg.sort_values('State').reset_index(drop=True)

print("\n===== AGGREGATED RESULTS =====")
print(state_agg.to_string(index=False))

# Save to subtask folder
output_csv = os.path.join(SUBTASK_DIR, 'state_obesity_aggregation.csv')
state_agg.to_csv(output_csv, index=False)
print(f"\nResults saved to: {output_csv}")

# Also save a summary text file
summary_txt = os.path.join(SUBTASK_DIR, 'state_obesity_summary.txt')
with open(summary_txt, 'w', encoding='utf-8') as f:
    f.write("===== State-Level Obesity Aggregation =====\n\n")
    f.write(state_agg.to_string(index=False))
    f.write(f"\n\nTotal states: {len(state_agg)}\n")
    f.write(f"Total counties processed: {len(gdf_clean)}\n")
print(f"Summary saved to: {summary_txt}")
