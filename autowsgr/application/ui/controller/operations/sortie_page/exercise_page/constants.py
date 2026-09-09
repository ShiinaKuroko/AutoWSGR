"""模块功能：维护演习面板的坐标、颜色和列表滚动常量。

上层调用：
- application.ui.controller.operations.sortie_page.exercise_page.page：读取演习面板操作校准。

下层依赖：
- 无。

本模块只保存演习页面的静态校准数据，不保存页面状态、设备对象或业务规则。
"""

from __future__ import annotations


# ── 列表状态和操作坐标 ──────────────────────────────────────────────────────

ARROW_GRAY = (177, 171, 176)  # 演习列表边界箭头颜色，用于判断列表是否到顶或到底。
ARROW_TOLERANCE: float = 60.0  # 边界箭头颜色容差，用于兼容截图渲染差异。
ARROW_UP_PROBE = (0.9719, 0.1098)  # 上箭头探测点，用于判断列表顶部状态。
ARROW_DOWN_PROBE = (0.9719, 0.9056)  # 下箭头探测点，用于判断列表底部状态。
CHALLENGE_COLOR = (33, 132, 226)  # 演习挑战按钮颜色，用于识别可挑战对手。
CHALLENGE_TOLERANCE: float = 50.0  # 挑战按钮颜色容差，用于兼容截图渲染差异。
CHALLENGE_PROBES = (
    (0.8024, 0.1848),  # 第 1 个可见对手的挑战状态探测点。
    (0.8024, 0.3889),  # 第 2 个可见对手的挑战状态探测点。
    (0.8024, 0.5931),  # 第 3 个可见对手的挑战状态探测点。
    (0.8024, 0.7959),  # 第 4 个可见对手的挑战状态探测点。
)
CLICK_RIVAL_INFO = (0.6930, 0.7403)  # 对手信息刷新按钮，用于刷新当前阵容。
CLICK_START_BATTLE = (0.8375, 0.7223)  # 演习开始按钮，用于进入出征准备页面。
SWIPE_TO_TOP = (
    0.8336,
    0.3709,
    0.8336,
    0.7403,
)  # 演习列表上滑坐标，用于显示对手 1-4。
SWIPE_TO_BOTTOM = (
    0.8336,
    0.7403,
    0.8336,
    0.3709,
)  # 演习列表下滑坐标，用于显示对手 5。
SWIPE_DELAY: float = 0.8  # 演习列表滑动等待时间，用于等待列表内容稳定。


__all__ = [
    'ARROW_DOWN_PROBE',
    'ARROW_GRAY',
    'ARROW_TOLERANCE',
    'ARROW_UP_PROBE',
    'CHALLENGE_COLOR',
    'CHALLENGE_PROBES',
    'CHALLENGE_TOLERANCE',
    'CLICK_RIVAL_INFO',
    'CLICK_START_BATTLE',
    'SWIPE_DELAY',
    'SWIPE_TO_BOTTOM',
    'SWIPE_TO_TOP',
]
