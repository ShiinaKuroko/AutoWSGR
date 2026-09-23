"""模块功能：执行演习页面的原子点击和列表滑动操作。

上层调用：
- application.ui.controller.operations.sortie_page.exercise_page.page：编排演习页面流程。

下层依赖：
- application.ui.controller.operations.sortie_page.exercise_page.constants：提供页面坐标。
- common.device：提供设备控制器契约。

边界：
本模块只执行已确定坐标的页面设备操作，不读取页面事实、不做候选判断或编排业务流程。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.exercise_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


_SWIPE_SETTLE_DELAY = 0.8  # 列表滑动后的页面稳定等待时间（秒）。


# ── 演习列表 ─────────────────────────────────────────────────────────────────


def swipe_rival_list_to_top(ctrl: DeviceService) -> None:
    """将演习对手列表滑动到顶部并等待列表稳定。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.swipe(*constants.SWIPE_TO_TOP)
    time.sleep(_SWIPE_SETTLE_DELAY)


def swipe_rival_list_to_bottom(ctrl: DeviceService) -> None:
    """将演习对手列表滑动到底部并等待列表稳定。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.swipe(*constants.SWIPE_TO_BOTTOM)
    time.sleep(_SWIPE_SETTLE_DELAY)


def click_rival(ctrl: DeviceService, visible_slot: int) -> None:
    """点击当前可见槽位的演习对手挑战按钮。

    Args:
        ctrl: 当前设备控制器。
        visible_slot: 可见对手槽位，范围为 0-3。
    """
    ctrl.click(*constants.RIVAL_CHALLENGE_POSITIONS[visible_slot])


# ── 对手信息页 ──────────────────────────────────────────────────────────────


def click_rival_refresh(ctrl: DeviceService) -> None:
    """点击对手信息页的刷新按钮。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_RIVAL_REFRESH)


def click_start_battle(ctrl: DeviceService) -> None:
    """点击对手信息页的开始战斗按钮。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_START_BATTLE)
