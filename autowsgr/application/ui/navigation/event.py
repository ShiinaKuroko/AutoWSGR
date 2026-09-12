"""模块功能：执行母港主页到活动地图的专用导航边动作。

上层调用：
- application.ui.navigation.graph.common：执行 HOME -> EVENT_MAP 导航边。
- application.ui.controller.home.main_page.page：复用活动入口的页面便捷导航。

下层依赖：
- application.ui.controller.home.main_page.constants：提供活动入口坐标。
- application.ui.controller.home.event_page：提供活动页面检查器。
- application.ui.controller.home.main_page.overlay：清除导航过程中的浮层。
- common.ui.interaction：提供活动页面导航异常类型。
- common.vision：匹配活动入口图标和主页模板。

活动入口需要图标等待、预约浮层处理和失败重试，不能退化为普通固定坐标边；
本模块只实现该导航边，不承载活动页面内部操作。
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home.event_page import BaseEventPage
from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.application.ui.controller.home.main_page.overlay import (
    dismiss_overlay,
    read_overlay,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ImageChecker
from autowsgr.common.vision.resources import Templates
from autowsgr.common.vision.resources.pages.event import event_icon_templates


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.common.device import AndroidController
    from autowsgr.common.vision import ImageTemplate


_log = get_logger('ui')


# ── 公开导航入口 ─────────────────────────────────────────────────────────────


def navigate_to_event(ctx: GameContext, *, max_retries: int = 3) -> None:
    """从母港主页进入活动地图，并在失败时重试。"""
    from autowsgr.common.ui.interaction import NavigationError

    ctrl = ctx.ctrl
    for attempt in range(1, max_retries + 1):
        _log.debug('[UI] 活动导航: 尝试 {}/{}', attempt, max_retries)
        if _try_navigate_to_event(ctrl):
            return
        time.sleep(1.0)

    raise NavigationError(
        f'活动导航失败: {max_retries} 次尝试后仍未进入活动地图页面',
        screen=ctrl.screenshot(),
    )


# ── 单次导航尝试 ─────────────────────────────────────────────────────────────


def _try_navigate_to_event(
    ctrl: AndroidController,
    *,
    icon_wait: float = 3.0,
    nav_wait: float = 5.0,
) -> bool:
    """执行一次活动入口点击和到达检查。"""
    screen = ctrl.screenshot()
    overlay = read_overlay(screen)
    if overlay is not None:
        _log.debug('[UI] 活动导航: 先消除浮层 {}', overlay.value)
        dismiss_overlay(ctrl, overlay)
        time.sleep(0.5)
        screen = ctrl.screenshot()

    if not ImageChecker.template_exists(screen, Templates.MainPage.MAIN, confidence=0.85):
        _log.warning('[UI] 活动导航: 当前不在主页面基础态')
        return False

    templates = _get_event_icon_templates()
    deadline = time.time() + icon_wait
    detail = None
    while time.time() < deadline:
        screen = ctrl.screenshot()
        detail = ImageChecker.find_any(screen, templates, confidence=0.8)
        if detail is not None:
            break
        time.sleep(0.3)

    if detail is None:
        _log.warning('[UI] 活动导航: 等待 {:.1f}s 后仍未检测到活动图标', icon_wait)
        return False

    coord = constants.NAV_POSITIONS['event']
    _log.debug('[UI] 主页面 → 活动')
    ctrl.click(*coord)
    time.sleep(1.0)

    deadline = time.time() + nav_wait
    while time.time() < deadline:
        screen = ctrl.screenshot()
        if BaseEventPage.check_current_page(screen):
            _log.info('[UI] 已到达活动地图页面')
            return True
        overlay = read_overlay(screen)
        if overlay is not None:
            _log.debug('[UI] 活动导航: 点击后出现浮层 {}, 消除', overlay.value)
            dismiss_overlay(ctrl, overlay)
        time.sleep(0.5)

    _log.warning('[UI] 活动导航: 点击后 {:.1f}s 内未到达活动页面', nav_wait)
    return False


# ── 模板加载辅助 ─────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_event_icon_templates() -> list[ImageTemplate]:
    """延迟加载活动入口图标模板。"""
    return event_icon_templates()


__all__ = ['navigate_to_event']
