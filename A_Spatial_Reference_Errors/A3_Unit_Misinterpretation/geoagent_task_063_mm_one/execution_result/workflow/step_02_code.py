import geopandas as gpd
import pandas as pd
import json

# Simple HTML escape function (replaces non-approved html module)
def escape_html(s):
    if s is None:
        return ''
    s = str(s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

# Use artifact path from predefined binding
input_path = artifact_paths_by_name["penn_state_buildings_projected.gpkg"]
output_path = output_paths[0]

# Read the projected GPKG
gdf = gpd.read_file(input_path)

# Parse tags column (stored as string representation of dict)
def parse_tags(tag_str):
    if pd.isna(tag_str):
        return {}
    try:
        return eval(tag_str)
    except Exception:
        return {}

# Extract building information with name, id, and area
buildings = []
for idx, row in gdf.iterrows():
    tags = parse_tags(row.get('tags', ''))
    # Prefer 'name', fallback to 'short_name', then 'id'
    name = tags.get('name', tags.get('short_name', row.get('id', str(idx))))
    building_id = str(row.get('id', idx))
    area = row.geometry.area if row.geometry is not None else 0.0
    buildings.append({
        'name': name,
        'id': building_id,
        'area': area
    })

# Sort by area descending for readability
buildings.sort(key=lambda x: x['area'], reverse=True)

# Calculate summary statistics
total_buildings = len(buildings)
total_area = sum(b['area'] for b in buildings)

# Generate styled HTML report
html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Building Area Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .summary p {{ margin: 5px 0; font-size: 16px; }}
        .summary strong {{ color: #2980b9; }}
        table {{ border-collapse: collapse; width: 100%; background-color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .area-col {{ text-align: right; }}
        .area-header {{ text-align: right; }}
    </style>
</head>
<body>
    <h1>Building Area Report</h1>
    <div class="summary">
        <p><strong>Total Buildings:</strong> {total_buildings}</p>
        <p><strong>Total Area:</strong> {total_area:,.2f} square meters</p>
    </div>
    <table>
        <tr>
            <th>Building Name</th>
            <th>Building ID</th>
            <th class="area-header">Area (sq m)</th>
        </tr>
'''

for b in buildings:
    html_content += f'''        <tr>
            <td>{escape_html(str(b['name']))}</td>
            <td>{escape_html(str(b['id']))}</td>
            <td class="area-col">{b['area']:,.2f}</td>
        </tr>
'''

html_content += '''    </table>
</body>
</html>
'''

# Write HTML report to output path
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

# Print execution summary as JSON to stdout
print(json.dumps({
    "step_id": "step_02",
    "output_paths": [output_path],
    "buildings_processed": total_buildings,
    "total_area_sqm": total_area
}, indent=2))
