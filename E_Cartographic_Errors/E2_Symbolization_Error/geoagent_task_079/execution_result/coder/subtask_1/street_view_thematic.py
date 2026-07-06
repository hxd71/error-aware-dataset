
# -*- coding: utf-8 -*-
"""
Street View Image Year Thematic Map Generator
---------------------------------------------
Reads the street_image shapefile, extracts the capture year,
and produces:
  1. A static PNG thematic map (matplotlib/geopandas)
  2. An interactive Folium HTML map with year-based layer toggles
"""

import os
import sys
import subprocess
import warnings
warnings.filterwarnings('ignore')

# ── Try to install folium if missing ────────────────────────────────────
try:
    import folium
except ImportError:
    print("folium not found; attempting pip install…")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'folium', '-q'])
    import folium
    print("  folium installed successfully.")

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

# ── Paths ───────────────────────────────────────────────────────────────
WORKING_DIRECTORY = os.getcwd()
SHAPEFILE_PATH = os.path.join(WORKING_DIRECTORY, 'data', 'street_image', 'street_image.shp')
SUBTASK_DIR = os.path.join(WORKING_DIRECTORY, 'coder', 'subtask_1')
os.makedirs(SUBTASK_DIR, exist_ok=True)

# ── 1. Read the shapefile ───────────────────────────────────────────────
print("Reading shapefile…")
gdf = gpd.read_file(SHAPEFILE_PATH, encoding='utf-8')
print(f"  Loaded {len(gdf):,} features, CRS: {gdf.crs}")

# ── 2. Extract year ─────────────────────────────────────────────────────
# The 'year' column is already pre-extracted; fallback to 'image_date' if needed
if 'year' in gdf.columns and gdf['year'].notna().all():
    print("  Using pre-existing 'year' column.")
    gdf['capture_year'] = gdf['year'].astype(int)
elif 'image_date' in gdf.columns:
    print("  Extracting year from 'image_date' column…")
    gdf['capture_year'] = gdf['image_date'].str.extract(r'(\d{4})').astype(int)
else:
    raise KeyError("Neither 'year' nor 'image_date' column found in the shapefile.")

# Determine year range
years = sorted(gdf['capture_year'].unique())
print(f"  Years found: {years}")

# ── 3. Build a discrete colormap for the years ──────────────────────────
n_years = len(years)
# Use 'tab10' qualitative colormap (works well for up to 10 classes; we have 9)
cmap = matplotlib.colormaps.get_cmap('tab10')
year_color_map = {yr: cmap(i) for i, yr in enumerate(years)}
gdf['color'] = gdf['capture_year'].map(year_color_map)

# Year → count for legend
year_counts = gdf['capture_year'].value_counts().sort_index()

# ── 4. Static thematic map ──────────────────────────────────────────────
print("Generating static thematic map…")
fig, ax = plt.subplots(figsize=(16, 12), dpi=200)

# Plot each year as a separate scatter layer for a clean legend
for yr in years:
    subset = gdf[gdf['capture_year'] == yr]
    ax.scatter(
        subset.geometry.x,
        subset.geometry.y,
        c=[year_color_map[yr]],
        s=3,
        label=f'{yr}  ({len(subset):,} pts)',
        edgecolors='none',
        alpha=0.85,
    )

ax.set_title(
    'Street View Image Locations by Capture Year\nColumbia, SC',
    fontsize=18,
    fontweight='bold',
    pad=18,
)
ax.set_xlabel('Longitude', fontsize=13)
ax.set_ylabel('Latitude', fontsize=13)

# Legend outside the plot
legend = ax.legend(
    loc='center left',
    bbox_to_anchor=(1.02, 0.5),
    title='Capture Year',
    title_fontsize=14,
    fontsize=11,
    markerscale=3,
    frameon=True,
    fancybox=True,
    shadow=True,
)

# Clean ticks
ax.tick_params(labelsize=11)
ax.grid(True, alpha=0.25, linestyle='--')

fig.tight_layout()

png_path = os.path.join(SUBTASK_DIR, 'street_view_years_thematic_map.png')
fig.savefig(png_path, dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"  Static map saved → {png_path}")

# ── 5. Interactive Folium map ───────────────────────────────────────────
print("Generating interactive Folium map…")

# Center the map on the mean coordinates
center_lat = gdf['lat'].mean() if 'lat' in gdf.columns else gdf.geometry.y.mean()
center_lon = gdf['lng'].mean() if 'lng' in gdf.columns else gdf.geometry.x.mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles='CartoDB positron',
    control_scale=True,
)

# Convert matplotlib RGBA (0-1) to hex for Folium
def rgba_to_hex(rgba_tuple):
    r, g, b = (int(255 * c) for c in rgba_tuple[:3])
    return f'#{r:02x}{g:02x}{b:02x}'

# Create one FeatureGroup per year for LayerControl
feature_groups = {}
for yr in years:
    fg = folium.FeatureGroup(name=f'{yr} ({year_counts[yr]:,})', show=True)
    feature_groups[yr] = fg
    m.add_child(fg)

# Get lat/lon columns (may be in geometry or separate columns)
use_geom = ('lat' not in gdf.columns) or ('lng' not in gdf.columns)

for _, row in gdf.iterrows():
    yr = row['capture_year']
    if use_geom:
        lat, lon = row.geometry.y, row.geometry.x
    else:
        lat, lon = row['lat'], row['lng']

    address = row.get('descriptio', '')
    img_date = row.get('image_date', '')
    pano_id = row.get('panoId', '')

    popup_html = (
        f'<b>Year:</b> {yr}<br>'
        f'<b>Address:</b> {address}<br>'
        f'<b>Date:</b> {img_date}<br>'
        f'<b>Lat/Lon:</b> {lat:.6f}, {lon:.6f}<br>'
        f'<b>PanoID:</b> {pano_id}'
    )

    folium.CircleMarker(
        location=[lat, lon],
        radius=3,
        color=rgba_to_hex(year_color_map[yr]),
        fill=True,
        fill_color=rgba_to_hex(year_color_map[yr]),
        fill_opacity=0.8,
        weight=0.5,
        popup=folium.Popup(popup_html, max_width=280),
    ).add_to(feature_groups[yr])

folium.LayerControl(collapsed=False).add_to(m)

html_path = os.path.join(SUBTASK_DIR, 'street_view_years_interactive.html')
m.save(html_path)
print(f"  Interactive map saved → {html_path}")

# ── Summary ─────────────────────────────────────────────────────────────
print("\nDone!  Summary:")
print(f"  Points mapped:   {len(gdf):,}")
print(f"  Year range:      {years[0]} – {years[-1]}")
print(f"  Years:           {years}")
for yr in years:
    print(f"    {yr}: {year_counts[yr]:,} points")
