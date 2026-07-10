import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# File paths (absolute, as provided)
data_dir = Path("<LOCAL_REPO_ROOT>/external_task_runs/data/geonature")
province_rankings_path = data_dir / "province_rankings.json"
admin_index_path = data_dir / "spain_admin_index.json"

# Load administrative index and filter for Andalucía provinces
with open(admin_index_path, 'r') as f:
    admin_data = json.load(f)
# Assume admin_data is a list of objects with at least 'province_name' and 'ccaa_name'
# Convert to DataFrame for easier filtering
admin_df = pd.DataFrame(admin_data)
# Filter
andalucia_provinces = admin_df[admin_df['ccaa_name'] == 'Andalucía']['province_name'].tolist()

# Load province rankings (expected structure: list of dicts with 'province' and 'eligible_pct')
with open(province_rankings_path, 'r') as f:
    rankings_data = json.load(f)
rankings_df = pd.DataFrame(rankings_data)
# Filter for only those provinces in Andalucía
# Ensure consistent name matching (e.g., strip whitespace, handle accents if needed)
# We'll assume exact match. But to be safe, we'll strip and compare.
rankings_df['province_clean'] = rankings_df['province'].str.strip()
admin_clean = [p.strip() for p in andalucia_provinces]
# Create a set for fast lookup
admin_set = set(admin_clean)
andalucia_rankings = rankings_df[rankings_df['province_clean'].isin(admin_set)].copy()

# If multiple entries per province? Average eligible_pct per province? Task says average eligible_pct across provinces, so we assume one record per province. If duplicates, we take first or mean per province? 
# We'll assume no duplicates, but to be safe, group by province_clean and take mean.
province_mean = andalucia_rankings.groupby('province_clean')['eligible_pct'].mean().reset_index()
province_mean.columns = ['province', 'eligible_pct']

# Compute overall average
average_pct = province_mean['eligible_pct'].mean()

# Save CSV
province_mean[['province', 'eligible_pct']].to_csv('andalucia_co2_province_values.csv', index=False)

# Save JSON
with open('andalucia_co2_average.json', 'w') as f:
    json.dump({'average_eligible_pct': average_pct}, f)

# Bar chart
plt.figure(figsize=(10, 6))
plt.bar(province_mean['province'], province_mean['eligible_pct'], color='skyblue')
plt.xlabel('Province')
plt.ylabel('CO2 Storage Eligibility (%)')
plt.title('CO2 Storage Eligibility in Andalucía Provinces')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('andalucia_co2_average_chart.png')
plt.close()

print(f"Average CO2 storage eligibility: {average_pct:.2f}%")
print("Outputs saved: andalucia_co2_province_values.csv, andalucia_co2_average.json, andalucia_co2_average_chart.png")