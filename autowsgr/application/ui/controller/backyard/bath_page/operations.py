"""模块功能：执行浴室页面的基础设备操作，并轮询浮层直接终态。

上层调用：
- application.ui.controller.backyard.bath_page.page：执行页面返回、浮层和修理流程的页面操作。

下层依赖：
- application.ui.controller.backyard.bath_page.constants：提供页面点击、滑动和等待校准参数。
- common.device：提供设备控制器契约。

边界：
本模块只执行显式传入控制器的页面基础操作，不决定修理业务流程或跨页面导航。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.bath_page import constants


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.common.device.service import DeviceService


_OVERLAY_CHECK_INTERVAL = 0.5  # 浮层终态轮询间隔（秒）。
_SWIPE_DURATION = 0.5  # 单次列表滑动持续时间（秒）。
_SWIPE_DELAY = 1.0  # 滑动后等待页面稳定的时间（秒）。


# ── 页面级返回 ──────────────────────────────────────────────────────────────


def click_back(ctrl: DeviceService) -> None:
    """点击浴室页面返回按钮。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_BACK)


# ── 选择修理浮层 ────────────────────────────────────────────────────────────


def click_choose_repair(ctrl: DeviceService) -> None:
    """点击浴室页面的选择修理入口。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_CHOOSE_REPAIR)


def click_close_overlay(ctrl: DeviceService) -> None:
    """点击选择修理浮层的关闭按钮。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_CLOSE_OVERLAY)


# ── 修理列表 ────────────────────────────────────────────────────────────────


def click_repair_card(ctrl: DeviceService, position: tuple[float, float]) -> None:
    """点击识别到的修理卡片位置。

    Args:
        ctrl: 当前设备控制器。
        position: 舰船卡片中心的归一化相对坐标。
    """
    ctrl.click(*position)


def click_repair_all(ctrl: DeviceService) -> None:
    """点击选择修理浮层的全部修理按钮。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.click(*constants.CLICK_REPAIR_ALL)


def swipe_repair_list(ctrl: DeviceService) -> None:
    """向左滑动选择修理列表，并等待列表稳定。

    Args:
        ctrl: 当前设备控制器。
    """
    ctrl.swipe(
        *constants.SWIPE_START,
        *constants.SWIPE_END,
        duration=_SWIPE_DURATION,
    )
    time.sleep(_SWIPE_DELAY)


# ── 浮层终态确认 ────────────────────────────────────────────────────────────


def wait_overlay_closed(
    ctrl: DeviceService,
    *,
    checker: Callable[[np.ndarray], bool],
    overlay_checker: Callable[[np.ndarray], bool],
    timeout: float,
) -> bool:
    """等待当前页面确认且选择修理浮层关闭。

    Args:
        ctrl: 当前设备控制器。
        checker: 判断截图是否仍属于当前页面的检查器。
        overlay_checker: 判断选择修理浮层是否仍打开的检查器。
        timeout: 等待终态的最长时间（秒）。

    Returns:
        在超时前确认页面和浮层状态时返回 True，否则返回 False。
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        screen = ctrl.screenshot()
        if checker(screen) and not overlay_checker(screen):
            return True
        time.sleep(_OVERLAY_CHECK_INTERVAL)
    return False
