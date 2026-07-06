# -*- coding: utf-8 -*-
"""
Street View Image Location Year Thematic Map
---------------------------------------------
Extracts year from image_date column, assigns distinct colors per year,
and renders a themed point map of street view image locations.
"""

import os
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams

# ============================================================
# 0. Setup paths
# ============================================================
WORKING_DIRECTORY = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
# Since we are running inside coder/subtask_1/, go up two levels to reach the root
# Actually WORKING_DIRECTORY is the root where data/ lives.
# The execution CWD is typically the subtask folder. We'll use a robust approach:
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBTASK_DIR = SCRIPT_DIR  # coder/subtask_1/
WORKING_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

DATA_DIR = os.path.join(WORKING_DIRECTORY, 'data', 'street_image')
SHP_PATH = os.path.join(DATA_DIR, 'street_image.shp')

OUTPUT_DIR = SUBTASK_DIR

print(f"Working Directory: {WORKING_DIRECTORY}")
print(f"Shapefile Path:   {SHP_PATH}")
print(f"Output Directory: {OUTPUT_DIR}")

# ============================================================
# 1. Load the shapefile
# ============================================================
print("\n[1/5] Loading shapefile...")
gdf = gpd.read_file(SHP_PATH)
print(f"  Loaded {len(gdf):,} features.")
print(f"  CRS: {gdf.crs}")
print(f"  Columns: {list(gdf.columns)}")

# ============================================================
# 2. Extract year from image_date column
# ============================================================
print("\n[2/5] Extracting year from 'image_date' column...")

# Check if 'year' column already exists
if 'year' not in gdf.columns:
    # image_date format: "YYYY-M" or "YYYY-MM"
    gdf['year'] = gdf['image_date'].astype(str).str.extract(r'(\d{4})').astype(int)
    print("  Year extracted from 'image_date'.")
else:
    print("  'year' column already exists — using it directly.")

# Clean: drop any rows with missing year
gdf = gdf.dropna(subset=['year'])
gdf['year'] = gdf['year'].astype(int)

years = sorted(gdf['year'].unique())
year_counts = gdf['year'].value_counts().sort_index()
print(f"  Unique years found: {years}")
print(f"  Year distribution:")
for yr in years:
    print(f"    {yr}: {year_counts[yr]:,} points")

# ============================================================
# 3. Assign colors per year using a perceptually distinct colormap
# ============================================================
print("\n[3/5] Assigning colors per year...")

num_years = len(years)
# Use a qualitative colormap (tab10, tab20) for distinct categorical colors
if num_years <= 10:
    cmap = plt.cm.tab10
elif num_years <= 20:
    cmap = plt.cm.tab20
else:
    cmap = plt.cm.gist_rainbow

# Build color mapping
color_map = {}
for i, yr in enumerate(years):
    color_map[yr] = cmap(i / max(num_years - 1, 1))

gdf['color'] = gdf['year'].map(color_map)

print(f"  Color map: { {yr: f'#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}' for yr, c in color_map.items()} }")

# ============================================================
# 4. Create the themed map
# ============================================================
print("\n[4/5] Rendering themed map...")

rcParams['font.family'] = 'sans-serif'
rcParams['font.size'] = 10

fig, ax = plt.subplots(figsize=(16, 12), dpi=200)

# Plot points
scatter = ax.scatter(
    gdf['lng'],
    gdf['lat'],
    c=gdf['color'],
    s=1.5,          # small point size for dense data
    alpha=0.7,
    edgecolors='none',
    linewidth=0
)

# Format axes
ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)
ax.set_title(
    'Street View Image Locations by Year — Columbia, SC',
    fontsize=16,
    fontweight='bold',
    pad=15
)

# Add grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Add legend
legend_patches = []
for yr in years:
    legend_patches.append(
        mpatches.Patch(color=color_map[yr], label=f'{yr} ({year_counts[yr]:,} pts)')
    )

legend = ax.legend(
    handles=legend_patches,
    title='Image Year',
    loc='center left',
    bbox_to_anchor=(1.02, 0.5),
    frameon=True,
    fancybox=True,
    shadow=True,
    fontsize=8,
    title_fontsize=10,
    ncol=1 if num_years <= 12 else 2
)

# Tight layout with room for legend
plt.tight_layout()

# Save
png_path = os.path.join(OUTPUT_DIR, 'street_view_years_thematic_map.png')
fig.savefig(png_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"  Map saved to: {png_path}")

# ============================================================
# 5. Create an interactive HTML map with folium (optional, richer output)
# ============================================================
print("\n[5/5] Creating interactive Folium map...")

try:
    import folium
    from folium import FeatureGroup, LayerControl

    # Center on data centroid
    center_lat = gdf['lat'].mean()
    center_lng = gdf['lng'].mean()

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=14,
        tiles='CartoDB positron',
        control_scale=True
    )

    # Add each year as a separate FeatureGroup for toggling
    for yr in years:
        yr_gdf = gdf[gdf['year'] == yr]
        # Convert matplotlib RGBA to hex
        rgba = color_map[yr]
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgba[0] * 255),
            int(rgba[1] * 255),
            int(rgba[2] * 255)
        )

        fg = FeatureGroup(name=f'{yr} ({len(yr_gdf):,} points)', show=True)

        for _, row in yr_gdf.iterrows():
            popup_text = (
                f"<b>Year:</b> {int(row['year'])}<br>"
                f"<b>Address:</b> {row.get('descriptio', 'N/A')}<br>"
                f"<b>Date:</b> {row.get('image_date', 'N/A')}<br>"
                f"<b>Lat/Lon:</b> {row['lat']:.5f}, {row['lng']:.5f}"
            )
            folium.CircleMarker(
                location=[row['lat'], row['lng']],
                radius=3,
                color=hex_color,
                fill=True,
                fill_color=hex_color,
                fill_opacity=0.7,
                weight=0.5,
                popup=folium.Popup(popup_text, max_width=250)
            ).add_to(fg)

        fg.add_to(m)

    LayerControl(collapsed=False).add_to(m)

    html_path = os.path.join(OUTPUT_DIR, 'street_view_years_interactive.html')
    m.save(html_path)
    print(f"  Interactive map saved to: {html_path}")

except ImportError:
    print("  Folium not installed — skipping interactive map. Install with: pip install folium")

print("\nDone! Thematic maps created successfully.")
