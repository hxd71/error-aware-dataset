"""
生成阶段汇报 PPT — GIS Error-aware Agent 基准测试框架
学术风格，蓝白配色
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = os.path.dirname(os.path.abspath(__file__))
GT = os.path.join(ROOT, "evaluation", "Ground_Truth")

# ── 配色 ──
DARK_BLUE = RGBColor(0x1A, 0x36, 0x55)
MID_BLUE = RGBColor(0x2B, 0x7B, 0xBD)
LIGHT_BLUE = RGBColor(0xD6, 0xE8, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
ACCENT_GREEN = RGBColor(0x27, 0xAE, 0x60)
ACCENT_RED = RGBColor(0xC0, 0x39, 0x2B)
ACCENT_ORANGE = RGBColor(0xE6, 0x7E, 0x22)
BG_WHITE = RGBColor(0xFA, 0xFC, 0xFE)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_bar(slide, title_text, subtitle_text=None):
    """顶部蓝色标题栏"""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = DARK_BLUE
    bar.line.fill.background()

    title = slide.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(12), Inches(0.55))
    tf = title.text_frame
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    if subtitle_text:
        sub = slide.shapes.add_textbox(Inches(0.6), Inches(0.65), Inches(12), Inches(0.35))
        sf = sub.text_frame
        sp = sf.paragraphs[0]
        sp.text = subtitle_text
        sp.font.size = Pt(13)
        sp.font.color.rgb = RGBColor(0xAA, 0xCC, 0xEE)


def add_body_text(slide, text, left=0.6, top=1.4, width=12, height=5.5, size=14, color=None):
    """正文文本"""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.color.rgb = color or DARK_GRAY
        p.space_after = Pt(4)
    return tb


def add_footer(slide, text="GIS Error-aware Agent · 阶段汇报"):
    """页脚"""
    ft = slide.shapes.add_textbox(Inches(0.5), Inches(7.1), Inches(12), Inches(0.3))
    tf = ft.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(9)
    p.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    # 细线
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(7.05), Inches(12.3), Pt(1))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
    line.line.fill.background()


def add_table(slide, headers, rows, left, top, width, height, col_widths=None):
    """添加表格"""
    n_rows = len(rows) + 1
    n_cols = len(headers)
    table_shape = slide.shapes.add_table(n_rows, n_cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = table_shape.table

    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)

    # 表头
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_BLUE
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.alignment = PP_ALIGN.CENTER

    # 数据行
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = str(val)
            if i % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_BLUE
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                p.font.color.rgb = DARK_GRAY
                p.alignment = PP_ALIGN.CENTER

    return table


def add_icon_box(slide, text, color, left, top, width, height):
    """带颜色的圆角方块"""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(11)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER
    return shape


def add_image_safe(slide, path, left, top, width, height):
    """安全添加图片"""
    if os.path.exists(path):
        try:
            slide.shapes.add_picture(path, Inches(left), Inches(top), Inches(width), Inches(height))
        except Exception:
            pass


# ════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ═══════════════════════ Slide 1: 封面 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide, DARK_BLUE)

# 装饰线
deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2.8), Inches(2), Pt(4))
deco.fill.solid(); deco.fill.fore_color.rgb = MID_BLUE; deco.line.fill.background()

add_body_text(slide, "GIS Error-aware Agent\n基准测试框架构建", left=1, top=3.0, width=11, height=1.8, size=40, color=WHITE)

add_body_text(slide, "Benchmark 基准测试集 · Ground Truth 标准真值库 · 自动化核验 Evaluation Pipeline", left=1, top=5.0, width=11, height=0.6, size=16, color=RGBColor(0xAA, 0xCC, 0xEE))

add_body_text(slide, "短学期实习 · 阶段性工作汇报\n2026年7月", left=1, top=5.8, width=11, height=0.8, size=13, color=RGBColor(0x88, 0x99, 0xAA))

# ═══════════════════════ Slide 2: 目录 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "汇报提纲")

items = [
    ("01", "项目背景与研究目标", "GIS Error-aware Agent 研究工作计划概述"),
    ("02", "Benchmark 基准测试集构建", "任务分类 · 数据组织 · 陷阱设计"),
    ("03", "Ground Truth 标准真值库", "GT 生成流程 · 文件规范 · 量化阈值"),
    ("04", "Evaluation Pipeline 核验引擎", "矢量/栅格/表格/可视化 四层比对架构"),
    ("05", "GIS 错误分类体系", "A–E 五大类 15 子类错误标签"),
    ("06", "先导测试与验证结果", "Pilot Test 5 任务实测数据"),
    ("07", "阶段成果与下一步计划", "代码交付物 · 后续工作安排"),
]
for i, (num, title, desc) in enumerate(items):
    y = 1.5 + i * 0.78
    # 编号
    num_box = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.2), Inches(y), Inches(0.5), Inches(0.5))
    num_box.fill.solid(); num_box.fill.fore_color.rgb = DARK_BLUE; num_box.line.fill.background()
    tf = num_box.text_frame; p = tf.paragraphs[0]; p.text = num; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER

    add_body_text(slide, title, left=2.0, top=y - 0.02, width=6, height=0.4, size=17, color=DARK_BLUE)
    add_body_text(slide, desc, left=2.0, top=y + 0.35, width=6, height=0.3, size=11, color=RGBColor(0x77, 0x77, 0x77))

add_footer(slide)

# ═══════════════════════ Slide 3: 项目背景 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "项目背景与研究目标", "基于 Curated GeoAgent Dataset 的 GIS Error-aware Agent 评测体系")

bullets = (
    "▎研究背景\n"
    "  • 大语言模型驱动的 GIS 智能体在空间分析任务中存在系统性错误（CRS 不匹配、无效几何、栅格异常等）\n"
    "  • 缺乏标准化的 GIS Agent 评测基准，难以量化 Agent 的空间推理能力与错误模式\n"
    "  • 现有评测方法未覆盖\"陷阱任务\"——主动注入 GIS 异常的鲁棒性测试\n\n"
    "▎核心目标\n"
    "  • 构建 40–50 条 GIS 空间分析 Benchmark 任务集，覆盖 5 大业务场景 × 3 级复杂度\n"
    "  • 建立 Ground Truth 标准真值库，提供脱离 AI 的 100% 正确参考结果\n"
    "  • 实现 Evaluation Pipeline 自动化核验引擎，完成矢量/栅格/表格/可视化四层比对\n"
    "  • 定义 A–E 五大类 15 子类 GIS 错误分类标签，为 Error-aware Agent 提供修复依据"
)
add_body_text(slide, bullets, top=1.4, size=13)

add_footer(slide)

# ═══════════════════════ Slide 4: Benchmark 构建 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "Benchmark 基准测试集构建", "任务二：40–50 条 GIS 空间分析任务 · 三层复杂度 · 五大场景")

# 任务分类表
add_table(slide,
    ["分类", "数量", "复杂度", "说明"],
    [
        ["单步基础任务", "15 个", "Level 1", "缓冲区、坡度计算、属性查询等单一操作"],
        ["复合多步骤工作流", "20 个", "Level 2", "空间连接→聚合→统计等操作链组合"],
        ["错误诱导陷阱任务", "15 个", "Level 3", "主动注入 CRS 不匹配、无效几何、NoData 异常等扰动"],
    ],
    left=0.6, top=1.5, width=8, height=1.8, col_widths=[2.2, 1.2, 1.4, 3.2]
)

# 五大场景
add_body_text(slide, "▎覆盖五大业务场景", left=0.6, top=3.6, width=12, height=0.4, size=14, color=DARK_BLUE)

scenes = ["🚗 交通空间分析", "🏔 栅格处理", "🔗 空间属性关联", "🕸 网络拓扑", "🗺 综合空间决策"]
for i, s in enumerate(scenes):
    add_icon_box(slide, s, MID_BLUE, 0.6 + i * 2.5, 4.1, 2.2, 0.55)

# 陷阱类型
add_body_text(slide, "▎五种陷阱注入类型", left=0.6, top=4.9, width=12, height=0.4, size=14, color=ACCENT_RED)
traps = ["CRS 不匹配\n(EPSG:4326 vs 3857)", "无效自相交几何\n(蝴蝶结多边形)", "栅格 NoData 异常\n(空值处理)", "属性空值/\n特殊字段", "断裂路网\n(拓扑中断)"]
for i, t in enumerate(traps):
    add_icon_box(slide, t, ACCENT_RED, 0.6 + i * 2.5, 5.4, 2.2, 0.75)

add_footer(slide)

# ═══════════════════════ Slide 5: 任务配置规范 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "数据集组织与任务配置规范", "cases.json ≡ Benchmark_Tasks.json · 标准化字段结构")

add_table(slide,
    ["字段", "类型", "说明"],
    [
        ["case_id", "string", "全局唯一编号 curated_geoagent_001 ~ 140"],
        ["task_type", "enum", "vector_single / raster_single / composite_workflow / trap"],
        ["complexity_level", "int (1–3)", "1=单步, 2=多流程, 3=逻辑推理 (陷阱)"],
        ["scenario", "string", "交通空间分析 / 栅格处理 / 空间属性关联 / 网络拓扑 / 综合空间决策"],
        ["task + output_requirements", "string ×2", "自然语言任务指令 + 输出约束说明"],
        ["operations", "array", "操作链: buffer / clip / dissolve / spatial_join / reproject / raster_calc"],
        ["output_types", "array", "期望输出: [vector, raster, table, map]"],
        ["trap_type + is_trap", "string + bool", "陷阱类型标记 + 预期诱发错误代码"],
        ["thresholds", "object", "任务级自定义验证阈值 (容差百分比等)"],
    ],
    left=0.4, top=1.4, width=12.5, height=4.8, col_widths=[3.2, 2.2, 7.1]
)

add_footer(slide)

# ═══════════════════════ Slide 6: GT 标准真值库 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "Ground Truth 标准真值库", "脱离 AI Agent，使用 GeoPandas / Rasterio 专业工具人工运行的 100% 正确基准")

add_body_text(slide, "▎单任务 GT 文件规范", left=0.6, top=1.3, width=6, height=0.4, size=14, color=DARK_BLUE)
add_table(slide,
    ["文件", "固定命名", "格式", "说明"],
    [
        ["矢量标准结果", "expected_vector.geojson", "GeoJSON", "经 make_valid() 修复的可信几何"],
        ["栅格标准结果", "expected_raster.tif", "GeoTIFF", "保持原始分辨率与范围的栅格"],
        ["统计真值表", "stats.csv", "UTF-8 CSV", "要素数/总面积/分组统计/均值"],
        ["标准制图", "map.png", "150 DPI PNG", "含标题/指北针/比例尺/图例"],
        ["验证阈值", "thresholds.json", "JSON", "面积容差 5% / 栅格统计容差 5%"],
    ],
    left=0.4, top=1.8, width=7.5, height=3.0, col_widths=[1.8, 2.2, 1.3, 2.2]
)

add_body_text(slide, "▎批量生成流程", left=0.6, top=5.0, width=6, height=0.4, size=14, color=DARK_BLUE)
flow = (
    "cases.json → 解析 inputs / operations 操作链 → GeoPandas / Rasterio 执行\n"
    "→ 输出到 Ground_Truth/{case_id}/  → 生成 generation_manifest.json 清单"
)
add_body_text(slide, flow, left=0.6, top=5.4, width=8, height=0.8, size=12)

# 右侧：GT 示例图片
add_image_safe(slide, os.path.join(GT, "curated_geoagent_001", "map.png"), 8.3, 1.8, 2.3, 1.6)
add_image_safe(slide, os.path.join(GT, "curated_geoagent_002", "map.png"), 10.8, 1.8, 2.3, 1.6)
add_image_safe(slide, os.path.join(GT, "curated_geoagent_003", "map.png"), 8.3, 3.6, 2.3, 1.6)
add_image_safe(slide, os.path.join(GT, "curated_geoagent_005", "map.png"), 10.8, 3.6, 2.3, 1.6)
add_body_text(slide, "GT制图示例: 道路网络 / DEM / 普查区块 / 土地利用", left=8.3, top=5.4, width=5, height=0.4, size=9, color=RGBColor(0x77, 0x77, 0x77))

add_footer(slide)

# ═══════════════════════ Slide 7: Evaluation Pipeline ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "Evaluation Pipeline 自动化核验引擎", "gis_evaluator.py — 矢量 · 栅格 · 表格 · 可视化 四层比对")

# 四大核验器 2×2 布局
verifiers = [
    ("① 矢量核验 VectorVerifier", MID_BLUE,
     "• 文件存在性检查\n• CRS 一致性（不匹配时自动重投影）\n• 几何有效性（shapely is_valid）\n• 要素数量匹配\n• 面积/长度相对误差（默认 5% 容差）\n• 属性字段名称匹配"),
    ("② 栅格核验 RasterVerifier", RGBColor(0x1A, 0x6B, 0x4A),
     "• 波段数、分辨率一致性\n• 空间范围偏差（1e-6 容差）\n• NoData 值定义匹配\n• 统计指标：RMSE / MAE / R²\n• 不对齐时自动取交集对比"),
    ("③ 表格核验 TableVerifier", ACCENT_ORANGE,
     "• CSV 列名匹配（缺失/多余检测）\n• 行数一致性\n• 数值列逐行比对\n• 分组统计量偏差\n• NaN 一致性判断"),
    ("④ 可视化核验 VisualVerifier", ACCENT_RED,
     "• 空白输出检测（标准差 < 5）\n• 像素差异率 + 颜色直方图相关\n• 启发性制图元素检测\n• 交叉推理：CRS+范围 → 图层错位\n• 自动标记 requires_visual_check"),
]

for i, (title, color, desc) in enumerate(verifiers):
    left = 0.3 + (i % 2) * 6.4
    top = 1.5 + (i // 2) * 2.9
    # 标题框
    hdr = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(6.0), Inches(0.45))
    hdr.fill.solid(); hdr.fill.fore_color.rgb = color; hdr.line.fill.background()
    tf = hdr.text_frame; p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    add_body_text(slide, desc, left=left + 0.15, top=top + 0.55, width=5.7, height=2.2, size=11)

add_footer(slide)

# ═══════════════════════ Slide 8: 错误分类 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "GIS 错误分类体系", "error_classifier.py — 核验失败自动映射为 A–E 五大类 15 子类错误标签")

add_table(slide,
    ["代码", "大类", "子类名称", "触发条件"],
    [
        ["A1", "空间参考系", "CRS 不匹配", "输出坐标系与 GT 不一致"],
        ["A2", "空间参考系", "投影转换错误", "投影参数或转换过程异常"],
        ["A3", "空间参考系", "坐标越界", "几何坐标超出有效范围"],
        ["B1", "几何完整性", "无效几何 / 自相交", "自相交环、重复节点等无效结构"],
        ["B2", "几何完整性", "拓扑错误", "面重叠/空隙、线未正确连接"],
        ["B3", "几何完整性", "几何类型不匹配", "输出类型与期望不一致"],
        ["C1", "属性 / 表格", "字段缺失 / 不匹配", "缺少必要字段或包含多余字段"],
        ["C2", "属性 / 表格", "属性值错误", "字段值计算错误或类型不匹配"],
        ["C3", "属性 / 表格", "统计量偏差", "分组统计/聚合超出允许误差"],
        ["D1", "栅格数据", "波段 / 分辨率不匹配", "波段数或像元分辨率不一致"],
        ["D2", "栅格数据", "NoData 异常", "NoData 定义错误或处理不当"],
        ["D3", "栅格数据", "栅格范围偏差", "空间范围/原点偏移超阈值"],
        ["E1", "可视化/逻辑", "图层错位 / 空白输出", "图层空间偏移或空白渲染"],
        ["E2", "可视化/逻辑", "制图元素缺失", "缺少图例/比例尺/指北针/标题"],
        ["E3", "可视化/逻辑", "隐形逻辑错误", "表面正常但深层有逻辑缺陷"],
    ],
    left=0.3, top=1.3, width=12.7, height=5.5, col_widths=[0.8, 1.8, 2.8, 7.3]
)

add_footer(slide)

# ═══════════════════════ Slide 9: 评测流程 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "评测流程与报告输出", "批量评测 → 四层核验 → 错误分类 → 逐任务 JSON + 汇总 MD 双格式报告")

steps = [
    ("加载任务", "cases.json\n读取全部任务", DARK_BLUE),
    ("GT 对照", "Ground_Truth/\n{case_id}/ 目录", MID_BLUE),
    ("Agent 输出", "agent_outputs/\n{case_id}/ 目录", RGBColor(0x1A, 0x6B, 0x4A)),
    ("四层核验", "Vector / Raster\nTable / Visual", ACCENT_ORANGE),
    ("错误分类", "A-E 15子类\n自动标签映射", ACCENT_RED),
    ("报告生成", "JSON + Markdown\n逐任务 + 汇总", RGBColor(0x8E, 0x44, 0xAD)),
]
for i, (title, desc, color) in enumerate(steps):
    left = 0.5 + i * 2.1
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(1.8), Inches(1.8), Inches(1.5))
    box.fill.solid(); box.fill.fore_color.rgb = color; box.line.fill.background()
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    p2 = tf.add_paragraph(); p2.text = desc; p2.font.size = Pt(9); p2.font.color.rgb = WHITE; p2.alignment = PP_ALIGN.CENTER
    # 箭头
    if i < len(steps) - 1:
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(left + 1.85), Inches(2.3), Inches(0.2), Inches(0.25))
        arr.fill.solid(); arr.fill.fore_color.rgb = RGBColor(0xBB, 0xBB, 0xBB); arr.line.fill.background()

add_body_text(slide, "▎报告输出", left=0.6, top=3.7, width=6, height=0.4, size=14, color=DARK_BLUE)
add_table(slide,
    ["报告文件", "内容"],
    [
        ["evaluation_summary.json", "JSON 汇总：总体通过率、错误按大类/子类分布、需视觉审查任务列表"],
        ["evaluation_summary.md", "Markdown 格式：统计表格 + 错误分类 + 逐任务结果"],
        ["{case_id}_eval_report.json", "单任务完整报告：15+ 核验指标详情 + 错误标签 + 指标偏差值"],
    ],
    left=0.4, top=4.1, width=12.5, height=1.8, col_widths=[3.5, 9.0]
)

add_body_text(slide, "评测框架自动拼合 task + output_requirements 生成 Agent 查询，评测元数据不注入 Agent 上下文。", left=0.6, top=6.2, width=12, height=0.4, size=10, color=RGBColor(0x88, 0x88, 0x88))

add_footer(slide)

# ═══════════════════════ Slide 10: 先导测试 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "先导测试结果 (Pilot Test)", "5 条模板任务 · 2 类正确输出 + 3 类含错输出 · 全流程贯通验证")

add_table(slide,
    ["Case ID", "任务类型", "复杂度", "陷阱", "结果", "检测到的错误"],
    [
        ["curated_geoagent_001", "矢量单步 (buffer)", "L1", "—", "✅ PASS", "0 errors"],
        ["curated_geoagent_002", "栅格单步 (slope)", "L1", "—", "✅ PASS", "0 errors"],
        ["curated_geoagent_003", "复合工作流 (spatial join)", "L2", "—", "△ PARTIAL", "C1 字段缺失 (population)"],
        ["curated_geoagent_004", "陷阱 (无效几何)", "L3", "invalid_geom", "△ PARTIAL", "C1 表格字段不匹配"],
        ["curated_geoagent_005", "陷阱 (CRS不匹配)", "L3", "crs_mismatch", "△ PARTIAL", "D3 栅格范围偏移 + 表格差异"],
    ],
    left=0.3, top=1.4, width=12.7, height=2.7, col_widths=[2.6, 2.8, 1.0, 1.5, 1.5, 3.3]
)

add_body_text(slide, "▎关键验证结论", left=0.6, top=4.3, width=6, height=0.4, size=14, color=DARK_BLUE)
findings = (
    "✓ 正确输出 (Task 001/002): Vector 全项通过 → 核验引擎无假阳性\n"
    "✓ 字段缺失 (Task 003): C1 错误被精确检出，missing_fields = ['population']\n"
    "✓ CRS 陷阱 (Task 005): 栅格范围偏移 1000m 被 D3 标签正确标记\n"
    "✓ 可视化异常: Task 003 地图缺失 → requires_visual_check 自动设为 true\n"
    "△ 统计表格式差异被统一归类为 C1，后续需区分表格结构与统计值偏差"
)
add_body_text(slide, findings, left=0.6, top=4.7, width=12, height=2.5, size=12)

add_footer(slide)

# ═══════════════════════ Slide 11: 代码交付 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "阶段成果 — 代码交付物", "14 个文件 · ~3,030 行 Python · 2 个 JSON Schema · 完整可运行")

add_table(slide,
    ["模块", "文件", "行数", "核心功能"],
    [
        ["核验引擎", "gis_evaluator.py", "~580", "Vector / Raster / Table / Visual 四层比对"],
        ["错误分类", "error_classifier.py", "~380", "A-E 五大类 15 子类自动标签映射"],
        ["GT 生成", "generate_ground_truth.py", "~440", "批量执行操作链，输出标准化 GT 文件"],
        ["批量评测", "batch_evaluate.py", "~330", "遍历全部任务，JSON + MD 双格式汇总"],
        ["主入口", "eval_curated_geoagent.py", "~200", "一键运行基准测试，支持 Pilot Test 模式"],
        ["数据生成", "generate_sample_data.py", "~180", "合成道路/DEM/普查/陷阱等 GIS 测试数据"],
        ["Agent模拟", "generate_agent_outputs.py", "~110", "正确/含错模拟输出，验证评测流水线"],
        ["Schema", "evaluation_schema.json", "~250", "报告 JSON Schema 标准化定义"],
        ["Schema", "cases_schema.json", "~80", "任务配置 JSON Schema"],
        ["文档", "README.md + evaluation/README.md", "~580", "项目总结 + 评测模块详细文档"],
    ],
    left=0.2, top=1.3, width=12.9, height=5.2, col_widths=[1.5, 3.2, 0.9, 7.3]
)

add_body_text(slide, "技术栈: Python 3.9 · GeoPandas · Rasterio · Shapely · NumPy · Pandas · Matplotlib · python-pptx", left=0.6, top=6.7, width=12, height=0.4, size=10, color=RGBColor(0x88, 0x88, 0x88))

add_footer(slide)

# ═══════════════════════ Slide 12: 下一步 ═══════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_title_bar(slide, "下一步工作计划")

plans = [
    ("近期 (1–2 周)", MID_BLUE, [
        "完成全部 40–50 条 Benchmark 任务编写与 cases.json 填充",
        "准备真实 GIS 数据集（OpenStreetMap / SRTM / 统计年鉴）替代合成数据",
        "对接第一个 GIS Agent 模型，采集真实 Agent 输出进行评测",
    ]),
    ("中期 (3–4 周)", ACCENT_ORANGE, [
        "扩展表格核验：支持分组统计值比对与密度/总量校验",
        "增强可视化核验：引入结构相似性 SSIM 指标替代启发性判断",
        "实现 Evaluation_Reports 自动生成 HTML 可视化报告",
    ]),
    ("远期 (5–8 周)", ACCENT_RED, [
        "将错误分类结果反馈至 Agent 的 Error-aware 修复循环",
        "扩展至更大规模基准测试（140 条 curated_geoagent 全量任务）",
        "撰写实验论文：GIS Agent 系统性错误分析",
    ]),
]

for i, (phase, color, items) in enumerate(plans):
    top = 1.5 + i * 1.9
    hdr = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(top), Inches(2.5), Inches(0.4))
    hdr.fill.solid(); hdr.fill.fore_color.rgb = color; hdr.line.fill.background()
    tf = hdr.text_frame; p = tf.paragraphs[0]; p.text = phase; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for j, item in enumerate(items):
        add_body_text(slide, f"  {j+1}. {item}", left=3.2, top=top + j * 0.45, width=9.5, height=0.4, size=12)

add_footer(slide)

# ═══════════════════════ Slide 13: 致谢 ═══════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, DARK_BLUE)

deco2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.5), Inches(2.5), Inches(2.3), Pt(4))
deco2.fill.solid(); deco2.fill.fore_color.rgb = MID_BLUE; deco2.line.fill.background()

add_body_text(slide, "感谢聆听", left=1, top=2.8, width=11, height=1.5, size=44, color=WHITE)
add_body_text(slide, "GIS Error-aware Agent Benchmark\n阶段工作汇报", left=1, top=4.2, width=11, height=1.2, size=18, color=RGBColor(0xAA, 0xCC, 0xEE))
add_body_text(slide, "欢迎提问与指导", left=1, top=5.8, width=11, height=0.5, size=14, color=RGBColor(0x88, 0x99, 0xAA))

# ── 保存 ──
output_path = os.path.join(ROOT, "阶段汇报_GIS_Error_Aware_Agent.pptx")
prs.save(output_path)
print(f"✅ PPT 已生成: {output_path}")
print(f"   共 {len(prs.slides)} 页幻灯片")
