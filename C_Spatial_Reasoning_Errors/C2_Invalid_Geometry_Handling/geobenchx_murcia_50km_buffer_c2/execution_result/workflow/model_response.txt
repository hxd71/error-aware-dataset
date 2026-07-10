import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Load data
path = "data_source/spain_provinces.geojson"
gdf = gpd.read_file(path)

# Find Murcia province row – look through all string columns
murcia_row = None
for col in gdf.columns:
    if gdf[col].dtype == object:
        mask = gdf[col].str.lower().str.strip() == 'murcia'
        if mask.any():
            murcia_row = gdf[mask]
            break
if murcia_row is None or len(murcia_row) == 0:
    raise ValueError("Province 'Murcia' not found in any column.")
murcia_index = murcia_row.index[0]

# Project to EPSG:25830 (metre units, UTM zone 30N covering Spain)
gdf_proj = gdf.to_crs("EPSG:25830")
murcia_proj = gdf_proj.loc[murcia_index, 'geometry']

# Create 50 km buffer (50 000 m)
buffer_proj = murcia_proj.buffer(50000)

# Convert buffer to EPSG:4326 for output
buffer_geo = gpd.GeoSeries(buffer_proj, crs="EPSG:25830").to_crs("EPSG:4326")
buffer_geo.name = 'geometry'
buffer_gdf = gpd.GeoDataFrame(geometry=buffer_geo)
buffer_gdf.to_file("murcia_50km_buffer.geojson", driver='GeoJSON')

# Find all provinces intersecting the buffer (in projected CRS)
intersecting_mask = gdf_proj.intersects(buffer_proj)
intersecting_proj = gdf_proj[intersecting_mask]

# Convert intersecting provinces back to EPSG:4326 and save as CSV (excluding geometry)
intersecting_geo = intersecting_proj.to_crs("EPSG:4326")
csv_data = intersecting_geo.drop(columns='geometry').copy()
csv_data.to_csv("murcia_50km_intersecting_provinces.csv", index=False)

# --- Map plot ---
fig, ax = plt.subplots(1, 1, figsize=(10, 8))

# Spain provinces as light grey boundaries
gdf.boundary.plot(ax=ax, color='grey', linewidth=0.5, label='All provinces')

# Buffer as semi‑transparent blue
buffer_geo.plot(ax=ax, color='blue', alpha=0.2, edgecolor='blue',
                label='50 km buffer')

# Murcia province in red
murcia_4326 = gdf.loc[[murcia_index]]
murcia_4326.plot(ax=ax, color='red', alpha=0.5, edgecolor='black',
                 label='Murcia')

# Other intersecting provinces in orange
intersecting_others = intersecting_geo.drop(murcia_index, errors='ignore')
if not intersecting_others.empty:
    intersecting_others.plot(ax=ax, color='orange', alpha=0.5,
                             edgecolor='orange', label='Intersecting provinces')

ax.set_title("50 km buffer around Murcia & intersecting provinces")
ax.legend(loc='lower right')
ax.set_axis_off()
plt.tight_layout()
plt.savefig("murcia_50km_intersections_map.png", dpi=150, bbox_inches='tight')
plt.close()