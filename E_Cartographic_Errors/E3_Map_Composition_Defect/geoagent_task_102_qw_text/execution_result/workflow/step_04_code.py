import json
import geopandas as gpd
import matplotlib.pyplot as plt

proposed_path = artifact_paths_by_name["proposed_walmart_location.shp"]
existing_path = current_step_assets_by_id["walmart_4_site_epsg32111"]["path"]
output_path = output_paths[0]

proposed_gdf = gpd.read_file(proposed_path)
existing_gdf = gpd.read_file(existing_path)

fig, ax = plt.subplots(figsize=(8, 8))
existing_gdf.plot(ax=ax, color="blue", markersize=80, label="Existing Walmarts")
proposed_gdf.plot(ax=ax, color="red", markersize=120, label="Proposed Location")

ax.set_title("Walmart Site Proposal Map")
ax.legend()
ax.axis("off")

fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(json.dumps({"status": "success", "output": output_path}))