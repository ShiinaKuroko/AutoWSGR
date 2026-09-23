"""模块功能：提供主页浮层和导航入口的原子设备操作。

上层调用：
- application.ui.controller.home.main_page.page、workflow：执行主页流程动作。
- application.ui.navigation.route_registry：点击主页出征入口。

下层依赖：
- application.ui.controller.home.main_page.constants：提供主页点击坐标。
- common.device.service：提供设备点击能力。

本模块只执行已确定坐标的一次点击，不负责识别、等待、重试或页面流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.main_page import constants


if TYPE_CHECKING:
    from autowsgr.common.device.service import DeviceService


# -- 页面导航操作 -----------------------------------------------------------


def click_sortie_entry(ctrl: DeviceService) -> None:
    """点击主页出征入口。"""
    ctrl.click(*constants.NAV_POSITIONS['sortie'])


# -- 公告操作 ---------------------------------------------------------------


def click_news_checkbox(ctrl: DeviceService, center: tuple[float, float]) -> None:
    """点击已经识别出的公告勾选框。"""
    ctrl.click(*center)


def click_news_close(ctrl: DeviceService) -> None:
    """点击一次公告关闭按钮。"""
    ctrl.click(*constants.DISMISS_POSITIONS['news_close'])


# -- 每日奖励操作 -----------------------------------------------------------


def click_reward_claim(ctrl: DeviceService, center: tuple[float, float]) -> None:
    """点击已经识别出的每日奖励领取按钮。"""
    ctrl.click(*center)


def click_reward_confirmation(ctrl: DeviceService, center: tuple[float, float]) -> None:
    """点击已经识别出的奖励确认按钮。"""
    ctrl.click(*center)


__all__ = [
    'click_news_checkbox',
    'click_news_close',
    'click_reward_claim',
    'click_reward_confirmation',
    'click_sortie_entry',
]
