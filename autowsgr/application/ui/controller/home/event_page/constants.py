"""模块功能：维护活动地图页面的静态坐标、颜色和模板匹配校准。

上层调用：
- application.ui.controller.home.event_page.page：读取活动地图页面校准。

下层依赖：
- common.vision：提供颜色和感兴趣区域类型。

边界：
本模块只保存页面静态数据，不持有设备、运行状态或页面流程策略。
"""

from __future__ import annotations

from autowsgr.common.vision.adapters.pixel_matching import Color
from autowsgr.common.vision.adapters.template_matching import ROI


# ── 地图节点坐标 ─────────────────────────────────────────────────────────────

# 坐标均为 1280x720 参考画面的归一化值。
NODE_POSITIONS = {
    1: (0.1790, 0.1987),
    2: (0.3915, 0.2528),
    3: (0.9086, 0.2875),
    4: (0.2891, 0.6292),
    5: (0.5368, 0.4028),
    6: (0.6352, 0.6653),
}

# 活动标识存在专属布局时覆盖通用节点坐标。
NODE_POSITIONS_BY_EVENT = {
    '20260730': {
        1: (0.1774, 0.3153),
        2: (0.1743, 0.7264),
        3: (0.5008, 0.2987),
        4: (0.4907, 0.7459),
        5: (0.8133, 0.2945),
        6: (0.8125, 0.7459),
    },
}


# ── 页面控件坐标 ─────────────────────────────────────────────────────────────

# 坐标均为 1280x720 参考画面的归一化值，按页面控件用途排列。
CLICK_BACK = (0.0274, 0.0556)
CLICK_CLOSE_NODE_OVERLAY = (0.9500, 0.1403)
CLICK_DIFFICULTY = (0.1204, 0.9000)
CLICK_ENTRANCE_ALPHA = (0.8305, 0.6834)
CLICK_ENTRANCE_BETA = (0.8282, 0.5875)
CLICK_FIGHT_BUTTON = (0.8274, 0.8431)  # 模板缺失时的固定坐标兜底。


# ── 入口识别校准 ─────────────────────────────────────────────────────────────

# 入口颜色用于判断当前入口，ROI 用于限制节点详情浮层的按钮匹配范围。
ENTRANCE_ALPHA_PROBE = (0.8305, 0.6834)
ENTRANCE_ALPHA_COLOR = Color.of(249, 146, 37)
ENTRANCE_ALPHA_TOLERANCE = 40.0  # 颜色距离容差。
FIGHT_BUTTON_ROI = ROI(
    0.6000,
    0.6500,
    1.0000,
    1.0000,
)  # 限制出击按钮模板匹配范围。


__all__ = [  # noqa: RUF022 - exports follow the coordinate definition order
    'NODE_POSITIONS',
    'NODE_POSITIONS_BY_EVENT',
    'CLICK_BACK',
    'CLICK_CLOSE_NODE_OVERLAY',
    'CLICK_DIFFICULTY',
    'CLICK_ENTRANCE_ALPHA',
    'CLICK_ENTRANCE_BETA',
    'CLICK_FIGHT_BUTTON',
    'ENTRANCE_ALPHA_PROBE',
    'ENTRANCE_ALPHA_COLOR',
    'ENTRANCE_ALPHA_TOLERANCE',
    'FIGHT_BUTTON_ROI',
]
