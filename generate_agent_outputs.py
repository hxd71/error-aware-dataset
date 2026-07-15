"""
创建模拟 Agent 输出
====================
为 5 条任务生成模拟智能体输出，用于验证评测流水线。
- 001: 正确输出（预期 PASS）
- 002: 正确输出（预期 PASS）
- 003: 缺少字段（预期 FAIL, C1 错误）
- 004: 含无效几何（预期 FAIL, B1 错误）
- 005: CRS 不一致（预期 FAIL, A1, D3 错误）
"""
import os
import shutil
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.transform import from_bounds

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(OUT_DIR, "agent_outputs")
GT_DIR = os.path.join(OUT_DIR, "evaluation", "Ground_Truth")
os.makedirs(AGENT_DIR, exist_ok=True)

PROJ_LIB = "C:\\Users\\print_li\\AppData\\Roaming\\Python\\Python39\\site-packages\\rasterio\\proj_data"
os.environ["PROJ_LIB"] = PROJ_LIB

# ──────────────────────────────────────────────────────────
# Task 001: 正确输出 — 复制 GT 文件
# ──────────────────────────────────────────────────────────
print("[001] 生成正确 Agent 输出...")
case_dir = os.path.join(AGENT_DIR, "curated_geoagent_001")
os.makedirs(case_dir, exist_ok=True)
gt_vec = os.path.join(GT_DIR, "curated_geoagent_001", "expected_vector.geojson")
shutil.copy(gt_vec, os.path.join(case_dir, "buffered_roads.geojson"))
shutil.copy(os.path.join(GT_DIR, "curated_geoagent_001", "map.png"),
            os.path.join(case_dir, "buffered_roads_map.png"))
print("  → agent_outputs/curated_geoagent_001/ (预期 PASS)")

# ──────────────────────────────────────────────────────────
# Task 002: 正确输出 — 复制 GT 栅格
# ──────────────────────────────────────────────────────────
print("[002] 生成正确 Agent 输出...")
case_dir = os.path.join(AGENT_DIR, "curated_geoagent_002")
os.makedirs(case_dir, exist_ok=True)
gt_ras = os.path.join(GT_DIR, "curated_geoagent_002", "expected_raster.tif")
shutil.copy(gt_ras, os.path.join(case_dir, "slope.tif"))
print("  → agent_outputs/curated_geoagent_002/ (预期 PASS)")

# ──────────────────────────────────────────────────────────
# Task 003: 缺少字段 — 故意去掉 population 列
# ──────────────────────────────────────────────────────────
print("[003] 生成含错误 Agent 输出（缺少字段）...")
case_dir = os.path.join(AGENT_DIR, "curated_geoagent_003")
os.makedirs(case_dir, exist_ok=True)
gt_vec = os.path.join(GT_DIR, "curated_geoagent_003", "expected_vector.geojson")
gdf = gpd.read_file(gt_vec)
# 删除 population 列来制造 C1 错误
if "population" in gdf.columns:
    gdf = gdf.drop(columns=["population"])
gdf.to_file(os.path.join(case_dir, "population_by_admin.geojson"), driver="GeoJSON")
# 统计表也做一份
stats = pd.DataFrame({
    "admin_name": ["North District", "Central District", "South District"],
    "block_count": [10, 10, 10],
})
stats.to_csv(os.path.join(case_dir, "population_stats.csv"), index=False)
print("  → agent_outputs/curated_geoagent_003/ (预期 FAIL: C1 字段缺失)")

# ──────────────────────────────────────────────────────────
# Task 004: 含无效几何 — 直接复制陷阱数据不修复
# ──────────────────────────────────────────────────────────
print("[004] 生成含错误 Agent 输出（无效几何）...")
case_dir = os.path.join(AGENT_DIR, "curated_geoagent_004")
os.makedirs(case_dir, exist_ok=True)
trap_vec = os.path.join(OUT_DIR, "asset_fixes", "roads_with_invalid_geom.shp")
gdf = gpd.read_file(trap_vec)
# 不修复无效几何，直接输出
gdf.to_file(os.path.join(case_dir, "fixed_roads.geojson"), driver="GeoJSON")
# 统计表
stats = gdf.groupby("road_class").size().reset_index(name="count")
stats["total_length_km"] = [12.5, 8.3, 5.1]
stats.to_csv(os.path.join(case_dir, "road_length_stats.csv"), index=False)
invalid_cnt = (~gdf.geometry.is_valid).sum()
print(f"  → agent_outputs/curated_geoagent_004/ (预期 FAIL: B1, {invalid_cnt} 个无效几何)")

# ──────────────────────────────────────────────────────────
# Task 005: CRS 不匹配 — 保持 EPSG:4326 不重投影
# ──────────────────────────────────────────────────────────
print("[005] 生成含错误 Agent 输出（CRS不匹配）...")
case_dir = os.path.join(AGENT_DIR, "curated_geoagent_005")
os.makedirs(case_dir, exist_ok=True)
# 矢量保持 EPSG:4326，不重投影到 3857
landuse_vec = os.path.join(OUT_DIR, "asset_fixes", "landuse_epsg4326.shp")
gdf = gpd.read_file(landuse_vec)
gdf.to_file(os.path.join(case_dir, "landuse_rasterized.geojson"), driver="GeoJSON")
# 栅格：创建一个与 GT 范围不一致的栅格
lc_ras = os.path.join(OUT_DIR, "assets", "landcover_epsg3857.tif")
with rasterio.open(lc_ras) as src:
    data = src.read()
    profile = src.profile.copy()
# 故意偏移范围
profile["transform"] = from_bounds(
    -13641000, 4541000, -13611000, 4561000,
    profile["width"], profile["height"]
)
with rasterio.open(os.path.join(case_dir, "landuse_rasterized.tif"), "w", **profile) as dst:
    dst.write(data)
# 统计表
stats = pd.DataFrame({
    "landuse_type": ["residential", "commercial", "industrial", "park", "agriculture"],
    "area_ha": [120, 80, 60, 45, 200],
})
stats.to_csv(os.path.join(case_dir, "landuse_area_stats.csv"), index=False)
print(f"  → agent_outputs/curated_geoagent_005/ (预期 FAIL: A1-CRS不匹配, D3-范围偏差)")

print("\n✅ 模拟 Agent 输出生成完毕！")
print(f"   预期: 2 PASS (001, 002), 3 FAIL (003, 004, 005)")
