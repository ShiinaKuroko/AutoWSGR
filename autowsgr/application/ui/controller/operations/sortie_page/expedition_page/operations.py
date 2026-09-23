"""模块功能：执行远征页面的原子点击操作。

上层调用：
- application.ui.controller.operations.sortie_page.expedition_page.page：调用槽位和结算点击。

下层依赖：
- application.ui.controller.operations.sortie_page.expedition_page.constants：提供点击坐标。
- common.device：提供设备控制器契约。

本模块只执行已确定坐标的页面点击，不负责页面识别、流程分支、等待或业务结果判断。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


def click_expedition_slot(
    ctrl: DeviceService,
    coordinate: tuple[float, float],
) -> None:
    """点击已识别的远征槽位。"""
    ctrl.click(*coordinate)


def click_expedition_skip(ctrl: DeviceService) -> None:
    """点击远征结算页面的跳过区域。"""
    ctrl.click(*constants.CLICK_SKIP)


__all__ = [  # noqa: RUF022 - exports follow the page action order
    'click_expedition_slot',
    'click_expedition_skip',
]
