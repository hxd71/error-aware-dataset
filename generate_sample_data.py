"""
生成合成样本空间数据
=====================
为 cases.json 中 5 条模板任务创建可用的合成 GIS 测试数据。
运行一次即可，后续 GT 生成和评测可直接使用。
"""
import os
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import Point, LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT_DIR, "assets")
FIXES = os.path.join(OUT_DIR, "asset_fixes")

os.makedirs(ASSETS, exist_ok=True)
os.makedirs(FIXES, exist_ok=True)

# ================================================================
# Task 001: 道路网络 → 缓冲区
# ================================================================
print("[001] 生成道路网络...")
roads = []
for i in range(20):
    x0, y0 = np.random.uniform(-122.52, -122.38), np.random.uniform(37.70, 37.82)
    pts = [(x0 + np.random.uniform(-0.02, 0.02), y0 + np.random.uniform(-0.02, 0.02)) for _ in range(np.random.randint(3, 8))]
    roads.append(LineString(pts))

road_gdf = gpd.GeoDataFrame({
    "road_id": range(1, 21),
    "road_class": np.random.choice(["highway", "arterial", "local"], 20),
    "name": [f"Road_{i}" for i in range(1, 21)],
    "lanes": np.random.randint(1, 5, 20),
}, geometry=roads, crs="EPSG:4326")
road_gdf.to_file(os.path.join(ASSETS, "roads.shp"))
print(f"  → assets/roads.shp ({len(road_gdf)} features)")

# ================================================================
# Task 002: DEM 栅格 → 坡度计算
# ================================================================
print("[002] 生成 DEM 栅格...")
width, height = 200, 200
x = np.linspace(-122.5, -122.3, width)
y = np.linspace(37.7, 37.9, height)
X, Y = np.meshgrid(x, y)
# 合成地形：两个山峰
dem = (3000 * np.exp(-((X + 122.42)**2 + (Y - 37.78)**2) / 0.0002) +
       2000 * np.exp(-((X + 122.36)**2 + (Y - 37.82)**2) / 0.00015) +
       np.random.normal(0, 10, (height, width)))
dem = dem.astype(np.float32)

transform = from_bounds(-122.5, 37.7, -122.3, 37.9, width, height)
profile = {
    "driver": "GTiff", "height": height, "width": width,
    "count": 1, "dtype": "float32", "crs": "EPSG:4326",
    "transform": transform, "nodata": -9999.0,
}
with rasterio.open(os.path.join(ASSETS, "dem.tif"), "w", **profile) as dst:
    dst.write(dem, 1)
print(f"  → assets/dem.tif ({width}x{height})")

# ================================================================
# Task 003: 人口普查区块 + 行政区划 → 空间连接
# ================================================================
print("[003] 生成普查区块和行政区划...")
# 3 个行政区
admin_polys = [
    box(-122.50, 37.70, -122.42, 37.82),
    box(-122.42, 37.70, -122.36, 37.82),
    box(-122.36, 37.70, -122.30, 37.82),
]
admin_gdf = gpd.GeoDataFrame({
    "admin_name": ["North District", "Central District", "South District"],
    "admin_code": ["ADM01", "ADM02", "ADM03"],
}, geometry=admin_polys, crs="EPSG:4326")
admin_gdf.to_file(os.path.join(ASSETS, "admin_boundaries.shp"))
print(f"  → assets/admin_boundaries.shp ({len(admin_gdf)} features)")

# 30 个普查区块（在行政区内随机撒点再 Voronoi 分区）
np.random.seed(42)
block_pts = []
block_admin = []
block_pop = []
for _, row in admin_gdf.iterrows():
    bounds = row.geometry.bounds
    for _ in range(10):
        px = np.random.uniform(bounds[0], bounds[2])
        py = np.random.uniform(bounds[1], bounds[3])
        pt = Point(px, py)
        if row.geometry.contains(pt):
            block_pts.append(pt)
            block_admin.append(row["admin_name"])
            block_pop.append(np.random.randint(500, 5000))

# 用简单的缓冲区作为区块面
block_polys = [pt.buffer(0.008) for pt in block_pts]
# 裁剪到行政区
block_polys_clipped = []
block_attrs = []
for i, (poly, admin, pop) in enumerate(zip(block_polys, block_admin, block_pop)):
    clipped = poly.intersection(admin_gdf[admin_gdf["admin_name"] == admin].geometry.iloc[0])
    if not clipped.is_empty:
        block_polys_clipped.append(clipped)
        block_attrs.append((i+1, admin, pop))

block_gdf = gpd.GeoDataFrame({
    "block_id": [a[0] for a in block_attrs],
    "admin_name": [a[1] for a in block_attrs],
    "population": [a[2] for a in block_attrs],
}, geometry=block_polys_clipped, crs="EPSG:4326")
block_gdf.to_file(os.path.join(ASSETS, "census_blocks.shp"))
print(f"  → assets/census_blocks.shp ({len(block_gdf)} features)")

# ================================================================
# Task 004: 陷阱 — 含无效几何的道路
# ================================================================
print("[004] 生成含无效几何的道路（陷阱数据）...")
trap_roads = []
for i in range(15):
    x0, y0 = np.random.uniform(-122.52, -122.38), np.random.uniform(37.70, 37.82)
    pts = [(x0 + np.random.uniform(-0.02, 0.02), y0 + np.random.uniform(-0.02, 0.02)) for _ in range(np.random.randint(3, 8))]
    trap_roads.append(LineString(pts))

# 注入一条自相交的无效道路线（折返形成自交）
invalid_road = LineString([
    (-122.45, 37.75), (-122.44, 37.77), (-122.46, 37.76),
    (-122.43, 37.74), (-122.45, 37.77), (-122.44, 37.75),
])
trap_roads.append(invalid_road)

# 再注入一个自相交多边形（蝴蝶结形 — 经典的无效几何）
from shapely.geometry.polygon import LinearRing
bowtie_ring = LinearRing([
    (-122.48, 37.71), (-122.46, 37.73), (-122.48, 37.73),
    (-122.46, 37.71), (-122.48, 37.71),
])
bowtie_poly = Polygon(bowtie_ring)
trap_roads.append(bowtie_poly)

n_trap = len(trap_roads)
trap_gdf = gpd.GeoDataFrame({
    "road_id": range(1, n_trap + 1),
    "road_class": np.random.choice(["highway", "arterial", "local"], n_trap),
    "name": [f"Trap_Road_{i}" for i in range(1, n_trap + 1)],
}, geometry=trap_roads, crs="EPSG:4326")
trap_gdf.to_file(os.path.join(FIXES, "roads_with_invalid_geom.shp"))
# 验证确实有无效几何
invalid_cnt = (~trap_gdf.geometry.is_valid).sum()
print(f"  → asset_fixes/roads_with_invalid_geom.shp ({len(trap_gdf)} features, {invalid_cnt} invalid)")

# ================================================================
# Task 005: 陷阱 — CRS不匹配
# ================================================================
print("[005] 生成CRS不匹配的陷阱数据...")
# 土地利用矢量 (EPSG:4326)
landuse_polys = [
    box(-122.50, 37.70, -122.44, 37.78),
    box(-122.44, 37.70, -122.38, 37.78),
    box(-122.38, 37.70, -122.30, 37.78),
    box(-122.50, 37.78, -122.44, 37.86),
    box(-122.44, 37.78, -122.38, 37.86),
]
landuse_gdf = gpd.GeoDataFrame({
    "landuse_id": range(1, 6),
    "landuse_type": ["residential", "commercial", "industrial", "park", "agriculture"],
    "area_ha": [120, 80, 60, 45, 200],
}, geometry=landuse_polys, crs="EPSG:4326")
landuse_gdf.to_file(os.path.join(FIXES, "landuse_epsg4326.shp"))
print(f"  → asset_fixes/landuse_epsg4326.shp ({len(landuse_gdf)} features, CRS=EPSG:4326)")

# 土地覆盖栅格 (EPSG:3857)
lc_width, lc_height = 150, 150
lc_data = np.random.choice([1, 2, 3, 4, 5], (lc_height, lc_width),
                           p=[0.3, 0.2, 0.15, 0.15, 0.2]).astype(np.uint8)
# 使用 EPSG:3857 范围（与4326不同）
lc_transform = from_bounds(
    -13640000, 4540000, -13610000, 4560000, lc_width, lc_height
)
lc_profile = {
    "driver": "GTiff", "height": lc_height, "width": lc_width,
    "count": 1, "dtype": "uint8", "crs": "EPSG:3857",
    "transform": lc_transform, "nodata": 255,
}
with rasterio.open(os.path.join(ASSETS, "landcover_epsg3857.tif"), "w", **lc_profile) as dst:
    dst.write(lc_data, 1)
print(f"  → assets/landcover_epsg3857.tif ({lc_width}x{lc_height}, CRS=EPSG:3857)")

print("\n✅ 所有合成数据生成完毕！")
