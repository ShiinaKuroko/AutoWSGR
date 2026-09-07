"""模块功能：执行母港主页到活动地图的专用导航流程。

上层调用：
- application.ui.controller.home.page：委托活动目标的页面导航。

下层依赖：
- application.ui.controller.home.constants：提供活动入口坐标。
- application.ui.controller.home.overlays：清除导航过程中的浮层。
- common.vision.resources.pages.event：提供活动入口图标模板。
- common.ui.interaction：提供活动页面导航异常类型。
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home import constants
from autowsgr.application.ui.controller.home.overlays import (
    dismiss_overlay,
    read_overlay,
)
from autowsgr.application.ui.controller.home.page import Target, _get_target_checker
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import ImageChecker
from autowsgr.common.vision.resources import Templates
from autowsgr.common.vision.resources.pages.event import event_icon_templates


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.common.device import AndroidController
    from autowsgr.common.vision import ImageTemplate

_log = get_logger('ui')

# ── 活动图标模板 (延迟加载) ──────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_event_icon_templates() -> list[ImageTemplate]:
    """延迟加载活动入口图标模板。

    每个活动主页面的入口图标外观不同, 这里收集各活动期的图标模板,
    匹配引擎按 ``source_resolution`` 自动缩放以适配当前截图分辨率,
    故 540p/720p 采集的模板可共存。导航时 ``find_any`` 命中任一即视为
    检测到活动入口。
    """
    return event_icon_templates()


# ── 内部: 单次导航尝试 ──────────────────────────────────────────────────


def _try_navigate_to_event(
    ctrl: AndroidController,
    event_checker: Callable[[np.ndarray], bool],
    *,
    icon_wait: float = 3.0,
    nav_wait: float = 5.0,
) -> bool:
    """执行一次活动导航尝试。

    流程:
        1. 确保无浮层覆盖
        2. 等待活动图标模板出现 (图像模板匹配)
        3. 点击图标并等待活动页面签名

    Args:
        ctrl: 当前游戏设备控制器。
        event_checker: 活动页面到达检查器。
        icon_wait: 等待活动入口图标的最长时间 (秒)。
        nav_wait: 点击入口后等待活动页面的最长时间 (秒)。

    Returns:
        成功到达活动页面时返回 True；本次尝试失败时返回 False。
    """

    # ① 清除浮层
    screen = ctrl.screenshot()
    overlay = read_overlay(screen)
    if overlay is not None:
        _log.debug('[UI] 活动导航: 先消除浮层 {}', overlay.value)
        dismiss_overlay(ctrl, overlay)
        time.sleep(0.5)
        screen = ctrl.screenshot()

    # 确认仍在主页面
    if not ImageChecker.template_exists(screen, Templates.MainPage.MAIN, confidence=0.85):
        _log.warning('[UI] 活动导航: 当前不在主页面基础态')
        return False

    # ② 等待活动图标模板出现
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

    # ③ 点击活动图标并等待活动页面
    coord = constants.NAV_POSITIONS['event']
    _log.debug('[UI] 主页面 → 活动')
    ctrl.click(*coord)
    time.sleep(1.0)

    deadline = time.time() + nav_wait
    while time.time() < deadline:
        screen = ctrl.screenshot()
        if event_checker(screen):
            _log.info('[UI] 已到达活动地图页面')
            return True
        # 点击后可能触发的浮层 (如预约页) 由 overlay 机制统一处理
        overlay = read_overlay(screen)
        if overlay is not None:
            _log.debug('[UI] 活动导航: 点击后出现浮层 {}, 消除', overlay.value)
            dismiss_overlay(ctrl, overlay)
        time.sleep(0.5)

    _log.warning('[UI] 活动导航: 点击后 {:.1f}s 内未到达活动页面', nav_wait)
    return False


# ── 公开: 带重试的导航入口 ──────────────────────────────────────────────


def navigate_to_event(
    ctrl: AndroidController,
    *,
    is_base_page: type,  # HomePage class (保留兼容签名)  # noqa: ARG001
    max_retries: int = 3,
) -> None:
    """导航到活动地图 — 带自动重试。

    Args:
        ctrl: 当前游戏设备控制器。
        is_base_page: HomePage 类型参数，保留既有调用签名。
        max_retries: 活动入口导航的最大尝试次数。

    Raises:
        NavigationError: 超过最大重试次数仍未到达活动地图页面。
    """
    from autowsgr.common.ui.interaction import NavigationError

    event_checker = _get_target_checker(Target.EVENT)

    for attempt in range(1, max_retries + 1):
        _log.debug('[UI] 活动导航: 尝试 {}/{}', attempt, max_retries)
        if _try_navigate_to_event(ctrl, event_checker):
            return
        time.sleep(1.0)

    raise NavigationError(
        f'活动导航失败: {max_retries} 次尝试后仍未进入活动地图页面',
        screen=ctrl.screenshot(),
    )
