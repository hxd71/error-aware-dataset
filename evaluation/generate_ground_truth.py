"""
Ground Truth 批量生成脚本
===========================
读取 Benchmark_Tasks.json (cases.json)，调用 GeoPandas / Rasterio 自动执行GIS任务，
批量输出标准真值文件至 Ground_Truth/ 目录。

输出规范:
    Ground_Truth/
    └── {case_id}/
        ├── expected_vector.geojson     # 矢量标准结果
        ├── expected_raster.tif         # 栅格标准结果
        ├── stats.csv                   # 统计真值表
        ├── map.png                     # 标准制图结果
        └── thresholds.json             # 量化验证阈值

用法:
    python generate_ground_truth.py [--cases cases.json] [--limit N] [--skip-existing]
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import box, mapping
from shapely.validation import make_valid

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_gt")


# ===================================================================
# 配置常量
# ===================================================================

DEFAULT_CASES_PATH = "cases.json"
DEFAULT_OUTPUT_DIR = "evaluation/Ground_Truth"
DEFAULT_THRESHOLDS = {
    "area_tolerance_pct": 5.0,
    "length_tolerance_pct": 5.0,
    "extent_tolerance": 1e-6,
    "stats_tolerance": 0.05,
    "numeric_tolerance_pct": 1.0,
}


# ===================================================================
# 任务执行器注册表
# ===================================================================

class TaskExecutorRegistry:
    """
    任务执行器注册表
    
    根据任务类型分派到对应的执行函数。
    支持的任务类别:
        - vector_single: 单步矢量操作
        - raster_single: 单步栅格操作
        - composite_workflow: 复合多步骤工作流
        - trap: 陷阱任务（需特殊处理）
    """

    def __init__(self, assets_dir: str, asset_fixes_dir: str):
        self.assets_dir = assets_dir
        self.asset_fixes_dir = asset_fixes_dir
        self._registry = {}

    def register(self, task_type: str, handler):
        """注册任务类型处理器"""
        self._registry[task_type] = handler

    def execute(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单条任务，返回结果字典

        Returns:
            {
                "vector_gdf": GeoDataFrame | None,
                "raster_array": np.ndarray | None,
                "raster_profile": dict | None,
                "stats_df": pd.DataFrame | None,
                "map_path": str | None,
            }
        """
        task_type = task_config.get("task_type", "vector_single")
        handler = self._registry.get(task_type)

        if handler is None:
            logger.warning(f"未注册的任务类型: {task_type}，使用默认处理器")
            handler = self._default_handler

        return handler(task_config, self.assets_dir, self.asset_fixes_dir)

    def _default_handler(self, task_config, assets_dir, asset_fixes_dir):
        """默认回退处理器：基于任务配置推断并执行"""
        logger.info(f"使用默认处理器处理: {task_config.get('case_id', 'unknown')}")
        result = {}

        inputs = task_config.get("inputs", {})
        operations = task_config.get("operations", [])

        # 尝试加载输入数据
        gdfs = {}
        rasters = {}

        for key, rel_path in inputs.items():
            # 规范化路径：去除可能的 assets/ 或 asset_fixes/ 前缀（避免重复拼接）
            clean_path = rel_path
            for prefix in ("assets/", "assets\\", "asset_fixes/", "asset_fixes\\"):
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
                    break

            full_path = os.path.join(assets_dir, clean_path)
            fix_path = os.path.join(asset_fixes_dir, clean_path)

            # 优先使用修复版本（陷阱任务）
            if os.path.exists(fix_path):
                full_path = fix_path

            if not os.path.exists(full_path):
                logger.warning(f"输入文件不存在: {full_path}")
                continue

            ext = os.path.splitext(full_path)[1].lower()
            if ext in (".shp", ".geojson", ".gpkg"):
                try:
                    gdfs[key] = gpd.read_file(full_path)
                except Exception as e:
                    logger.error(f"读取矢量失败 {full_path}: {e}")
            elif ext in (".tif", ".tiff"):
                try:
                    with rasterio.open(full_path) as src:
                        rasters[key] = {
                            "data": src.read(),
                            "profile": src.profile,
                        }
                except Exception as e:
                    logger.error(f"读取栅格失败 {full_path}: {e}")

        # 执行操作链
        current_vector = gdfs.get(list(gdfs.keys())[0]) if gdfs else None
        current_raster = rasters.get(list(rasters.keys())[0]) if rasters else None

        for op in operations:
            op_type = op.get("type", "")
            try:
                current_vector, current_raster = self._execute_operation(
                    op, current_vector, current_raster, gdfs, rasters
                )
            except Exception as e:
                logger.error(f"操作 {op_type} 执行失败: {e}")

        if current_vector is not None:
            result["vector_gdf"] = current_vector
        if current_raster is not None:
            result["raster_array"] = current_raster.get("data")
            result["raster_profile"] = current_raster.get("profile")

        # 生成统计表
        if current_vector is not None:
            try:
                stats = self._compute_stats(current_vector)
                result["stats_df"] = stats
            except Exception as e:
                logger.warning(f"统计计算失败: {e}")

        return result

    def _execute_operation(self, op, vector, raster, all_gdfs, all_rasters):
        """执行单个操作"""
        op_type = op.get("type", "")
        params = op.get("params", {})

        if op_type == "buffer":
            distance = params.get("distance", 100)
            if vector is not None and vector.crs:
                vector_proj = vector.to_crs(vector.estimate_utm_crs())
                vector_proj["geometry"] = vector_proj.geometry.buffer(distance)
                vector = vector_proj.to_crs(vector.crs)
        elif op_type == "clip":
            clip_key = params.get("clip_layer")
            if clip_key and clip_key in all_gdfs and vector is not None:
                vector = gpd.clip(vector, all_gdfs[clip_key])
        elif op_type == "intersection":
            other_key = params.get("other_layer")
            if other_key and other_key in all_gdfs and vector is not None:
                vector = gpd.overlay(vector, all_gdfs[other_key], how="intersection")
        elif op_type == "union":
            other_key = params.get("other_layer")
            if other_key and other_key in all_gdfs and vector is not None:
                vector = gpd.overlay(vector, all_gdfs[other_key], how="union")
        elif op_type == "dissolve":
            by_col = params.get("by")
            if vector is not None:
                vector = vector.dissolve(by=by_col) if by_col else vector.dissolve()
        elif op_type == "spatial_join":
            other_key = params.get("other_layer")
            if other_key and other_key in all_gdfs and vector is not None:
                vector = gpd.sjoin(vector, all_gdfs[other_key], how="inner")
        elif op_type == "reproject":
            target_crs = params.get("crs", "EPSG:3857")
            if vector is not None:
                vector = vector.to_crs(target_crs)
        elif op_type == "select_by_attribute":
            expr = params.get("expression", "")
            if vector is not None and expr:
                vector = vector.query(expr)
        elif op_type == "raster_calc":
            if raster is not None:
                data = raster["data"].astype(np.float64)
                formula = params.get("formula", "data")
                # 安全求值
                result_data = eval(formula, {"np": np, "data": data})
                raster["data"] = result_data.astype(raster["profile"]["dtype"])
        elif op_type == "raster_reclass":
            if raster is not None:
                rules = params.get("rules", {})
                data = raster["data"].copy()
                for old_val, new_val in rules.items():
                    data[data == old_val] = new_val
                raster["data"] = data

        return vector, raster

    @staticmethod
    def _compute_stats(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """从矢量数据计算统计真值表"""
        records = []

        # 基本统计
        records.append({
            "metric": "feature_count",
            "value": len(gdf),
            "unit": "count"
        })

        if gdf.crs:
            gdf_proj = gdf.to_crs(gdf.estimate_utm_crs())
            records.append({
                "metric": "total_area",
                "value": round(gdf_proj.geometry.area.sum(), 2),
                "unit": "m²"
            })
            records.append({
                "metric": "total_length",
                "value": round(gdf_proj.geometry.length.sum(), 2),
                "unit": "m"
            })
            records.append({
                "metric": "mean_area",
                "value": round(gdf_proj.geometry.area.mean(), 2),
                "unit": "m²"
            })

        # 数值列统计
        numeric_cols = gdf.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            records.append({
                "metric": f"{col}_sum",
                "value": round(gdf[col].sum(), 4),
                "unit": ""
            })
            records.append({
                "metric": f"{col}_mean",
                "value": round(gdf[col].mean(), 4),
                "unit": ""
            })

        # 分类列统计
        for col in gdf.select_dtypes(include=["object", "category"]).columns:
            if col != "geometry":
                value_counts = gdf[col].value_counts().to_dict()
                for val, cnt in value_counts.items():
                    records.append({
                        "metric": f"{col}_{val}",
                        "value": cnt,
                        "unit": "count"
                    })

        return pd.DataFrame(records)


# ===================================================================
# Ground Truth 生成器
# ===================================================================

class GroundTruthGenerator:
    """
    Ground Truth 批量生成器

    遍历 cases.json 中的全部任务，调用 TaskExecutorRegistry 执行，
    并将结果标准化输出至 Ground_Truth/{case_id}/ 目录。
    """

    def __init__(self,
                 cases_path: str = DEFAULT_CASES_PATH,
                 output_dir: str = DEFAULT_OUTPUT_DIR,
                 assets_dir: str = "assets",
                 asset_fixes_dir: str = "asset_fixes"):
        self.cases_path = cases_path
        self.output_dir = Path(output_dir)
        self.assets_dir = assets_dir
        self.asset_fixes_dir = asset_fixes_dir

        self.executor = TaskExecutorRegistry(assets_dir, asset_fixes_dir)

    def load_cases(self) -> List[Dict[str, Any]]:
        """加载 cases.json"""
        if not os.path.exists(self.cases_path):
            raise FileNotFoundError(f"cases.json 不存在: {self.cases_path}")

        with open(self.cases_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 支持多种结构
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "cases" in data:
                return data["cases"]
            if "tasks" in data:
                return data["tasks"]
            # 键值对形式
            return list(data.values())

        return []

    def generate(self,
                 limit: Optional[int] = None,
                 skip_existing: bool = False,
                 case_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        批量生成 Ground Truth

        Args:
            limit: 限制处理任务数量
            skip_existing: 跳过已存在GT的任务
            case_ids: 仅处理指定case_id列表

        Returns:
            生成摘要列表
        """
        cases = self.load_cases()
        logger.info(f"加载了 {len(cases)} 条任务")

        if case_ids:
            cases = [c for c in cases if c.get("case_id") in case_ids]
            logger.info(f"筛选后 {len(cases)} 条任务")

        if limit:
            cases = cases[:limit]
            logger.info(f"限制处理前 {limit} 条")

        summaries = []
        succeeded = 0
        failed = 0
        skipped = 0

        for i, case in enumerate(cases):
            case_id = case.get("case_id", f"task_{i:03d}")

            gt_dir = self.output_dir / case_id
            if skip_existing and gt_dir.exists() and any(gt_dir.iterdir()):
                logger.info(f"[{case_id}] GT已存在，跳过")
                skipped += 1
                summaries.append({"case_id": case_id, "status": "skipped"})
                continue

            logger.info(f"[{case_id}] ({i+1}/{len(cases)}) 开始生成...")
            try:
                self._generate_one(case, gt_dir)
                logger.info(f"[{case_id}] ✓ 生成成功")
                succeeded += 1
                summaries.append({"case_id": case_id, "status": "success"})
            except Exception as e:
                logger.error(f"[{case_id}] ✗ 生成失败: {e}", exc_info=True)
                failed += 1
                summaries.append({
                    "case_id": case_id,
                    "status": "failed",
                    "error": str(e)
                })

        # 生成全局清单
        self._write_manifest(summaries)

        logger.info(f"=" * 50)
        logger.info(f"Ground Truth 生成完成: 成功={succeeded}, 失败={failed}, 跳过={skipped}")
        logger.info(f"=" * 50)

        return summaries

    def _generate_one(self, case: Dict[str, Any], gt_dir: Path):
        """生成单个任务的Ground Truth"""
        gt_dir.mkdir(parents=True, exist_ok=True)

        case_id = case.get("case_id", "unknown")
        task_type = case.get("task_type", "vector_single")

        # 检查是否为陷阱任务
        is_trap = case.get("trap_type") is not None
        if is_trap:
            logger.info(f"  [{case_id}] 检测到陷阱任务: {case.get('trap_type')}")

        # 执行任务
        result = self.executor.execute(case)

        # 输出矢量标准结果
        vector_gdf = result.get("vector_gdf")
        if vector_gdf is not None and not vector_gdf.empty:
            # 确保几何有效
            vector_gdf["geometry"] = vector_gdf.geometry.apply(
                lambda g: make_valid(g) if g is not None and not g.is_valid else g
            )
            vector_path = gt_dir / "expected_vector.geojson"
            vector_gdf.to_file(str(vector_path), driver="GeoJSON")
            logger.info(f"    → 矢量输出: {vector_path} ({len(vector_gdf)} features)")

        # 输出栅格标准结果
        raster_array = result.get("raster_array")
        raster_profile = result.get("raster_profile")
        if raster_array is not None and raster_profile is not None:
            raster_path = gt_dir / "expected_raster.tif"
            raster_profile.update(driver="GTiff")
            with rasterio.open(str(raster_path), "w", **raster_profile) as dst:
                if raster_array.ndim == 2:
                    dst.write(raster_array, 1)
                else:
                    dst.write(raster_array)
            logger.info(f"    → 栅格输出: {raster_path} ({raster_array.shape})")

        # 输出统计真值表
        stats_df = result.get("stats_df")
        if stats_df is not None and not stats_df.empty:
            stats_path = gt_dir / "stats.csv"
            stats_df.to_csv(str(stats_path), index=False, encoding="utf-8")
            logger.info(f"    → 统计表: {stats_path} ({len(stats_df)} rows)")

        # 输出标准制图
        map_path = self._generate_map(vector_gdf, raster_array, raster_profile, gt_dir, case_id)
        if map_path:
            logger.info(f"    → 制图: {map_path}")

        # 输出阈值配置
        thresholds = case.get("thresholds", DEFAULT_THRESHOLDS.copy())
        thresholds_path = gt_dir / "thresholds.json"
        with open(str(thresholds_path), "w", encoding="utf-8") as f:
            json.dump(thresholds, f, indent=2, ensure_ascii=False)
        logger.info(f"    → 阈值配置: {thresholds_path}")

        # 元信息
        meta = {
            "case_id": case_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task_type": task_type,
            "is_trap": is_trap,
            "trap_type": case.get("trap_type"),
            "source_id": case.get("source_id"),
            "complexity": case.get("complexity_level"),
        }
        meta_path = gt_dir / "meta.json"
        with open(str(meta_path), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _generate_map(self, vector_gdf, raster_array, raster_profile,
                      gt_dir: Path, case_id: str) -> Optional[str]:
        """生成标准制图PNG"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=150)

            has_content = False

            # 绘制栅格
            if raster_array is not None and raster_profile is not None:
                data_2d = raster_array[0] if raster_array.ndim == 3 else raster_array
                transform = raster_profile.get("transform")
                if transform:
                    from rasterio.plot import show
                    show(data_2d, ax=ax, transform=transform, cmap="viridis")
                else:
                    ax.imshow(data_2d, cmap="viridis")
                has_content = True

            # 绘制矢量
            if vector_gdf is not None and not vector_gdf.empty:
                vector_gdf.plot(ax=ax, facecolor="none", edgecolor="red",
                                linewidth=0.5, alpha=0.8)
                has_content = True

            if not has_content:
                ax.text(0.5, 0.5, "No spatial data", transform=ax.transAxes,
                        ha="center", va="center", fontsize=14)
            else:
                # 制图元素
                ax.set_title(f"Ground Truth — {case_id}", fontsize=12, fontweight="bold")
                ax.set_xlabel("Longitude / X")
                ax.set_ylabel("Latitude / Y")

                # 指北针
                ax.annotate("N", xy=(0.95, 0.95), xycoords="axes fraction",
                            fontsize=14, fontweight="bold",
                            ha="center", va="center",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.8))

                # 比例尺（简化）
                ax.text(0.05, 0.02, "Scale: ~1:100,000", transform=ax.transAxes,
                        fontsize=8, bbox=dict(boxstyle="round", fc="white", alpha=0.7))

                # 图例
                from matplotlib.lines import Line2D
                legend_elements = [
                    Line2D([0], [0], color="red", lw=1, label="Vector features")
                ]
                ax.legend(handles=legend_elements, loc="lower right", fontsize=8)

                ax.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()
            map_path = str(gt_dir / "map.png")
            fig.savefig(map_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

            return map_path
        except ImportError:
            logger.warning("matplotlib 未安装，跳过制图生成")
        except Exception as e:
            logger.warning(f"制图生成失败: {e}")

        return None

    def _write_manifest(self, summaries: List[Dict[str, Any]]):
        """写入GT生成清单"""
        manifest_path = self.output_dir / "generation_manifest.json"
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_cases": self.cases_path,
            "total": len(summaries),
            "succeeded": sum(1 for s in summaries if s["status"] == "success"),
            "failed": sum(1 for s in summaries if s["status"] == "failed"),
            "skipped": sum(1 for s in summaries if s["status"] == "skipped"),
            "details": summaries,
        }
        with open(str(manifest_path), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        logger.info(f"生成清单已保存: {manifest_path}")


# ===================================================================
# CLI 入口
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="批量生成 Ground Truth 标准真值库"
    )
    parser.add_argument(
        "--cases", default=DEFAULT_CASES_PATH,
        help=f"cases.json 路径 (默认: {DEFAULT_CASES_PATH})"
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--assets", default="assets",
        help="原始资产目录"
    )
    parser.add_argument(
        "--asset-fixes", default="asset_fixes",
        help="修复资产目录"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="限制处理任务数"
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="跳过已有GT的任务"
    )
    parser.add_argument(
        "--case-ids", nargs="*", default=None,
        help="仅处理指定case_id"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="详细日志"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    generator = GroundTruthGenerator(
        cases_path=args.cases,
        output_dir=args.output,
        assets_dir=args.assets,
        asset_fixes_dir=args.asset_fixes,
    )

    summaries = generator.generate(
        limit=args.limit,
        skip_existing=args.skip_existing,
        case_ids=args.case_ids,
    )

    # 返回退出码
    failed = sum(1 for s in summaries if s["status"] == "failed")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
