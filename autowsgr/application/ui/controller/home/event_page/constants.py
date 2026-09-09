"""模块功能：维护活动地图页面的节点、入口和浮层识别校准参数。

上层调用：
- application.ui.controller.home.event_page.page：执行活动地图页面操作。

下层依赖：
- common.vision：提供颜色和感兴趣区域类型。

参数属于活动地图页面；活动名称、难度策略、节点业务和出征返回导航仍由页面或
导航层负责。本模块不读取共享校准文件，避免页面专用参数产生第二个运行时来源。
"""

from __future__ import annotations

from autowsgr.common.vision import Color
from autowsgr.common.vision.roi import ROI


# ── 节点和页面操作坐标 ───────────────────────────────────────────────────────

NODE_POSITIONS = {
    1: (0.1790, 0.1987),  # 通用活动节点 1，用于打开对应关卡详情。
    2: (0.3915, 0.2528),  # 通用活动节点 2，用于打开对应关卡详情。
    3: (0.9086, 0.2875),  # 通用活动节点 3，用于打开对应关卡详情。
    4: (0.2891, 0.6292),  # 通用活动节点 4，用于打开对应关卡详情。
    5: (0.5368, 0.4028),  # 通用活动节点 5，用于打开对应关卡详情。
    6: (0.6352, 0.6653),  # 通用活动节点 6，用于打开对应关卡详情。
}  # 通用活动节点坐标，用于没有活动专属布局时选择关卡。

NODE_POSITIONS_BY_EVENT = {
    '20260730': {
        1: (0.1774, 0.3153),  # 20260730 活动节点 1，用于打开对应关卡详情。
        2: (0.1743, 0.7264),  # 20260730 活动节点 2，用于打开对应关卡详情。
        3: (0.5008, 0.2987),  # 20260730 活动节点 3，用于打开对应关卡详情。
        4: (0.4907, 0.7459),  # 20260730 活动节点 4，用于打开对应关卡详情。
        5: (0.8133, 0.2945),  # 20260730 活动节点 5，用于打开对应关卡详情。
        6: (0.8125, 0.7459),  # 20260730 活动节点 6，用于打开对应关卡详情。
    },  # 20260730 活动专属节点布局，用于适配地图页面位置。
}  # 活动专属节点坐标，用于覆盖通用节点布局。

CLICK_BACK = (0.0274, 0.0556)  # 活动地图返回按钮，用于回到母港主页。
CLICK_FIGHT_BUTTON = (0.8274, 0.8431)  # 固定出击按钮，用于模板缺失时进入准备页。
CLICK_CLOSE_NODE_OVERLAY = (0.9500, 0.1403)  # 节点详情关闭按钮，用于恢复活动地图。
CLICK_DIFFICULTY = (0.1204, 0.9000)  # 难度切换按钮，用于切换简单/困难模式。
CLICK_ENTRANCE_ALPHA = (0.8305, 0.6834)  # Alpha 入口按钮，用于选择活动入口。
CLICK_ENTRANCE_BETA = (0.8282, 0.5875)  # Beta 入口按钮，用于选择活动入口。


# ── 页面状态探测和识别区域 ───────────────────────────────────────────────────

ENTRANCE_ALPHA_PROBE = (0.8305, 0.6834)  # Alpha 入口状态探测点，用于读取当前入口。
ENTRANCE_ALPHA_COLOR = Color.of(249, 146, 37)  # Alpha 入口选中颜色，用于判断当前入口。
ENTRANCE_ALPHA_TOLERANCE = 40.0  # Alpha 入口颜色容差，用于兼容渲染差异。
FIGHT_BUTTON_ROI = ROI(0.6000, 0.6500, 1.0000, 1.0000)  # 出击按钮匹配区域，用于过滤背景误报。


__all__ = [
    'CLICK_BACK',
    'CLICK_CLOSE_NODE_OVERLAY',
    'CLICK_DIFFICULTY',
    'CLICK_ENTRANCE_ALPHA',
    'CLICK_ENTRANCE_BETA',
    'CLICK_FIGHT_BUTTON',
    'ENTRANCE_ALPHA_COLOR',
    'ENTRANCE_ALPHA_PROBE',
    'ENTRANCE_ALPHA_TOLERANCE',
    'FIGHT_BUTTON_ROI',
    'NODE_POSITIONS',
    'NODE_POSITIONS_BY_EVENT',
]
