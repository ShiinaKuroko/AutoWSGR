"""模块功能：负责母港主页的页面检查、浮层处理和一级页面导航。

上层调用：
- application.ui.navigation：执行母港到地图、任务、后院、侧边栏和活动页面的导航。
- application.runtime：识别母港并处理每日浮层。
- business.logistics：读取任务和远征通知状态。
- testing.ui：执行母港页面的导航验证。

下层依赖：
- application.ui.controller.home.constants：提供母港页面专用校准。
- application.ui.controller.home.event_nav：执行活动入口的专用导航。
- application.ui.controller.home.overlays：检测和消除母港浮层。
- common.ui.interaction：等待目标页面到达。
- common.vision：执行模板和像素签名检查。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.home import constants
from autowsgr.application.ui.controller.home.overlays import (
    OverlayKind,
    dismiss_overlay,
    read_overlay,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.vision import ImageChecker, PageMatch, PixelChecker
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext

_log = get_logger('ui')


# ── 页面导航目标 ──────────────────────────────────────────────────────────────


class Target(enum.Enum):
    """母港主页可导航的目标页面。"""

    SORTIE = '出征'
    TASK = '任务'
    SIDEBAR = '侧边栏'
    BACKYARD = '后院'
    EVENT = '活动'

    @property
    def page_name(self) -> str:
        """返回导航图使用的目标页面名称。"""
        return _TARGET_PAGES[self]


_TARGET_PAGES: dict[Target, str] = {
    Target.SORTIE: PageName.MAP,
    Target.TASK: PageName.MISSION,
    Target.SIDEBAR: PageName.SIDEBAR,
    Target.BACKYARD: PageName.BACKYARD,
    Target.EVENT: PageName.EVENT_MAP,
}


# ── 目标页面检查器 ───────────────────────────────────────────────────────────


def _get_target_checker(target: Target) -> Callable[[np.ndarray], bool]:
    """延迟导入并返回目标页面的页面检查器。

    Args:
        target: 母港主页支持的导航目标。

    Returns:
        用于确认目标页面到达的检查器。

    Raises:
        ValueError: target 不属于已支持的页面目标。
    """
    if target is Target.SORTIE:
        from autowsgr.application.ui.controller.map import MapPage

        return MapPage.is_current_page
    if target is Target.TASK:
        from autowsgr.application.ui.controller.mission_page import MissionPage

        return MissionPage.is_current_page
    if target is Target.SIDEBAR:
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        return SidebarPage.check_current_page
    if target is Target.BACKYARD:
        from autowsgr.application.ui.controller.backyard.main_page import BackyardPage

        return BackyardPage.check_current_page
    if target is Target.EVENT:
        from autowsgr.application.ui.controller.event.event_page import BaseEventPage

        return BaseEventPage.is_current_page
    raise ValueError(f'未知的导航目标: {target}')


# ── 母港页面控制器 ───────────────────────────────────────────────────────────


class HomePage:
    """母港主页的 UI 操作控制器。

    集成页面识别、浮层处理与导航:

    - **页面识别** — :meth:`check_current_page` 同时检测基础页面与浮层
    - **浮层处理** — :meth:`read_overlay` / :meth:`dismiss_current_overlay`
    - **常规导航** — 走「点击 + 等待目标页面签名」流程
    - **活动导航** — 专用流程，处理侧边栏图标识别与预约页误入

    使用方式::

        page = HomePage(ctx)
        page.navigate_to(HomePage.Target.SORTIE)
    """

    Target = Target

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于母港主页或其覆盖浮层。

        参考 :class:`~autowsgr.application.ui.controller.event.event_page.BaseEventPage` 模式，
        将浮层 (新闻公告 / 每日签到 / 活动预约 / 提督信息) 也识别为主页面。
        基础模板用更高阈值 (0.95) 抑制动态背景误命中, 浮层模板 0.85。

        返回带置信度的 PageMatch 供候选集排序，保留旧式真值调用。

        Args:
            screen: RGB 截图，形状为 (H, W, 3)。

        Returns:
            母港主页匹配结果；基础页、已知浮层或像素签名命中时视为匹配。
        """
        page = Templates.MainPage
        name = PageName.HOME.value
        result = ImageChecker.find_template(screen, page.MAIN, confidence=0.95)
        if result is not None:
            return PageMatch(name=name, matched=True, score=result.confidence)
        overlay = ImageChecker.find_any(
            screen, [page.NEWS, page.SIGN, page.BOOKING, page.USER_INFO], confidence=0.85
        )
        if overlay is not None:
            return PageMatch(name=name, matched=True, score=overlay.confidence)
        # 像素签名兜底: 部分环境渲染差异会使模板得分略低于阈值 (实测远端 0.945 < 0.95),
        # 底部栏 4 锚点像素签名可补充识别 (非主页面实测 ratio=0, 无误报风险)
        pixel_result = PixelChecker.check_signature(screen, constants.PAGE_SIGNATURE)
        if pixel_result.matched:
            return PageMatch(name=name, matched=True, score=pixel_result.ratio)
        return PageMatch(name=name, matched=False, score=0.0)

    @staticmethod
    def check_base_page(screen: np.ndarray) -> bool:
        """检查截图是否为母港主页基础状态，不含浮层覆盖。

        Args:
            screen: RGB 截图，形状为 (H, W, 3)。

        Returns:
            截图命中母港基础模板时返回 True。
        """
        return ImageChecker.template_exists(screen, Templates.MainPage.MAIN, confidence=0.85)

    # ── 通知状态 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_expedition_ready(screen: np.ndarray) -> bool:
        """检查母港是否有远征奖励可收取。

        Args:
            screen: RGB 截图，形状为 (H, W, 3)。

        Returns:
            远征通知红点命中时返回 True。
        """
        return PixelChecker.get_pixel(
            screen,
            *constants.PROBE_POSITIONS['expedition_ready'],
        ).near(constants.NOTIFICATION_RED, constants.NOTIFICATION_RED_TOLERANCE)

    @staticmethod
    def check_task_ready(screen: np.ndarray) -> bool:
        """检查母港是否有任务奖励可领取。

        Args:
            screen: RGB 截图，形状为 (H, W, 3)。

        Returns:
            任务通知红点命中时返回 True。
        """
        return PixelChecker.get_pixel(
            screen,
            *constants.PROBE_POSITIONS['task_ready'],
        ).near(constants.NOTIFICATION_RED, constants.NOTIFICATION_RED_TOLERANCE)

    # ── 浮层读取 ───────────────────────────────────────────────────────────────

    @staticmethod
    def read_overlay(screen: np.ndarray) -> OverlayKind | None:
        """读取当前截图中的母港浮层类型；没有浮层时返回 None。

        Args:
            screen: RGB 截图，形状为 (H, W, 3)。

        Returns:
            当前浮层类型；没有已知浮层时返回 None。
        """
        return read_overlay(screen)

    # ── 浮层处理 ──────────────────────────────────────────────────────────

    def dismiss_current_overlay(self) -> bool:
        """检测并消除当前浮层。

        Returns:
            已知浮层被处理时返回 True；当前没有已知浮层时返回 False。
        """
        screen = self._ctrl.screenshot()
        overlay = read_overlay(screen)
        if overlay is None:
            return False
        dismiss_overlay(self._ctrl, overlay)
        return True

    # ── 导航入口 ──────────────────────────────────────────────────────────

    def navigate_to(self, target: Target) -> None:
        """导航到指定子页面。

        自动处理浮层后再执行导航。活动目标走专用流程。

        Args:
            target: 母港主页支持的导航目标。

        Raises:
            NavigationError: 超时未到达目标页面。
        """
        self._ensure_clean_page()
        if target is Target.EVENT:
            self._navigate_to_event()
        else:
            self._navigate_standard(target)

    def _ensure_clean_page(self, *, max_attempts: int = 3) -> None:
        """确保当前在干净的母港主页，不带已知浮层覆盖。

        Args:
            max_attempts: 最多连续消除浮层的次数。
        """
        for i in range(max_attempts):
            screen = self._ctrl.screenshot()
            overlay = read_overlay(screen)
            if overlay is None:
                return
            _log.info(
                '[UI] 主页面: 导航前消除浮层 {} ({}/{})',
                overlay.value,
                i + 1,
                max_attempts,
            )
            dismiss_overlay(self._ctrl, overlay)
            time.sleep(0.5)

    def _navigate_standard(self, target: Target) -> None:
        """执行通用单步导航，点击入口并等待目标页面。

        Args:
            target: 母港主页支持的非活动导航目标。
        """
        from autowsgr.common.ui.interaction import click_and_wait_for_page

        coord = constants.NAV_POSITIONS[target.name.lower()]
        _log.info('[UI] 主页面 → {}', target.value)
        click_and_wait_for_page(
            self._ctrl,
            click_coord=coord,
            checker=_get_target_checker(target),
            source=PageName.HOME,
            target=target.page_name,
        )

    # ── 活动导航 (委托 event_nav) ────────────────────────────────────────

    def _navigate_to_event(self, *, max_retries: int = 3) -> None:
        """导航到活动地图，处理活动图标和预约浮层。

        Args:
            max_retries: 活动入口导航的最大尝试次数。
        """
        from autowsgr.application.ui.controller.home.event_nav import navigate_to_event

        navigate_to_event(self._ctrl, is_base_page=HomePage, max_retries=max_retries)

    # ── 便捷方法 ──────────────────────────────────────────────────────────

    def go_to_sortie(self) -> None:
        """进入地图选择页面。"""
        self.navigate_to(Target.SORTIE)

    def go_to_task(self) -> None:
        """进入任务页面。"""
        self.navigate_to(Target.TASK)

    def go_to_sidebar(self) -> None:
        """打开侧边栏。"""
        self.navigate_to(Target.SIDEBAR)

    def go_to_backyard(self) -> None:
        """进入后院页面。"""
        self.navigate_to(Target.BACKYARD)

    def go_to_event(self) -> None:
        """进入活动页面。"""
        self.navigate_to(Target.EVENT)
