"""模块功能：负责侧边栏页面检查、子页面导航和页面关闭。

上层调用：
- application.ui.controller.home：从母港打开侧边栏并取得页面检查器。
- application.ui.navigation.graph.logistics：执行侧边栏与子页面之间的页面边动作。
- application.ui.navigation.registry：注册侧边栏页面检查器。
- testing.ui：执行侧边栏导航验证。

下层依赖：
- application.ui.controller.sidebar.main_page.constants：提供侧边栏点击坐标和等待参数。
- common.ui.interaction：等待子页面或母港页面到达。
- common.vision：匹配侧边栏页面模板。
- common.types：提供页面名称和匹配结果类型。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.sidebar.main_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page, wait_for_page
from autowsgr.common.vision import ImageChecker, PageMatch
from autowsgr.common.vision.resources import Templates


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')

# ── 页面目标 ─────────────────────────────────────────────────────────────────


class SidebarTarget(enum.Enum):
    """侧边栏可导航的目标页面。"""

    BUILD = '建造'
    INTENSIFY = '强化'
    FRIEND = '好友'


_SUBMENU_TARGETS: frozenset[SidebarTarget] = frozenset(
    {SidebarTarget.BUILD, SidebarTarget.INTENSIFY}
)

_NAV_COORDINATES: dict[SidebarTarget, tuple[float, float]] = {
    SidebarTarget.BUILD: constants.CLICK_BUILD,
    SidebarTarget.INTENSIFY: constants.CLICK_INTENSIFY,
    SidebarTarget.FRIEND: constants.CLICK_FRIEND,
}
_SUBMENU_COORDINATES: dict[SidebarTarget, tuple[float, float]] = {
    SidebarTarget.BUILD: constants.CLICK_BUILD_SUBMENU,
    SidebarTarget.INTENSIFY: constants.CLICK_INTENSIFY_SUBMENU,
}


class SidebarPage:
    """侧边栏页面内的 UI 操作控制器。"""

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于侧边栏页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            侧边栏页面匹配结果。
        """
        result = ImageChecker.find_template(screen, Templates.Page.SIDEBAR, confidence=0.8)
        name = PageName.SIDEBAR.value
        if result is None:
            return PageMatch(name=name, matched=False, score=0.0)
        return PageMatch(name=name, matched=True, score=result.confidence)

    # ── 页面导航 ──────────────────────────────────────────────────────────────

    def navigate_to(self, target: SidebarTarget) -> None:
        """点击侧边栏入口并进入指定页面。

        Args:
            target: 目标页面；建造和强化需要额外点击二级菜单，好友直接进入。

        Raises:
            NavigationError: 点击后未在限定重试次数内到达目标页面。
        """
        from autowsgr.application.ui.controller.sidebar.build_page import BuildPage
        from autowsgr.application.ui.controller.sidebar.friend_page import FriendPage
        from autowsgr.application.ui.controller.sidebar.intensify_page import IntensifyPage

        target_checker = {
            SidebarTarget.BUILD: BuildPage.check_current_page,
            SidebarTarget.INTENSIFY: IntensifyPage.check_current_page,
            SidebarTarget.FRIEND: FriendPage.check_current_page,
        }
        _log.info('[UI] 侧边栏 → {}', target.value)

        if target in _SUBMENU_TARGETS:
            # 二级菜单：点击侧边栏入口、等待菜单出现、选择目标页面并确认到达。
            self._navigate_with_submenu(
                target,
                target_checker[target],
            )
        else:
            # 好友入口不弹出二级菜单，直接点击并确认到达。
            click_and_wait_for_page(
                self._ctrl,
                click_coord=_NAV_COORDINATES[target],
                checker=target_checker[target],
                source=PageName.SIDEBAR,
                target=target.value,
            )

    def go_to_build(self) -> None:
        """点击「建造」— 进入建造页面。"""
        self.navigate_to(SidebarTarget.BUILD)

    def go_to_intensify(self) -> None:
        """点击「强化」— 进入强化页面。"""
        self.navigate_to(SidebarTarget.INTENSIFY)

    def go_to_friend(self) -> None:
        """点击「好友」— 进入好友页面。"""
        self.navigate_to(SidebarTarget.FRIEND)

    # ── 页面关闭 ──────────────────────────────────────────────────────────────

    def close(self) -> None:
        """关闭侧边栏并确认回到母港主页面。

        Raises:
            NavigationError: 点击后未在限定时间内回到母港主页面。
        """
        from autowsgr.application.ui.controller.home import HomePage

        _log.info('[UI] 侧边栏 → 关闭 (返回主页面)')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_CLOSE,
            checker=HomePage.check_current_page,
            source=PageName.SIDEBAR,
            target=PageName.HOME,
        )

    # ── 二级菜单辅助 ──────────────────────────────────────────────────────────

    def _navigate_with_submenu(
        self,
        target: SidebarTarget,
        checker: Callable,
    ) -> None:
        """点击二级菜单并确认目标页面到达。

        Args:
            target: 需要二级菜单的侧边栏目标。
            checker: 目标页面检查器。

        Raises:
            NavigationError: 重试后仍未到达目标页面。
        """
        from autowsgr.common.ui.interaction import DEFAULT_NAV_CONFIG, NavigationError

        config = DEFAULT_NAV_CONFIG
        last_err: NavigationError | None = None

        for attempt in range(1, config.max_retries + 1):
            if attempt > 1:
                _log.warning(
                    '[UI] 二级菜单重试 {}/{}: 侧边栏 → {} (等 {:.1f}s)',
                    attempt,
                    config.max_retries,
                    target.value,
                    config.retry_delay,
                )
                time.sleep(config.retry_delay)

            # 点击侧边栏菜单项，等待二级菜单出现，再点击目标选项。
            self._ctrl.click(*_NAV_COORDINATES[target])
            time.sleep(constants.SUBMENU_DELAY)
            self._ctrl.click(*_SUBMENU_COORDINATES[target])

            try:
                wait_for_page(
                    self._ctrl,
                    checker,
                    timeout=config.timeout,
                    interval=config.interval,
                    handle_overlays=config.handle_overlays,
                    source=PageName.SIDEBAR,
                    target=target.value,
                )
            except NavigationError as exc:
                last_err = exc
                _log.warning(
                    '[UI] 二级菜单后超时 ({}/{}): 侧边栏 → {}',
                    attempt,
                    config.max_retries,
                    target.value,
                )
            else:
                return

        raise NavigationError(
            f'导航失败 (已重试 {config.max_retries} 次): 侧边栏 → {target.value}',
            screen=self._ctrl.screenshot(),
        ) from last_err
