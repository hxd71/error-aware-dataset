# -*- coding: utf-8 -*-
"""
Bar chart showing obesity prevalence in the United States.
Aggregates county-level obesity data to state-level means,
then produces a clear, labeled horizontal bar chart.
"""

import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# 1.  Resolve paths
# ---------------------------------------------------------------------------
WORKING_DIRECTORY = os.getcwd()
data_path = os.path.join(WORKING_DIRECTORY, "data", "US_Counties", "US_Counties.shp")
output_dir = os.path.join(WORKING_DIRECTORY, "coder", "subtask_1")
os.makedirs(output_dir, exist_ok=True)
output_png = os.path.join(output_dir, "obesity_prevalence_barchart.png")

# ---------------------------------------------------------------------------
# 2.  Read the shapefile
# ---------------------------------------------------------------------------
gdf = gpd.read_file(data_path)

# ---------------------------------------------------------------------------
# 3.  Convert Obesity column to float (it is stored as string)
# ---------------------------------------------------------------------------
gdf["Obesity"] = pd.to_numeric(gdf["Obesity"], errors="coerce")

# Drop rows where Obesity could not be converted
gdf_clean = gdf.dropna(subset=["Obesity", "StateAbbr"])

# ---------------------------------------------------------------------------
# 4.  Aggregate to state-level mean obesity prevalence
# ---------------------------------------------------------------------------
state_stats = (
    gdf_clean.groupby("StateAbbr")["Obesity"]
    .agg(["mean", "count"])
    .reset_index()
    .sort_values("mean", ascending=True)  # ascending for horizontal bar
)

# ---------------------------------------------------------------------------
# 5.  Plot  --  horizontal bar chart for readability
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 14))

bars = ax.barh(state_stats["StateAbbr"], state_stats["mean"],
               color="steelblue", edgecolor="white", linewidth=0.5, height=0.75)

# Add value labels at the end of each bar
for i, (bar, val) in enumerate(zip(bars, state_stats["mean"])):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=8, color="black")

# ---------------------------------------------------------------------------
# 6.  Styling and clear labels
# ---------------------------------------------------------------------------
ax.set_xlabel("Obesity Prevalence (%)", fontsize=13, fontweight="bold")
ax.set_ylabel("State", fontsize=13, fontweight="bold")
ax.set_title("Obesity Prevalence by U.S. State\n(County-Level Mean Aggregated by State)",
             fontsize=15, fontweight="bold", pad=15)
ax.set_xlim(0, state_stats["mean"].max() + 4)
ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
ax.tick_params(axis="both", labelsize=10)
ax.grid(axis="x", alpha=0.35, linestyle="--")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(output_png, dpi=200, bbox_inches="tight")
plt.close()

print(f"Bar chart saved to: {output_png}")
print(f"Number of states plotted: {len(state_stats)}")
print(f"Mean obesity range: {state_stats['mean'].min():.1f}% – {state_stats['mean'].max():.1f}%")
print("Done.")
