"""执行任务页面的可复用设备原子操作。

上层调用：
- application.ui.controller.operations.mission_page.page：执行任务领取流程中的页面原子动作。

下层依赖：
- application.ui.controller.operations.mission_page.constants：提供页面动作坐标。
- common.device：提供游戏设备控制器。

边界：
只执行明确页面对象的点击、滑动和动作等待，不负责识别、流程分支或业务结果判断。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.mission_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


# ── 页面动作时序 ───────────────────────────────────────────────────────────────────

_PANEL_SWITCH_SETTLE_SECONDS: float = 0.5
"""任务面板切换后的列表稳定等待时间。"""

_TASK_LIST_SCROLL_DURATION_SECONDS: float = 0.75
"""任务列表滑动动画时长。"""

_TASK_LIST_SCROLL_SETTLE_SECONDS: float = 0.5
"""任务列表滑动后的内容稳定等待时间。"""


def select_panel(ctrl: DeviceService, panel: str) -> None:
    """点击任务页面的指定面板并等待列表稳定。

    Args:
        ctrl: 游戏设备控制器。
        panel: 面板配置键，例如 ``daily`` 或 ``weekly``。
    """
    ctrl.click(*constants.PANEL_POSITIONS[panel])
    time.sleep(_PANEL_SWITCH_SETTLE_SECONDS)


def scroll_task_list(ctrl: DeviceService) -> None:
    """向下滑动任务列表并等待滚动结果稳定。

    Args:
        ctrl: 游戏设备控制器。
    """
    ctrl.swipe(*constants.SCROLL, duration=_TASK_LIST_SCROLL_DURATION_SECONDS)
    time.sleep(_TASK_LIST_SCROLL_SETTLE_SECONDS)


def click_reward_button(ctrl: DeviceService, center: tuple[float, float]) -> None:
    """点击已识别的奖励按钮中心。

    Args:
        ctrl: 游戏设备控制器。
        center: 奖励按钮中心的相对坐标。
    """
    ctrl.click(*center)


def click_confirm_button(ctrl: DeviceService, center: tuple[float, float]) -> None:
    """点击已识别的确认按钮中心。

    Args:
        ctrl: 游戏设备控制器。
        center: 确认按钮中心的相对坐标。
    """
    ctrl.click(*center)


__all__ = [  # noqa: RUF022
    'select_panel',
    'scroll_task_list',
    'click_reward_button',
    'click_confirm_button',
]
