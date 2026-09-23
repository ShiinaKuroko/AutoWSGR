"""模块功能：执行侧边栏二级菜单的原子点击。

上层调用：
- application.ui.controller.sidebar.main_page.page：编排二级菜单导航流程。

下层依赖：
- common.device：提供设备控制器契约。

边界：
本模块只执行显式传入坐标的单次点击，不决定目标页面、等待策略、重试分支或导航终态。
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


def click_sidebar_entry(
    ctrl: DeviceService,
    coordinate: tuple[float, float],
) -> None:
    """点击侧边栏的一级入口。

    Args:
        ctrl: 当前设备控制器。
        coordinate: 一级入口的归一化坐标。
    """
    ctrl.click(*coordinate)


def click_submenu_entry(
    ctrl: DeviceService,
    coordinate: tuple[float, float],
) -> None:
    """点击侧边栏的二级菜单入口。

    Args:
        ctrl: 当前设备控制器。
        coordinate: 二级菜单入口的归一化坐标。
    """
    ctrl.click(*coordinate)


__all__ = ['click_sidebar_entry', 'click_submenu_entry']
