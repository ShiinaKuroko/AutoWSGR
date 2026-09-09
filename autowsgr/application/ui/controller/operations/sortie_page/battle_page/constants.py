"""模块功能：维护战斗地图聚合页面和普通出征导航的私有校准参数。

上层调用：
- application.ui.controller.operations.sortie_page.battle_page.base：读取地图页面和标签状态。
- application.ui.controller.operations.sortie_page.sortie：执行普通出征章节导航。
- application.ui.controller.operations.sortie_page.decisive：进入决战总览。
- testing.ui：执行地图页面和出征准备验证。

下层依赖：
- common.vision：提供地图页面颜色类型。

本模块只保存战斗地图聚合页仍在使用的物理校准；演习、战役和远征专用参数由各自
页面目录所有。旧 common.calibration.map 保留为外部兼容入口，不再是本页面依赖。
"""

from __future__ import annotations

from autowsgr.common.vision import Color


# ── 地图页面和顶部标签 ──────────────────────────────────────────────────────

CLICK_BACK = (0.0219, 0.0584)  # 地图页面返回按钮，用于回到母港主页。
PANEL_POSITIONS = {
    'sortie': (0.1844, 0.0514),  # 出征标签，用于打开普通章节选择面板。
    'exercise': (0.3157, 0.0500),  # 演习标签，用于打开演习对手面板。
    'expedition': (0.4422, 0.0514),  # 远征标签，用于打开远征收取面板。
    'battle': (0.5750, 0.0459),  # 战役标签，用于打开战役选择面板。
    'decisive': (0.6985, 0.0514),  # 决战标签，用于打开决战入口面板。
}  # 地图顶部标签坐标，用于切换五个出征相关页面。

CLICK_ENTER_SORTIE = (0.6250, 0.5560)  # 普通出征入口，用于进入章节选择页面。
CLICK_ENTER_DECISIVE = (0.1200, 0.2090)  # 决战入口，用于进入决战总览页面。
CLICK_MAP_NEXT = (0.9761, 0.5130)  # 章节右切按钮，用于查看后续章节。
CLICK_MAP_PREV = (0.2573, 0.5130)  # 章节左切按钮，用于查看前置章节。


# ── 普通出征章节侧栏 ────────────────────────────────────────────────────────

CHAPTER_PROBE_Y = {
    1: (0.7000, 0.6450, 0.7550, 0.5900),  # 向下查找高亮章节的扫描范围。
    -1: (0.3000, 0.3550, 0.2450, 0.4100),  # 向上查找高亮章节的扫描范围。
}  # 章节方向探针范围，用于高亮识别失败时选择备用点击位置。
SIDEBAR_SAFE_MARGIN = 0.0400  # 章节侧栏安全边距，用于避开顶部和底部控件。
SIDEBAR_JITTER = 0.0060  # 章节点击基础抖动范围，用于避开文字边缘。
SIDEBAR_FALLBACK_JITTER = 0.0080  # 章节点击备用抖动范围，用于基础点击未命中时重试。
SIDEBAR_FALLBACK_JITTER_AFTER_SWIPE = 0.0100  # 侧栏滑动后抖动范围，用于补偿动画偏移。
SIDEBAR_SWIPE_TOP = (0.8000, 0.2000)  # 侧栏上滑起止坐标，用于寻找更早章节。
SIDEBAR_SWIPE_BOTTOM = (0.2000, 0.8000)  # 侧栏下滑起止坐标，用于寻找更晚章节。
SIDEBAR_SWIPE_RESET_TOP = (0.2500, 0.8000)  # 侧栏复位起点，用于恢复可预测位置。
SIDEBAR_SWIPE_RESET_BOTTOM = (0.8000, 0.2500)  # 侧栏复位终点，用于恢复可预测位置。
SIDEBAR_SWIPE_INITIAL_DURATION = 0.35  # 首次侧栏滑动时长，用于等待章节列表移动。
SIDEBAR_SWIPE_DURATION = 0.45  # 后续侧栏滑动时长，用于等待章节列表移动。
SIDEBAR_SWIPE_SETTLE_DELAY = 0.30  # 侧栏滑动等待时间，用于读取新的高亮位置。
SIDEBAR_RESET_SETTLE_DELAY = 0.50  # 侧栏复位等待时间，用于重新识别章节列表。
SIDEBAR_SCAN_X = 0.0800  # 章节高亮扫描横坐标，用于读取侧栏亮度变化。
SIDEBAR_SCAN_Y_RANGE = (0.1200, 0.8800)  # 高亮扫描纵向范围，用于排除边缘控件。
SIDEBAR_SCAN_STEP = 0.0100  # 高亮扫描步长，用于平衡定位精度和截图采样量。
SIDEBAR_BRIGHTNESS_THRESHOLD = 150  # 高亮亮度阈值，用于过滤普通背景像素。
CHAPTER_SPACING = 0.1200  # 章节条目间距，用于推算目标章节的纵坐标。
SIDEBAR_CLICK_X = 0.1000  # 章节侧栏点击横坐标，用于点击推算出的章节位置。
CHAPTER_NAV_DELAY = 0.50  # 章节导航动作间隔，用于等待侧栏动画完成。
CHAPTER_NAV_MAX_ATTEMPTS = 20  # 章节导航最大尝试次数，用于限制失败循环。
CHAPTER_SLOT_CENTERS = (0.3100, 0.4300, 0.5500, 0.6700, 0.7900)  # 五个固定章节槽位的点击纵坐标。
CHAPTER_SLOT_ROIS = (
    (0.0550, 0.2650, 0.1700, 0.3550),  # 第 1 个章节槽位 OCR 区域，用于读取侧栏上方标签。
    (0.0550, 0.3850, 0.1700, 0.4750),  # 第 2 个章节槽位 OCR 区域，用于读取侧栏上方标签。
    (0.0550, 0.5050, 0.1700, 0.5950),  # 第 3 个章节槽位 OCR 区域，用于读取侧栏中部标签。
    (0.0550, 0.6250, 0.1700, 0.7150),  # 第 4 个章节槽位 OCR 区域，用于读取侧栏下方标签。
    (0.0550, 0.7450, 0.1700, 0.8350),  # 第 5 个章节槽位 OCR 区域，用于读取侧栏底部标签。
)  # 固定槽位 OCR 裁剪区域，覆盖章节标签而避开侧栏边缘控件。
CHAPTER_SLOT_CENTER_INDEX = 2  # 固定槽位中间索引，用于作为当前章节的侧栏锚点。
CHAPTER_OCR_ALLOWLIST = '0123456789第章一二三四五六七八九十'  # 章节标签 OCR 允许字符。
MAP_NAV_SETTLE_DELAY = 1.5000  # 章节或地图切换后的等待时间，用于避开页面动画过渡帧。


# ── 地图状态和结算 ──────────────────────────────────────────────────────────

EXPEDITION_NOTIF_COLOR = Color.of(245, 88, 47)  # 远征完成通知颜色，用于识别顶部通知。
EXPEDITION_TOLERANCE = 40.0  # 远征通知颜色容差，用于过滤截图渲染误差。
EXPEDITION_NOTIF_PROBE = (0.4953, 0.0213)  # 远征通知探测点，用于读取通知状态。
TITLE_CROP_REGION = (0.7000, 0.1800, 0.9000, 0.2150)  # 地图标题 OCR 区域，用于读取章节和关卡。
CLICK_EXPEDITION_SKIP = (0.7600, 0.5000)  # 远征结算跳过区域，用于结束奖励动画。


# ── 测试和兼容入口使用的地图节点 ────────────────────────────────────────────

MAP_NODE_POSITIONS = {
    1: (0.5000, 0.2000),  # 第 1 个地图节点，用于进入对应关卡。
    2: (0.5000, 0.3500),  # 第 2 个地图节点，用于进入对应关卡。
    3: (0.5000, 0.5000),  # 第 3 个地图节点，用于进入对应关卡。
    4: (0.5000, 0.6500),  # 第 4 个地图节点，用于进入对应关卡。
    5: (0.5000, 0.8000),  # 第 5 个地图节点，用于进入对应关卡。
}  # 地图节点测试坐标，用于演示普通出征入口。


__all__ = [
    'CHAPTER_NAV_DELAY',
    'CHAPTER_NAV_MAX_ATTEMPTS',
    'CHAPTER_OCR_ALLOWLIST',
    'CHAPTER_PROBE_Y',
    'CHAPTER_SLOT_CENTERS',
    'CHAPTER_SLOT_CENTER_INDEX',
    'CHAPTER_SLOT_ROIS',
    'CHAPTER_SPACING',
    'CLICK_BACK',
    'CLICK_ENTER_DECISIVE',
    'CLICK_ENTER_SORTIE',
    'CLICK_EXPEDITION_SKIP',
    'CLICK_MAP_NEXT',
    'CLICK_MAP_PREV',
    'EXPEDITION_NOTIF_COLOR',
    'EXPEDITION_NOTIF_PROBE',
    'EXPEDITION_TOLERANCE',
    'MAP_NAV_SETTLE_DELAY',
    'MAP_NODE_POSITIONS',
    'PANEL_POSITIONS',
    'SIDEBAR_BRIGHTNESS_THRESHOLD',
    'SIDEBAR_CLICK_X',
    'SIDEBAR_FALLBACK_JITTER',
    'SIDEBAR_FALLBACK_JITTER_AFTER_SWIPE',
    'SIDEBAR_JITTER',
    'SIDEBAR_RESET_SETTLE_DELAY',
    'SIDEBAR_SAFE_MARGIN',
    'SIDEBAR_SCAN_STEP',
    'SIDEBAR_SCAN_X',
    'SIDEBAR_SCAN_Y_RANGE',
    'SIDEBAR_SWIPE_BOTTOM',
    'SIDEBAR_SWIPE_DURATION',
    'SIDEBAR_SWIPE_INITIAL_DURATION',
    'SIDEBAR_SWIPE_RESET_BOTTOM',
    'SIDEBAR_SWIPE_RESET_TOP',
    'SIDEBAR_SWIPE_SETTLE_DELAY',
    'SIDEBAR_SWIPE_TOP',
    'TITLE_CROP_REGION',
]
