"""
GIS Evaluator — 自动化核验主程序 (GIS Verifier)
====================================================
基于 Ground Truth 标准真值库完成矢量、栅格、表格、可视化四层比对逻辑。

主入口:
    evaluate(agent_output_path, truth_path, task_config) -> dict

核验四大分支:
    ① VectorVerifier    — 矢量核验: CRS、几何有效性、要素数量、面积/长度、属性字段
    ② RasterVerifier    — 栅格核验: 波段、分辨率、空间范围、NoData、统计指标
    ③ TableVerifier     — 属性统计表核验: 字段名、分组统计、数值匹配
    ④ VisualVerifier    — 可视化隐形错误核验: 图层错位、空白输出、制图元素缺失

输出: 标准化评估报告 dict，符合 evaluation_schema.json 规范
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np

from .error_classifier import ErrorClassifier, ErrorLabel

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logger = logging.getLogger("gis_evaluator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_h)


# ===================================================================
# 矢量核验器
# ===================================================================

class VectorVerifier:
    """矢量数据核验器：对比Agent输出矢量与Ground Truth矢量"""

    def __init__(self, area_tolerance_pct: float = 5.0, length_tolerance_pct: float = 5.0):
        """
        Args:
            area_tolerance_pct: 面积相对误差容差百分比
            length_tolerance_pct: 长度相对误差容差百分比
        """
        self.area_tolerance_pct = area_tolerance_pct
        self.length_tolerance_pct = length_tolerance_pct

    def verify(self, agent_path: Optional[str], truth_path: str) -> Dict[str, Any]:
        """
        执行矢量核验

        Args:
            agent_path: 智能体输出矢量文件路径（.shp/.geojson/.gpkg）
            truth_path: Ground Truth矢量文件路径

        Returns:
            矢量核验结果字典
        """
        result = {
            "file_exists": False,
            "crs_match": False,
            "crs_agent": None,
            "crs_expected": None,
            "geometry_valid": False,
            "invalid_geometry_count": 0,
            "feature_count_match": False,
            "feature_count_agent": 0,
            "feature_count_expected": 0,
            "area_error_pct": None,
            "length_error_pct": None,
            "area_within_tolerance": False,
            "length_within_tolerance": False,
            "attribute_fields_match": False,
            "missing_fields": [],
            "extra_fields": [],
        }

        # ---------------------------------------------------------------
        # 1. 文件存在性检查
        # ---------------------------------------------------------------
        if agent_path is None or not os.path.exists(agent_path):
            logger.warning(f"Agent矢量文件不存在: {agent_path}")
            return result
        if not os.path.exists(truth_path):
            logger.error(f"Ground Truth矢量文件不存在: {truth_path}")
            return result

        result["file_exists"] = True

        try:
            import geopandas as gpd
            from shapely.validation import explain_validity

            agent_gdf = gpd.read_file(agent_path)
            truth_gdf = gpd.read_file(truth_path)

            if agent_gdf.empty or truth_gdf.empty:
                logger.warning("矢量文件为空")
                return result

            # -----------------------------------------------------------
            # 2. CRS一致性检查
            # -----------------------------------------------------------
            result["crs_agent"] = str(agent_gdf.crs) if agent_gdf.crs else "None"
            result["crs_expected"] = str(truth_gdf.crs) if truth_gdf.crs else "None"

            if agent_gdf.crs is not None and truth_gdf.crs is not None:
                result["crs_match"] = agent_gdf.crs.equals(truth_gdf.crs)
            elif agent_gdf.crs is None and truth_gdf.crs is None:
                result["crs_match"] = True
            else:
                result["crs_match"] = False

            # 如果CRS不匹配，尝试重投影后再比对几何
            if not result["crs_match"] and agent_gdf.crs is not None:
                logger.info("CRS不匹配，将Agent数据重投影至GT坐标系后继续核验")
                agent_gdf = agent_gdf.to_crs(truth_gdf.crs)

            # -----------------------------------------------------------
            # 3. 几何有效性检查
            # -----------------------------------------------------------
            if "geometry" in agent_gdf.columns:
                invalid_mask = ~agent_gdf.geometry.is_valid
                result["invalid_geometry_count"] = int(invalid_mask.sum())
                result["geometry_valid"] = (result["invalid_geometry_count"] == 0)

                if not result["geometry_valid"]:
                    # 记录无效几何原因
                    invalid_reasons = agent_gdf.loc[invalid_mask, "geometry"].apply(
                        lambda g: explain_validity(g) if g is not None else "null geometry"
                    )
                    logger.warning(f"发现 {result['invalid_geometry_count']} 个无效几何: "
                                   f"{invalid_reasons.tolist()[:5]}")

            # -----------------------------------------------------------
            # 4. 要素数量检查
            # -----------------------------------------------------------
            result["feature_count_agent"] = len(agent_gdf)
            result["feature_count_expected"] = len(truth_gdf)
            result["feature_count_match"] = (
                result["feature_count_agent"] == result["feature_count_expected"]
            )

            # -----------------------------------------------------------
            # 5. 面积/长度误差检查（投影坐标系下）
            # -----------------------------------------------------------
            if (result["geometry_valid"] and not agent_gdf.empty and not truth_gdf.empty
                    and agent_gdf.crs is not None):
                try:
                    # 统一到合适投影坐标系计算面积
                    agent_proj = agent_gdf.to_crs(agent_gdf.estimate_utm_crs()) if agent_gdf.crs else agent_gdf
                    truth_proj = truth_gdf.to_crs(agent_gdf.estimate_utm_crs()) if truth_gdf.crs else truth_gdf

                    agent_area = agent_proj.geometry.area.sum()
                    truth_area = truth_proj.geometry.area.sum()

                    if truth_area > 0:
                        result["area_error_pct"] = float(
                            abs(agent_area - truth_area) / truth_area * 100
                        )
                        result["area_within_tolerance"] = (
                            result["area_error_pct"] <= self.area_tolerance_pct
                        )
                    else:
                        result["area_error_pct"] = 0.0 if agent_area == 0 else float("inf")
                        result["area_within_tolerance"] = (agent_area == 0)

                    agent_length = agent_proj.geometry.length.sum()
                    truth_length = truth_proj.geometry.length.sum()

                    if truth_length > 0:
                        result["length_error_pct"] = float(
                            abs(agent_length - truth_length) / truth_length * 100
                        )
                        result["length_within_tolerance"] = (
                            result["length_error_pct"] <= self.length_tolerance_pct
                        )
                    else:
                        result["length_error_pct"] = 0.0 if agent_length == 0 else float("inf")
                        result["length_within_tolerance"] = (agent_length == 0)

                except Exception as e:
                    logger.warning(f"面积/长度计算失败: {e}")

            # -----------------------------------------------------------
            # 6. 属性字段匹配检查
            # -----------------------------------------------------------
            # 排除geometry列
            agent_cols = set(c for c in agent_gdf.columns if c != "geometry")
            truth_cols = set(c for c in truth_gdf.columns if c != "geometry")

            result["missing_fields"] = sorted(list(truth_cols - agent_cols))
            result["extra_fields"] = sorted(list(agent_cols - truth_cols))
            result["attribute_fields_match"] = (
                len(result["missing_fields"]) == 0 and len(result["extra_fields"]) == 0
            )

        except ImportError:
            logger.error("geopandas 未安装，跳过矢量核验")
        except Exception as e:
            logger.error(f"矢量核验异常: {e}", exc_info=True)

        return result


# ===================================================================
# 栅格核验器
# ===================================================================

class RasterVerifier:
    """栅格数据核验器：对比Agent输出栅格与Ground Truth栅格"""

    def __init__(self, extent_tolerance: float = 1e-6, stats_tolerance: float = 0.05):
        """
        Args:
            extent_tolerance: 空间范围容差（坐标单位）
            stats_tolerance: 统计指标相对容差
        """
        self.extent_tolerance = extent_tolerance
        self.stats_tolerance = stats_tolerance

    def verify(self, agent_path: Optional[str], truth_path: str) -> Dict[str, Any]:
        """
        执行栅格核验

        Args:
            agent_path: 智能体输出栅格文件路径 (.tif)
            truth_path: Ground Truth栅格文件路径

        Returns:
            栅格核验结果字典
        """
        result = {
            "file_exists": False,
            "band_count_match": False,
            "band_count_agent": 0,
            "band_count_expected": 0,
            "resolution_match": False,
            "resolution_agent": [0.0, 0.0],
            "resolution_expected": [0.0, 0.0],
            "spatial_extent_match": False,
            "extent_bounds_agent": [0.0, 0.0, 0.0, 0.0],
            "extent_bounds_expected": [0.0, 0.0, 0.0, 0.0],
            "nodata_handling_correct": False,
            "nodata_value_agent": None,
            "nodata_value_expected": None,
            "stats_rmse": None,
            "stats_mae": None,
            "stats_r2": None,
            "stats_within_tolerance": False,
        }

        # ---------------------------------------------------------------
        # 1. 文件存在性
        # ---------------------------------------------------------------
        if agent_path is None or not os.path.exists(agent_path):
            logger.warning(f"Agent栅格文件不存在: {agent_path}")
            return result
        if not os.path.exists(truth_path):
            logger.error(f"Ground Truth栅格文件不存在: {truth_path}")
            return result

        result["file_exists"] = True

        try:
            import rasterio
            from rasterio.warp import aligned_target

            with rasterio.open(agent_path) as agent_src, rasterio.open(truth_path) as truth_src:
                # -------------------------------------------------------
                # 2. 波段数检查
                # -------------------------------------------------------
                result["band_count_agent"] = agent_src.count
                result["band_count_expected"] = truth_src.count
                result["band_count_match"] = (
                    result["band_count_agent"] == result["band_count_expected"]
                )

                # -------------------------------------------------------
                # 3. 分辨率检查
                # -------------------------------------------------------
                result["resolution_agent"] = [float(agent_src.res[0]), float(agent_src.res[1])]
                result["resolution_expected"] = [float(truth_src.res[0]), float(truth_src.res[1])]
                result["resolution_match"] = (
                    abs(agent_src.res[0] - truth_src.res[0]) < 1e-10 and
                    abs(agent_src.res[1] - truth_src.res[1]) < 1e-10
                )

                # -------------------------------------------------------
                # 4. 空间范围检查
                # -------------------------------------------------------
                result["extent_bounds_agent"] = [
                    float(agent_src.bounds.left),
                    float(agent_src.bounds.bottom),
                    float(agent_src.bounds.right),
                    float(agent_src.bounds.top),
                ]
                result["extent_bounds_expected"] = [
                    float(truth_src.bounds.left),
                    float(truth_src.bounds.bottom),
                    float(truth_src.bounds.right),
                    float(truth_src.bounds.top),
                ]
                result["spatial_extent_match"] = all(
                    abs(a - e) < self.extent_tolerance
                    for a, e in zip(result["extent_bounds_agent"],
                                    result["extent_bounds_expected"])
                )

                # -------------------------------------------------------
                # 5. NoData值检查
                # -------------------------------------------------------
                result["nodata_value_agent"] = agent_src.nodata
                result["nodata_value_expected"] = truth_src.nodata

                if agent_src.nodata is None and truth_src.nodata is None:
                    result["nodata_handling_correct"] = True
                elif agent_src.nodata is not None and truth_src.nodata is not None:
                    result["nodata_handling_correct"] = (
                        abs(agent_src.nodata - truth_src.nodata) < 1e-10
                    )
                else:
                    result["nodata_handling_correct"] = False

                # -------------------------------------------------------
                # 6. 统计指标对比
                # -------------------------------------------------------
                try:
                    agent_data = agent_src.read(1).astype(np.float64)
                    truth_data = truth_src.read(1).astype(np.float64)

                    # 处理NoData
                    if agent_src.nodata is not None:
                        agent_data = np.where(agent_data == agent_src.nodata, np.nan, agent_data)
                    if truth_src.nodata is not None:
                        truth_data = np.where(truth_data == truth_src.nodata, np.nan, truth_data)

                    # 如果分辨率不对齐，重采样至一致
                    if not result["resolution_match"] or not result["spatial_extent_match"]:
                        logger.info("栅格不对齐，尝试重采样后统计对比")
                        # 取两者公共区域 & 统一分辨率
                        # 这里使用简化策略：如果尺寸不同，取最小交集对比
                        min_rows = min(agent_data.shape[0], truth_data.shape[0])
                        min_cols = min(agent_data.shape[1], truth_data.shape[1])
                        agent_crop = agent_data[:min_rows, :min_cols]
                        truth_crop = truth_data[:min_rows, :min_cols]
                    else:
                        agent_crop = agent_data
                        truth_crop = truth_data

                    # 只对两个都有效的像素计算
                    valid_mask = ~np.isnan(agent_crop) & ~np.isnan(truth_crop)
                    if valid_mask.sum() > 0:
                        a_valid = agent_crop[valid_mask]
                        t_valid = truth_crop[valid_mask]

                        result["stats_rmse"] = float(np.sqrt(np.mean((a_valid - t_valid) ** 2)))
                        result["stats_mae"] = float(np.mean(np.abs(a_valid - t_valid)))

                        # R²
                        ss_res = np.sum((t_valid - a_valid) ** 2)
                        ss_tot = np.sum((t_valid - np.mean(t_valid)) ** 2)
                        if ss_tot > 0:
                            result["stats_r2"] = float(1 - ss_res / ss_tot)
                        else:
                            result["stats_r2"] = 1.0 if ss_res == 0 else 0.0

                        # 判断是否在容差内
                        t_range = np.nanmax(truth_crop) - np.nanmin(truth_crop)
                        if t_range > 0:
                            result["stats_within_tolerance"] = (
                                result["stats_rmse"] / abs(t_range) <= self.stats_tolerance
                            )
                        else:
                            result["stats_within_tolerance"] = (result["stats_rmse"] < 1e-10)
                    else:
                        result["stats_rmse"] = None
                        result["stats_mae"] = None
                        result["stats_r2"] = None
                        result["stats_within_tolerance"] = False

                except Exception as e:
                    logger.warning(f"栅格统计对比失败: {e}")

        except ImportError:
            logger.error("rasterio 未安装，跳过栅格核验")
        except Exception as e:
            logger.error(f"栅格核验异常: {e}", exc_info=True)

        return result


# ===================================================================
# 属性统计表核验器
# ===================================================================

class TableVerifier:
    """属性统计表核验器：对比Agent输出CSV与Ground Truth CSV"""

    def __init__(self, numeric_tolerance_pct: float = 1.0):
        """
        Args:
            numeric_tolerance_pct: 数值相对误差容差百分比
        """
        self.numeric_tolerance_pct = numeric_tolerance_pct

    def verify(self, agent_path: Optional[str], truth_path: str) -> Dict[str, Any]:
        """
        执行属性统计表核验

        Args:
            agent_path: 智能体输出CSV文件路径
            truth_path: Ground Truth CSV文件路径

        Returns:
            表格核验结果字典
        """
        result = {
            "file_exists": False,
            "column_names_match": False,
            "missing_columns": [],
            "extra_columns": [],
            "row_count_match": False,
            "row_count_agent": 0,
            "row_count_expected": 0,
            "grouped_stats_match": False,
            "numeric_diffs": [],
        }

        if agent_path is None or not os.path.exists(agent_path):
            logger.warning(f"Agent统计表文件不存在: {agent_path}")
            return result
        if not os.path.exists(truth_path):
            logger.error(f"Ground Truth统计表文件不存在: {truth_path}")
            return result

        result["file_exists"] = True

        try:
            import pandas as pd

            agent_df = pd.read_csv(agent_path)
            truth_df = pd.read_csv(truth_path)

            # 列名比对
            result["missing_columns"] = sorted(list(set(truth_df.columns) - set(agent_df.columns)))
            result["extra_columns"] = sorted(list(set(agent_df.columns) - set(truth_df.columns)))
            result["column_names_match"] = (
                len(result["missing_columns"]) == 0 and
                len(result["extra_columns"]) == 0
            )

            # 行数比对
            result["row_count_agent"] = len(agent_df)
            result["row_count_expected"] = len(truth_df)
            result["row_count_match"] = (
                result["row_count_agent"] == result["row_count_expected"]
            )

            # 数值列逐项比对
            common_cols = set(truth_df.columns) & set(agent_df.columns)
            numeric_diffs = []

            for col in sorted(common_cols):
                if col in truth_df.columns and col in agent_df.columns:
                    try:
                        t_vals = pd.to_numeric(truth_df[col], errors="coerce")
                        a_vals = pd.to_numeric(agent_df[col], errors="coerce")

                        # 逐行比对
                        for i in range(min(len(t_vals), len(a_vals))):
                            tv, av = t_vals.iloc[i], a_vals.iloc[i]
                            if pd.notna(tv) and pd.notna(av):
                                if abs(tv) > 1e-10:
                                    diff_pct = float(abs(av - tv) / abs(tv) * 100)
                                else:
                                    diff_pct = float(abs(av - tv) * 100)
                                if diff_pct > self.numeric_tolerance_pct:
                                    numeric_diffs.append({
                                        "column": col,
                                        "row": i,
                                        "agent_value": float(av),
                                        "expected_value": float(tv),
                                        "diff_pct": round(diff_pct, 4),
                                    })
                            elif pd.isna(tv) != pd.isna(av):
                                numeric_diffs.append({
                                    "column": col,
                                    "row": i,
                                    "agent_value": str(av),
                                    "expected_value": str(tv),
                                    "diff_pct": None,
                                })
                    except Exception:
                        pass

            result["numeric_diffs"] = numeric_diffs
            result["grouped_stats_match"] = (len(numeric_diffs) == 0)

        except ImportError:
            logger.error("pandas 未安装，跳过表格核验")
        except Exception as e:
            logger.error(f"表格核验异常: {e}", exc_info=True)

        return result


# ===================================================================
# 可视化核验器
# ===================================================================

class VisualVerifier:
    """
    可视化隐形错误核验器
    
    检测以下可视化异常：
    - 空白输出（纯色图片）
    - 图层空间错位
    - 制图元素缺失（图例、比例尺、指北针、标题）
    - 符号分级异常
    
    注意：本模块提供自动化初步筛查，最终仍需人工视觉审查确认。
    """

    def verify(self, agent_path: Optional[str], truth_path: str,
               vector_result: Optional[Dict] = None,
               raster_result: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行可视化核验

        Args:
            agent_path: 智能体输出PNG地图文件路径
            truth_path: Ground Truth PNG地图文件路径
            vector_result: 矢量核验结果（用于交叉判断）
            raster_result: 栅格核验结果（用于交叉判断）

        Returns:
            可视化核验结果字典
        """
        result = {
            "file_exists": False,
            "is_blank": False,
            "layer_misalignment": False,
            "legend_missing": False,
            "scale_bar_missing": False,
            "title_missing": False,
            "symbolization_anomaly": False,
            "north_arrow_missing": False,
            "requires_visual_check": False,
            "anomaly_symptoms": [],
        }

        # ---------------------------------------------------------------
        # 1. 文件存在性
        # ---------------------------------------------------------------
        if agent_path is None or not os.path.exists(agent_path):
            logger.warning(f"Agent地图文件不存在: {agent_path}")
            result["requires_visual_check"] = True
            result["anomaly_symptoms"].append("地图输出文件缺失")
            return result

        result["file_exists"] = True

        symptoms: List[str] = []

        try:
            from PIL import Image
            import numpy as np

            agent_img = Image.open(agent_path).convert("RGB")
            agent_arr = np.array(agent_img)

            # -----------------------------------------------------------
            # 2. 空白输出检测
            # -----------------------------------------------------------
            # 检查是否几乎为单一颜色（标准差极小）
            std_per_channel = agent_arr.std(axis=(0, 1))
            if all(s < 5.0 for s in std_per_channel):
                result["is_blank"] = True
                symptoms.append("输出地图为空白/纯色")

            # 检查是否全白或全黑
            mean_per_channel = agent_arr.mean(axis=(0, 1))
            if all(abs(m - 255) < 1 for m in mean_per_channel):
                result["is_blank"] = True
                symptoms.append("输出地图为纯白")
            elif all(abs(m) < 1 for m in mean_per_channel):
                result["is_blank"] = True
                symptoms.append("输出地图为纯黑")

            # -----------------------------------------------------------
            # 3. 与Ground Truth图像的结构相似性快速筛查
            # -----------------------------------------------------------
            if os.path.exists(truth_path):
                try:
                    truth_img = Image.open(truth_path).convert("RGB")
                    truth_arr = np.array(truth_img)

                    # 尺寸一致性检查
                    if agent_arr.shape != truth_arr.shape:
                        symptoms.append(f"输出尺寸({agent_arr.shape})与GT({truth_arr.shape})不一致")
                        result["layer_misalignment"] = True

                    # 像素级差异率
                    if agent_arr.shape == truth_arr.shape:
                        diff_ratio = np.mean(agent_arr != truth_arr)
                        if diff_ratio > 0.90:
                            symptoms.append(f"像素差异率极高({diff_ratio:.2%})，图层可能错位")
                            result["layer_misalignment"] = True

                    # 颜色分布对比
                    agent_hist = np.histogram(agent_arr, bins=50, range=(0, 255))[0]
                    truth_hist = np.histogram(truth_arr, bins=50, range=(0, 255))[0]
                    hist_corr = np.corrcoef(agent_hist, truth_hist)[0, 1]
                    if hist_corr < 0.3:
                        symptoms.append(f"颜色分布与GT差异大(相关={hist_corr:.2f})")
                        result["symbolization_anomaly"] = True

                except Exception as e:
                    logger.warning(f"GT图像对比失败: {e}")

            # -----------------------------------------------------------
            # 4. 交叉判断：基于矢量/栅格结果推断可视化问题
            # -----------------------------------------------------------
            if vector_result:
                if not vector_result.get("crs_match", True):
                    symptoms.append("矢量CRS不匹配可能导致图层错位")
                    result["layer_misalignment"] = True
                if not vector_result.get("geometry_valid", True):
                    symptoms.append("无效几何可能导致渲染异常")

            if raster_result:
                if not raster_result.get("spatial_extent_match", True):
                    symptoms.append("栅格范围不一致可能导致图层错位")
                    result["layer_misalignment"] = True

            # -----------------------------------------------------------
            # 5. 制图元素检测（基于图像特征启发式判断）
            # -----------------------------------------------------------
            # 这些检查是启发式的，精度有限，标记为需人工审查
            # 检查图像底部是否有比例尺区域（通常底部条带）
            bottom_strip = agent_arr[-20:, :, :]
            bottom_std = bottom_strip.std()
            if bottom_std < 10:
                result["scale_bar_missing"] = True
                symptoms.append("可能缺少比例尺（底部区域均匀）")

            # 检查右侧是否有图例区域
            right_strip = agent_arr[:, -30:, :]
            right_std = right_strip.std()
            if right_std < 10:
                result["legend_missing"] = True
                symptoms.append("可能缺少图例（右侧区域均匀）")

            # 检查顶部是否有标题区域
            top_strip = agent_arr[:20, :, :]
            top_std = top_strip.std()
            if top_std < 10:
                result["title_missing"] = True
                symptoms.append("可能缺少标题（顶部区域均匀）")

        except ImportError:
            logger.warning("PIL/Pillow 未安装，使用基础可视化核验")
            symptoms.append("PIL未安装，仅执行基础核验")
        except Exception as e:
            logger.error(f"可视化核验异常: {e}", exc_info=True)
            symptoms.append(f"可视化核验异常: {str(e)}")

        # ---------------------------------------------------------------
        # 6. 汇总：是否需要人工视觉审查
        # ---------------------------------------------------------------
        result["anomaly_symptoms"] = symptoms
        result["requires_visual_check"] = (
            result["is_blank"] or
            result["layer_misalignment"] or
            result["symbolization_anomaly"] or
            result["legend_missing"] or
            result["scale_bar_missing"] or
            result["title_missing"] or
            result["north_arrow_missing"] or
            len(symptoms) > 0
        )

        return result


# ===================================================================
# GIS Evaluator 主类
# ===================================================================

class GisEvaluator:
    """
    GIS自动化核验主程序

    用法:
        evaluator = GisEvaluator()
        report = evaluator.evaluate(
            agent_output_dir="path/to/agent/output",
            truth_dir="path/to/ground_truth",
            task_config={...}
        )
    """

    def __init__(self,
                 area_tolerance_pct: float = 5.0,
                 length_tolerance_pct: float = 5.0,
                 extent_tolerance: float = 1e-6,
                 stats_tolerance: float = 0.05,
                 numeric_tolerance_pct: float = 1.0):
        """
        Args:
            area_tolerance_pct: 矢量面积容差百分比
            length_tolerance_pct: 矢量长度容差百分比
            extent_tolerance: 栅格范围容差
            stats_tolerance: 栅格统计容差
            numeric_tolerance_pct: 表格数值容差百分比
        """
        self.vector_verifier = VectorVerifier(area_tolerance_pct, length_tolerance_pct)
        self.raster_verifier = RasterVerifier(extent_tolerance, stats_tolerance)
        self.table_verifier = TableVerifier(numeric_tolerance_pct)
        self.visual_verifier = VisualVerifier()
        self.error_classifier = ErrorClassifier()

    def evaluate(self,
                 agent_output_dir: str,
                 truth_dir: str,
                 task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整四层核验

        Args:
            agent_output_dir: 智能体输出目录路径
            truth_dir: 对应任务的Ground Truth目录路径
            task_config: 任务配置，包含:
                - case_id: 任务编号
                - output_types: 期望输出类型列表 ["vector", "raster", "table", "map"]
                - thresholds (可选): 自定义阈值覆盖
                - expected_files (可选): 期望输出文件名映射

        Returns:
            标准化评估报告 dict
        """
        case_id = task_config.get("case_id", "unknown")
        output_types = task_config.get("output_types", ["vector", "raster", "table", "map"])

        # 允许任务级别覆盖阈值
        thresholds = task_config.get("thresholds", {})
        if thresholds:
            self.vector_verifier.area_tolerance_pct = thresholds.get(
                "area_tolerance_pct", self.vector_verifier.area_tolerance_pct)
            self.vector_verifier.length_tolerance_pct = thresholds.get(
                "length_tolerance_pct", self.vector_verifier.length_tolerance_pct)

        # ---------------------------------------------------------------
        # 文件路径解析
        # ---------------------------------------------------------------
        expected_files = task_config.get("expected_files", {})
        agent_vector = self._resolve_path(agent_output_dir, expected_files.get("vector"))
        truth_vector = self._resolve_path(truth_dir, "expected_vector.geojson")
        agent_raster = self._resolve_path(agent_output_dir, expected_files.get("raster"))
        truth_raster = self._resolve_path(truth_dir, "expected_raster.tif")
        agent_table = self._resolve_path(agent_output_dir, expected_files.get("table"))
        truth_table = self._resolve_path(truth_dir, "stats.csv")
        agent_map = self._resolve_path(agent_output_dir, expected_files.get("map"))
        truth_map = self._resolve_path(truth_dir, "map.png")

        # ---------------------------------------------------------------
        # 四层核验
        # ---------------------------------------------------------------
        vector_result = {}
        raster_result = {}
        table_result = {}
        visual_result = {}

        if "vector" in output_types:
            vector_result = self.vector_verifier.verify(agent_vector, truth_vector)

        if "raster" in output_types:
            raster_result = self.raster_verifier.verify(agent_raster, truth_raster)

        if "table" in output_types:
            table_result = self.table_verifier.verify(agent_table, truth_table)

        if "map" in output_types:
            visual_result = self.visual_verifier.verify(
                agent_map, truth_map, vector_result, raster_result
            )

        # ---------------------------------------------------------------
        # 错误分类
        # ---------------------------------------------------------------
        errors: List[ErrorLabel] = self.error_classifier.classify_all(
            vector_result, raster_result, table_result, visual_result
        )
        error_dicts = [e.to_dict() for e in errors]

        # ---------------------------------------------------------------
        # 综合判定
        # ---------------------------------------------------------------
        requires_visual = visual_result.get("requires_visual_check", False)
        overall = self._determine_overall(vector_result, raster_result,
                                          table_result, visual_result)

        # 统计检查通过/失败数
        total_checks, passed_checks = self._count_checks(
            vector_result, raster_result, table_result, visual_result)
        failed_checks = total_checks - passed_checks

        # ---------------------------------------------------------------
        # 构建报告
        # ---------------------------------------------------------------
        report = {
            "report_id": f"eval_{case_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_result": overall,
            "vector_verification": vector_result,
            "raster_verification": raster_result,
            "table_verification": table_result,
            "visual_verification": visual_result,
            "errors": error_dicts,
            "requires_visual_check": requires_visual,
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "error_categories": self.error_classifier.get_error_categories(errors),
                "failure_reasons": self.error_classifier.get_failure_reasons(errors),
                "metric_deltas": self._extract_metric_deltas(
                    vector_result, raster_result, table_result),
            }
        }

        return report

    @staticmethod
    def _resolve_path(base_dir: str, filename: Optional[str]) -> Optional[str]:
        """解析文件路径"""
        if filename is None:
            return None
        path = os.path.join(base_dir, filename)
        return path if os.path.exists(path) else None

    @staticmethod
    def _determine_overall(vector: Dict, raster: Dict,
                           table: Dict, visual: Dict) -> str:
        """综合判定 PASS / FAIL / PARTIAL / SKIP"""
        all_results = [vector, raster, table, visual]

        # 全部空结果 = SKIP
        if all(not r for r in all_results):
            return "SKIP"

        checks = []

        # 矢量
        if vector:
            checks.append(vector.get("file_exists", False))
            if vector.get("file_exists"):
                checks.extend([
                    vector.get("crs_match", True),
                    vector.get("geometry_valid", True),
                    vector.get("feature_count_match", True),
                    vector.get("area_within_tolerance", True),
                    vector.get("length_within_tolerance", True),
                    vector.get("attribute_fields_match", True),
                ])

        # 栅格
        if raster:
            checks.append(raster.get("file_exists", False))
            if raster.get("file_exists"):
                checks.extend([
                    raster.get("band_count_match", True),
                    raster.get("resolution_match", True),
                    raster.get("spatial_extent_match", True),
                    raster.get("nodata_handling_correct", True),
                    raster.get("stats_within_tolerance", True),
                ])

        # 表格
        if table:
            checks.append(table.get("file_exists", False))
            if table.get("file_exists"):
                checks.extend([
                    table.get("column_names_match", True),
                    table.get("row_count_match", True),
                    table.get("grouped_stats_match", True),
                ])

        # 可视化
        if visual:
            checks.append(visual.get("file_exists", False))
            if visual.get("file_exists"):
                checks.extend([
                    not visual.get("is_blank", True),
                    not visual.get("layer_misalignment", True),
                ])

        if not checks:
            return "SKIP"

        if all(checks):
            return "PASS"
        elif any(checks):
            return "PARTIAL" if sum(checks) / len(checks) >= 0.5 else "FAIL"
        else:
            return "FAIL"

    @staticmethod
    def _count_checks(vector: Dict, raster: Dict,
                      table: Dict, visual: Dict) -> Tuple[int, int]:
        """统计总检查项和通过数"""
        all_checks = []

        bool_keys = ["file_exists", "crs_match", "geometry_valid",
                     "feature_count_match", "area_within_tolerance",
                     "length_within_tolerance", "attribute_fields_match",
                     "band_count_match", "resolution_match", "spatial_extent_match",
                     "nodata_handling_correct", "stats_within_tolerance",
                     "column_names_match", "row_count_match", "grouped_stats_match"]

        for result in [vector, raster, table, visual]:
            if result:
                for k in bool_keys:
                    if k in result:
                        all_checks.append(bool(result[k]))

        # 可视化特殊项
        if visual:
            if "is_blank" in visual:
                all_checks.append(not visual["is_blank"])
            if "layer_misalignment" in visual:
                all_checks.append(not visual["layer_misalignment"])

        total = len(all_checks)
        passed = sum(1 for c in all_checks if c)
        return total, passed

    @staticmethod
    def _extract_metric_deltas(vector: Dict, raster: Dict,
                               table: Dict) -> Dict[str, Any]:
        """提取关键指标偏差值"""
        deltas = {}

        if vector:
            if vector.get("area_error_pct") is not None:
                deltas["area_error_pct"] = vector["area_error_pct"]
            if vector.get("length_error_pct") is not None:
                deltas["length_error_pct"] = vector["length_error_pct"]
            if vector.get("feature_count_agent") is not None:
                deltas["feature_count_delta"] = (
                    vector.get("feature_count_agent", 0) -
                    vector.get("feature_count_expected", 0)
                )

        if raster:
            if raster.get("stats_rmse") is not None:
                deltas["raster_rmse"] = raster["stats_rmse"]
            if raster.get("stats_mae") is not None:
                deltas["raster_mae"] = raster["stats_mae"]

        if table:
            if table.get("numeric_diffs"):
                deltas["table_diff_count"] = len(table["numeric_diffs"])

        return deltas


# ---------------------------------------------------------------------------
# 便捷函数：与 batch_evaluate 集成
# ---------------------------------------------------------------------------

def evaluate(agent_output_dir: str,
             truth_dir: str,
             task_config: Dict[str, Any],
             **kwargs) -> Dict[str, Any]:
    """
    主入口便捷函数
    """
    evaluator = GisEvaluator(**kwargs)
    return evaluator.evaluate(agent_output_dir, truth_dir, task_config)


# ---------------------------------------------------------------------------
# 模块自检
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("GIS Evaluator — 模块自检")
    print("=" * 60)

    # 创建临时测试数据
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="gis_eval_test_")
    print(f"临时目录: {tmpdir}")

    try:
        # 测试评估器初始化
        evaluator = GisEvaluator()
        print("✓ GisEvaluator 初始化成功")

        # 测试无文件场景
        report = evaluator.evaluate(
            agent_output_dir=tmpdir,
            truth_dir=tmpdir,
            task_config={
                "case_id": "test_001",
                "output_types": ["vector", "raster", "table", "map"],
            }
        )
        print(f"  综合结果: {report['overall_result']}")
        print(f"  错误数: {len(report['errors'])}")
        print(f"  需人工审查: {report['requires_visual_check']}")
        print("✓ 空目录核验完成（预期SKIP）")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("=" * 60)
    print("模块自检完成")
