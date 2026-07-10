import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# Path to the local BigEarthNet Portugal stats JSON file
data_path = r"<LOCAL_REPO_ROOT>\external_task_runs\data\geonature\bigearthnet_portugal_stats.json"

# Load the JSON data
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract land cover composition for Beja
beja_lulc = None

# Attempt to handle various possible JSON structures
if isinstance(data, dict):
    # Check if the top-level dictionary has district names as keys
    if 'Beja' in data:
        district_data = data['Beja']
        if isinstance(district_data, dict):
            # Assume keys are class names, values are percentages
            beja_lulc = district_data.copy()
        elif isinstance(district_data, list):
            # List of dictionaries with class and percentage fields
            beja_lulc = {}
            for item in district_data:
                cls = item.get('class') or item.get('class_name') or item.get('label')
                pct = item.get('percentage') or item.get('percent') or item.get('value')
                if cls is not None and pct is not None:
                    beja_lulc[cls] = pct
    # Otherwise check if data contains a 'districts' list
    elif 'districts' in data:
        for d in data['districts']:
            if d.get('name') == 'Beja' or d.get('district') == 'Beja':
                lulc_data = d.get('land_cover') or d.get('lulc') or d.get('classes')
                if isinstance(lulc_data, list):
                    beja_lulc = {}
                    for item in lulc_data:
                        cls = item.get('class') or item.get('class_name') or item.get('label')
                        pct = item.get('percentage') or item.get('percent') or item.get('value')
                        if cls is not None and pct is not None:
                            beja_lulc[cls] = pct
                elif isinstance(lulc_data, dict):
                    beja_lulc = lulc_data.copy()
                break
elif isinstance(data, list):
    # List of district entries
    for d in data:
        if d.get('name') == 'Beja' or d.get('district') == 'Beja':
            lulc_data = d.get('land_cover') or d.get('lulc') or d.get('classes')
            if isinstance(lulc_data, list):
                beja_lulc = {}
                for item in lulc_data:
                    cls = item.get('class') or item.get('class_name') or item.get('label')
                    pct = item.get('percentage') or item.get('percent') or item.get('value')
                    if cls is not None and pct is not None:
                        beja_lulc[cls] = pct
            elif isinstance(lulc_data, dict):
                beja_lulc = lulc_data.copy()
            break

if beja_lulc is None:
    raise ValueError("Beja district data not found in the JSON file.")

# Prepare data as lists
classes = list(beja_lulc.keys())
percentages = [float(v) for v in beja_lulc.values()]

# Create a DataFrame and save as CSV
df = pd.DataFrame({'LandCoverClass': classes, 'Percentage': percentages})
df.to_csv('beja_lulc_breakdown.csv', index=False)

# Create summary: total number of classes, dominant class, total percentage
dominant_idx = percentages.index(max(percentages))
dominant_class = classes[dominant_idx]
dominant_pct = percentages[dominant_idx]
total_pct = sum(percentages)

summary = {
    'total_classes': len(classes),
    'dominant_class': dominant_class,
    'dominant_percentage': round(dominant_pct, 2),
    'sum_percentage': round(total_pct, 2),
    'classes': classes
}

# Save summary as JSON
with open('beja_lulc_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

# Create a bar chart of land cover composition
plt.figure(figsize=(10, 6))
plt.bar(classes, percentages)
plt.xlabel('Land Cover Class')
plt.ylabel('Percentage (%)')
plt.title('Land Cover Composition - Beja, Portugal')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('beja_lulc_chart.png', dpi=150)
plt.close()