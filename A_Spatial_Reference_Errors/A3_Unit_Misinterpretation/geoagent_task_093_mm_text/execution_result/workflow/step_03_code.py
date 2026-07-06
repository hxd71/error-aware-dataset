from src.tools.report_tools import write_text_report
import pandas as pd

# Read the input CSV
input_csv = artifact_paths_by_name["county_boundary_lengths.csv"]
df = pd.read_csv(input_csv)

# Sort by county NAME
df_sorted = df.sort_values(by="NAME")

# Calculate summary statistics
total_counties = len(df_sorted)
mean_boundary = df_sorted["boundary_km"].mean()

# Build HTML content
html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>County Boundary Lengths</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>County Boundary Lengths</h1>
    </div>
    
    <div class="summary">
        <p><strong>Total Counties:</strong> {total_counties}</p>
        <p><strong>Mean Boundary Length:</strong> {mean_boundary:.2f} km</p>
        <p><strong>Total Boundary Length:</strong> {df_sorted["boundary_km"].sum():.2f} km</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>County Name</th>
                <th>Boundary (km)</th>
            </tr>
        </thead>
        <tbody>
'''

# Add rows sorted by county name
for _, row in df_sorted.iterrows():
    html_content += f'            <tr><td>{row["NAME"]}</td><td>{row["boundary_km"]:.2f}</td></tr>\n'

html_content += '''        </tbody>
    </table>
    
    <div class="footer">
        <p>Generated from county_boundary_lengths.csv</p>
    </div>
</body>
</html>
'''

# Write HTML file using the helper
output_path = output_paths[0]
write_text_report(html_content, output_path=output_path)

print(json.dumps({
    "step_id": "step_03",
    "output": output_path,
    "counties_reported": total_counties,
    "mean_boundary_km": round(mean_boundary, 2)
}))
