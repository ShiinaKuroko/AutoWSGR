"""模块功能：执行食堂页面的原子点击操作。

上层调用：
- application.ui.controller.backyard.canteen_page.page：调用菜谱、弹窗和结果动画的页面点击。

下层依赖：
- application.ui.controller.backyard.canteen_page.constants：提供食堂页面的点击坐标。
- common.device：提供设备控制器契约。

本模块只执行已确定坐标的页面点击，不负责参数校验、流程分支、页面识别或业务结果判断。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.backyard.canteen_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


def click_recipe(ctrl: DeviceService, coordinate: tuple[float, float]) -> None:
    """点击指定菜谱坐标。"""
    ctrl.click(*coordinate)


def click_cook_button(ctrl: DeviceService, coordinate: tuple[float, float]) -> None:
    """点击识别到的做菜按钮坐标。"""
    ctrl.click(*coordinate)


def click_force_cook(ctrl: DeviceService) -> None:
    """点击覆盖当前生效料理的确认按钮。"""
    ctrl.click(*constants.CLICK_FORCE_COOK)


def click_cancel_cook(ctrl: DeviceService) -> None:
    """点击取消覆盖当前生效料理的按钮。"""
    ctrl.click(*constants.CLICK_CANCEL_COOK)


def click_dismiss_popup(ctrl: DeviceService) -> None:
    """点击关闭做菜提示弹窗。"""
    ctrl.click(*constants.CLICK_DISMISS_POPUP)


def click_skip_animation(ctrl: DeviceService) -> None:
    """点击结果动画区域。"""
    ctrl.click(*constants.CLICK_SKIP_ANIMATION)


__all__ = [  # noqa: RUF022 - exports follow the page action order
    'click_recipe',
    'click_cook_button',
    'click_force_cook',
    'click_cancel_cook',
    'click_dismiss_popup',
    'click_skip_animation',
]
