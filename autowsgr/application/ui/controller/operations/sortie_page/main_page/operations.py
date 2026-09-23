"""模块功能：提供 sortie_page 页面壳的原子返回操作。

上层调用：
- application.ui.navigation.route_registry：执行出征页面返回主页的页面边。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page.constants：提供返回坐标。
- common.device.service：提供设备点击能力。

本模块只执行一次返回点击，不负责页面识别、等待、重试或业务流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


def click_return_home(ctrl: DeviceService) -> None:
    """点击出征页面返回主页的按钮。"""
    ctrl.click(*constants.CLICK_BACK)


__all__ = ['click_return_home']
