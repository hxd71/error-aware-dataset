"""
GIS Error Classifier — 错误分类器模块
========================================
将核验失败结果映射为 A–E 五大类 15 个子类 GIS 错误标签。

错误分类体系:
  A. 空间参考系错误 (Spatial Reference Errors)
     A1 — CRS不匹配 (CRS Mismatch)
     A2 — 投影转换错误 (Projection Transform Error)
     A3 — 坐标越界 (Coordinate Out-of-Bounds)

  B. 几何完整性错误 (Geometry Integrity Errors)
     B1 — 无效几何/自相交 (Invalid Geometry / Self-intersection)
     B2 — 拓扑错误 (Topology Error)
     B3 — 几何类型不匹配 (Geometry Type Mismatch)

  C. 属性/表格错误 (Attribute / Tabular Errors)
     C1 — 字段缺失/不匹配 (Field Missing / Mismatch)
     C2 — 属性值错误 (Attribute Value Error)
     C3 — 统计量偏差 (Statistical Deviation)

  D. 栅格数据错误 (Raster Data Errors)
     D1 — 波段/分辨率不匹配 (Band / Resolution Mismatch)
     D2 — NoData异常 (NoData Anomaly)
     D3 — 栅格范围偏差 (Raster Extent Deviation)

  E. 可视化/逻辑错误 (Visualization / Logic Errors)
     E1 — 图层错位/空白输出 (Layer Misalignment / Blank Output)
     E2 — 制图元素缺失 (Cartographic Element Missing)
     E3 — 隐形逻辑错误 (Invisible Logic Error)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


# ---------------------------------------------------------------------------
# 错误分类枚举
# ---------------------------------------------------------------------------

class ErrorCategory(Enum):
    """五大错误类别"""
    A = ("A", "空间参考系错误 (Spatial Reference)")
    B = ("B", "几何完整性错误 (Geometry Integrity)")
    C = ("C", "属性/表格错误 (Attribute / Tabular)")
    D = ("D", "栅格数据错误 (Raster Data)")
    E = ("E", "可视化/逻辑错误 (Visualization / Logic)")

    def __init__(self, code: str, label_cn: str):
        self.code = code
        self.label_cn = label_cn


class ErrorSubCategory(Enum):
    """15个子类错误标签"""
    A1 = ("A1", "A", "CRS不匹配", "CRS Mismatch",
          "输出数据坐标系与Ground Truth不一致")
    A2 = ("A2", "A", "投影转换错误", "Projection Transform Error",
          "投影转换过程中产生偏差或使用了错误的投影参数")
    A3 = ("A3", "A", "坐标越界", "Coordinate Out-of-Bounds",
          "几何坐标超出有效范围或目标区域边界")

    B1 = ("B1", "B", "无效几何/自相交", "Invalid Geometry / Self-intersection",
          "输出几何包含自相交环、重复节点或其他无效结构")
    B2 = ("B2", "B", "拓扑错误", "Topology Error",
          "面之间有意外重叠/空隙、线未正确连接等拓扑关系错误")
    B3 = ("B3", "B", "几何类型不匹配", "Geometry Type Mismatch",
          "输出几何类型与期望类型不一致（如期望Polygon输出LineString）")

    C1 = ("C1", "C", "字段缺失/不匹配", "Field Missing / Mismatch",
          "输出属性表缺失必要字段或包含多余字段")
    C2 = ("C2", "C", "属性值错误", "Attribute Value Error",
          "属性字段值计算错误或类型不匹配")
    C3 = ("C3", "C", "统计量偏差", "Statistical Deviation",
          "分组统计或聚合数值超出允许误差范围")

    D1 = ("D1", "D", "波段/分辨率不匹配", "Band / Resolution Mismatch",
          "栅格波段数、像元分辨率与Ground Truth不一致")
    D2 = ("D2", "D", "NoData异常", "NoData Anomaly",
          "NoData值定义错误或NoData区域处理不当")
    D3 = ("D3", "D", "栅格范围偏差", "Raster Extent Deviation",
          "栅格空间范围、原点偏移超出允许阈值")

    E1 = ("E1", "E", "图层错位/空白输出", "Layer Misalignment / Blank Output",
          "输出图层空间位置偏移或渲染结果为空")
    E2 = ("E2", "E", "制图元素缺失", "Cartographic Element Missing",
          "地图输出缺少图例、比例尺、指北针、标题等必要制图元素")
    E3 = ("E3", "E", "隐形逻辑错误", "Invisible Logic Error",
          "输出表面正常但存在深层逻辑缺陷，需人工视觉审查确认")

    def __init__(self, code: str, category: str, name_cn: str, name_en: str, description: str):
        self.code = code
        self.category = category
        self.name_cn = name_cn
        self.name_en = name_en
        self.description = description


# ---------------------------------------------------------------------------
# 错误标签数据类
# ---------------------------------------------------------------------------

@dataclass
class ErrorLabel:
    """
    单个GIS错误标签
    
    Attributes:
        category: 错误大类 (A-E)
        subcategory: 错误子类 (A1-E3)
        label_name: 人类可读错误名
        description: 详细描述
        details: 补充上下文信息（触发条件、建议修复方向）
    """
    category: str
    subcategory: str
    label_name: str
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "label_name": self.label_name,
            "description": self.description,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# 错误分类器核心类
# ---------------------------------------------------------------------------

class ErrorClassifier:
    """
    GIS错误分类器
    
    根据矢量/栅格/表格/可视化四层核验结果，
    自动将失败项映射为对应的GIS错误标签。
    """

    # ------------------------------------------------------------------
    # 分类规则映射表： (触发条件函数, 对应ErrorSubCategory)
    # ------------------------------------------------------------------

    @staticmethod
    def classify_vector_errors(vector_result: Dict[str, Any]) -> List[ErrorLabel]:
        """
        根据矢量核验结果生成错误标签列表
        
        Args:
            vector_result: 矢量核验结果字典，包含各检查项布尔值与偏差值
            
        Returns:
            错误标签列表
        """
        errors: List[ErrorLabel] = []

        if not vector_result:
            return errors

        # A1: CRS不匹配
        if not vector_result.get("crs_match", True) and vector_result.get("file_exists", False):
            esc = ErrorSubCategory.A1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "agent_crs": vector_result.get("crs_agent", "unknown"),
                    "expected_crs": vector_result.get("crs_expected", "unknown"),
                }
            ))

        # A3: 坐标越界 (通过面积异常大来间接判断)
        area_err = vector_result.get("area_error_pct", 0) or 0
        if abs(area_err) > 100.0:  # 面积偏差超过100%可能坐标越界
            esc = ErrorSubCategory.A3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={"area_error_pct": area_err}
            ))

        # B1: 无效几何
        if not vector_result.get("geometry_valid", True):
            esc = ErrorSubCategory.B1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "invalid_count": vector_result.get("invalid_geometry_count", 0)
                }
            ))

        # B3: 几何类型不匹配 (通过要素数量差异和面积差异联合判断)
        if (not vector_result.get("feature_count_match", True) and
                not vector_result.get("geometry_valid", True)):
            esc = ErrorSubCategory.B3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "agent_count": vector_result.get("feature_count_agent"),
                    "expected_count": vector_result.get("feature_count_expected"),
                }
            ))

        # B2: 拓扑错误 (面积/长度偏差过大但几何有效)
        if vector_result.get("geometry_valid", True):
            if not vector_result.get("area_within_tolerance", True):
                esc = ErrorSubCategory.B2
                errors.append(ErrorLabel(
                    category=esc.category,
                    subcategory=esc.code,
                    label_name=esc.name_cn,
                    description="面积偏差超出容差范围，可能存在拓扑重叠或空隙",
                    details={"area_error_pct": area_err}
                ))
            if not vector_result.get("length_within_tolerance", True):
                esc = ErrorSubCategory.B2
                # 避免重复添加
                if not any(e.subcategory == "B2" for e in errors):
                    errors.append(ErrorLabel(
                        category=esc.category,
                        subcategory=esc.code,
                        label_name=esc.name_cn,
                        description="长度偏差超出容差范围，可能存在拓扑断裂",
                        details={"length_error_pct": vector_result.get("length_error_pct", 0)}
                    ))

        # C1: 字段缺失/不匹配
        if not vector_result.get("attribute_fields_match", True):
            esc = ErrorSubCategory.C1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "missing_fields": vector_result.get("missing_fields", []),
                    "extra_fields": vector_result.get("extra_fields", []),
                }
            ))

        # 文件不存在
        if not vector_result.get("file_exists", True):
            esc = ErrorSubCategory.E1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description="矢量输出文件不存在",
                details={}
            ))

        return errors

    @staticmethod
    def classify_raster_errors(raster_result: Dict[str, Any]) -> List[ErrorLabel]:
        """
        根据栅格核验结果生成错误标签列表
        """
        errors: List[ErrorLabel] = []

        if not raster_result:
            return errors

        # D1: 波段/分辨率不匹配
        if (not raster_result.get("band_count_match", True) or
                not raster_result.get("resolution_match", True)):
            esc = ErrorSubCategory.D1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "band_count_agent": raster_result.get("band_count_agent"),
                    "band_count_expected": raster_result.get("band_count_expected"),
                    "resolution_agent": raster_result.get("resolution_agent"),
                    "resolution_expected": raster_result.get("resolution_expected"),
                }
            ))

        # D2: NoData异常
        if not raster_result.get("nodata_handling_correct", True):
            esc = ErrorSubCategory.D2
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "nodata_agent": raster_result.get("nodata_value_agent"),
                    "nodata_expected": raster_result.get("nodata_value_expected"),
                }
            ))

        # D3: 栅格范围偏差
        if not raster_result.get("spatial_extent_match", True):
            esc = ErrorSubCategory.D3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "extent_agent": raster_result.get("extent_bounds_agent"),
                    "extent_expected": raster_result.get("extent_bounds_expected"),
                }
            ))

        # 统计指标偏差
        if not raster_result.get("stats_within_tolerance", True):
            esc = ErrorSubCategory.C3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=f"栅格统计指标偏差: RMSE={raster_result.get('stats_rmse', 'N/A')}",
                details={
                    "rmse": raster_result.get("stats_rmse"),
                    "mae": raster_result.get("stats_mae"),
                    "r2": raster_result.get("stats_r2"),
                }
            ))

        # 文件不存在
        if not raster_result.get("file_exists", True):
            esc = ErrorSubCategory.E1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description="栅格输出文件不存在",
                details={}
            ))

        return errors

    @staticmethod
    def classify_table_errors(table_result: Dict[str, Any]) -> List[ErrorLabel]:
        """
        根据属性统计表核验结果生成错误标签列表
        """
        errors: List[ErrorLabel] = []

        if not table_result:
            return errors

        # C1: 字段缺失/不匹配
        if not table_result.get("column_names_match", True):
            esc = ErrorSubCategory.C1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "missing_columns": table_result.get("missing_columns", []),
                    "extra_columns": table_result.get("extra_columns", []),
                }
            ))

        # C2: 属性值错误
        if table_result.get("numeric_diffs") and len(table_result.get("numeric_diffs", [])) > 0:
            esc = ErrorSubCategory.C2
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={"diffs": table_result.get("numeric_diffs", [])}
            ))

        # C3: 统计量偏差
        if (not table_result.get("grouped_stats_match", True) or
                not table_result.get("row_count_match", True)):
            esc = ErrorSubCategory.C3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "row_count_agent": table_result.get("row_count_agent"),
                    "row_count_expected": table_result.get("row_count_expected"),
                }
            ))

        if not table_result.get("file_exists", True):
            esc = ErrorSubCategory.E1
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description="统计表输出文件不存在",
                details={}
            ))

        return errors

    @staticmethod
    def classify_visual_errors(visual_result: Dict[str, Any]) -> List[ErrorLabel]:
        """
        根据可视化核验结果生成错误标签列表
        """
        errors: List[ErrorLabel] = []

        if not visual_result:
            return errors

        # E1: 图层错位/空白输出
        if (visual_result.get("is_blank", False) or
                visual_result.get("layer_misalignment", False)):
            esc = ErrorSubCategory.E1
            symptoms = []
            if visual_result.get("is_blank"):
                symptoms.append("空白输出")
            if visual_result.get("layer_misalignment"):
                symptoms.append("图层空间错位")
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={"symptoms": symptoms}
            ))

        # E2: 制图元素缺失
        cartographic_issues = []
        if visual_result.get("legend_missing", False):
            cartographic_issues.append("图例缺失")
        if visual_result.get("scale_bar_missing", False):
            cartographic_issues.append("比例尺缺失")
        if visual_result.get("title_missing", False):
            cartographic_issues.append("标题缺失")
        if visual_result.get("north_arrow_missing", False):
            cartographic_issues.append("指北针缺失")
        if visual_result.get("symbolization_anomaly", False):
            cartographic_issues.append("符号分级异常")

        if cartographic_issues:
            esc = ErrorSubCategory.E2
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={"missing_elements": cartographic_issues}
            ))

        # E3: 隐形逻辑错误 (需人工审查)
        if visual_result.get("requires_visual_check", False):
            esc = ErrorSubCategory.E3
            errors.append(ErrorLabel(
                category=esc.category,
                subcategory=esc.code,
                label_name=esc.name_cn,
                description=esc.description,
                details={
                    "anomaly_symptoms": visual_result.get("anomaly_symptoms", []),
                }
            ))

        return errors

    # ------------------------------------------------------------------
    # 综合分类
    # ------------------------------------------------------------------

    @classmethod
    def classify_all(cls,
                     vector_result: Dict[str, Any],
                     raster_result: Dict[str, Any],
                     table_result: Dict[str, Any],
                     visual_result: Dict[str, Any]) -> List[ErrorLabel]:
        """
        综合四层核验结果，返回完整的错误标签列表
        
        Args:
            vector_result: 矢量核验结果
            raster_result: 栅格核验结果
            table_result: 表格核验结果
            visual_result: 可视化核验结果
            
        Returns:
            去重后的错误标签列表
        """
        all_errors: List[ErrorLabel] = []
        all_errors.extend(cls.classify_vector_errors(vector_result))
        all_errors.extend(cls.classify_raster_errors(raster_result))
        all_errors.extend(cls.classify_table_errors(table_result))
        all_errors.extend(cls.classify_visual_errors(visual_result))

        # 去重：相同 subcategory 只保留第一个（保留最详细的）
        seen = set()
        deduped: List[ErrorLabel] = []
        for e in all_errors:
            if e.subcategory not in seen:
                seen.add(e.subcategory)
                deduped.append(e)
        return deduped

    @staticmethod
    def get_error_categories(errors: List[ErrorLabel]) -> List[str]:
        """提取涉及的大类列表"""
        return sorted(set(e.category for e in errors))

    @staticmethod
    def get_failure_reasons(errors: List[ErrorLabel]) -> List[str]:
        """提取失败原因摘要"""
        return [f"[{e.subcategory}] {e.label_name}: {e.description}" for e in errors]


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

_ERROR_CATEGORY_MAP: Dict[str, ErrorSubCategory] = {
    e.code: e for e in ErrorSubCategory
}


def get_error_info(code: str) -> Optional[ErrorSubCategory]:
    """根据错误代码获取错误信息"""
    return _ERROR_CATEGORY_MAP.get(code)


def list_all_errors() -> List[Dict[str, str]]:
    """列出全部15个错误子类"""
    return [
        {
            "code": e.code,
            "category": e.category,
            "name_cn": e.name_cn,
            "name_en": e.name_en,
            "description": e.description,
        }
        for e in ErrorSubCategory
    ]


# ---------------------------------------------------------------------------
# 模块自检
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("GIS Error Classifier — 错误分类体系")
    print("=" * 60)
    for err in list_all_errors():
        print(f"  [{err['code']}] {err['name_cn']} ({err['name_en']})")
        print(f"        {err['description']}")
    print()

    # 模拟分类测试
    print("--- 模拟分类测试 ---")
    classifier = ErrorClassifier()

    mock_vector = {
        "file_exists": True,
        "crs_match": False,
        "crs_agent": "EPSG:4326",
        "crs_expected": "EPSG:3857",
        "geometry_valid": True,
        "invalid_geometry_count": 0,
        "feature_count_match": True,
        "area_error_pct": 5.2,
        "area_within_tolerance": False,
        "length_within_tolerance": True,
        "attribute_fields_match": False,
        "missing_fields": ["population"],
        "extra_fields": [],
    }

    errors = classifier.classify_all(mock_vector, {}, {}, {})
    for e in errors:
        print(f"  -> [{e.subcategory}] {e.label_name}: {e.description}")
    print(f"  大类: {classifier.get_error_categories(errors)}")
