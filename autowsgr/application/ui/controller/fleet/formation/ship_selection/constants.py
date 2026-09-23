"""模块功能：维护编队选船节点的页面、船卡和滚动校准参数。

上层调用：
- ship_selection.page：执行船池页面 UI 原子动作。
- ship_selection.recognition：读取船卡和约束识别结果。
- ship_selection.workflow：控制选船重试和页面等待。

下层依赖：
- common.calibration.choose_ship：提供已有船池页面校准。
- main_page.constants：复用准备页返回坐标。
"""

from __future__ import annotations

from autowsgr.application.ui.controller.fleet.main_page.constants import CLICK_BACK
from autowsgr.application.vision.calibration import choose_ship


# ── 船池页面校准 ─────────────────────────────────────────────────────────────

CLICK_SEARCH_BOX = choose_ship.CLICK_SEARCH_BOX  # 船池搜索框点击点，用于开始输入舰船名称。
CLICK_DISMISS_KEYBOARD = choose_ship.CLICK_DISMISS_KEYBOARD  # 键盘关闭点击点，用于恢复船卡列表。
CLICK_REMOVE_SHIP = choose_ship.CLICK_REMOVE_SHIP  # 移除按钮点击点，用于清空准备页当前槽位。
PAGE_SIGNATURE = choose_ship.PAGE_SIGNATURE  # 船池页面签名，用于确认已进入选船页面。
INPUT_SIGNATURE = choose_ship.INPUT_SIGNATURE  # 搜索输入签名，用于确认软键盘已打开。


# ── 船卡扫描校准 ─────────────────────────────────────────────────────────────

SCROLL_X = choose_ship.SCROLL_X  # 船池列表滚动横坐标，用于保持滚动轨迹稳定。
SCROLL_FROM_Y = choose_ship.SCROLL_FROM_Y  # 船池列表滚动起点，用于向上翻查隐藏船卡。
SCROLL_TO_Y = choose_ship.SCROLL_TO_Y  # 船池列表滚动终点，用于向上翻查隐藏船卡。
SCROLL_DURATION = choose_ship.SCROLL_DURATION  # 船池列表滚动时长，用于控制列表滑动速度。


# ── 选船流程参数 ─────────────────────────────────────────────────────────────

CHOOSE_PAGE_TIMEOUT = 5.0  # 打开或退出船池页面的最长等待时间。
OCR_MAX_ATTEMPTS = 3  # 单条舰船规则的船卡识别最大轮次。
CARD_CLICK_WAIT = 1.0  # 船卡点击前等待列表稳定的时间。
LEVEL_RETRY_WAIT = 0.3  # 等级 OCR 噪声触发同屏重试前的等待时间。
SCROLL_WAIT = 0.5  # 船池列表滚动后等待新卡片渲染的时间。


__all__ = [
    'CARD_CLICK_WAIT',
    'CHOOSE_PAGE_TIMEOUT',
    'CLICK_BACK',
    'CLICK_DISMISS_KEYBOARD',
    'CLICK_REMOVE_SHIP',
    'CLICK_SEARCH_BOX',
    'INPUT_SIGNATURE',
    'LEVEL_RETRY_WAIT',
    'OCR_MAX_ATTEMPTS',
    'PAGE_SIGNATURE',
    'SCROLL_DURATION',
    'SCROLL_FROM_Y',
    'SCROLL_TO_Y',
    'SCROLL_WAIT',
    'SCROLL_X',
]
