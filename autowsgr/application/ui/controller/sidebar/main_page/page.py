"""模块功能：编排侧边栏到子页面或母港主页面的导航。

上层调用：
- application.ui.controller.home.main_page：从母港打开侧边栏并取得页面检查器。
- application.ui.navigation.graph.logistics：执行侧边栏与子页面之间的页面边动作。
- application.ui.navigation.registry：注册侧边栏页面检查器。
- testing.ui.sidebar_page：执行侧边栏导航验证。

下层依赖：
- application.ui.controller.sidebar.main_page.constants：提供侧边栏点击坐标。
- application.ui.controller.sidebar.main_page.operations：执行二级菜单原子点击。
- application.ui.controller.sidebar.main_page.recognition：识别侧边栏页面事实。
- common.device.interaction：等待子页面或母港页面到达。
- common.types：提供页面名称。

边界：
本模块只编排侧边栏页面导航，不负责子页面业务、跨任务调度或运行时上下文创建。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.sidebar.main_page import constants, operations, recognition
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import (
    DEFAULT_NAV_CONFIG,
    NavigationError,
    click_and_wait_for_page,
    wait_for_page,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.sidebar.main_page')


# ── 页面目标 ─────────────────────────────────────────────────────────────────


class SidebarTarget(enum.Enum):
    """侧边栏可导航的目标页面。"""

    BUILD = '建造'
    INTENSIFY = '强化'
    FRIEND = '好友'


_SUBMENU_TARGETS: frozenset[SidebarTarget] = frozenset(
    {SidebarTarget.BUILD, SidebarTarget.INTENSIFY}
)
_SUBMENU_DELAY_SECONDS = 1.25  # 侧边栏入口点击后等待二级菜单出现的时间。
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
    """侧边栏页面的导航控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面导航 ──────────────────────────────────────────────────────────────

    def navigate_to(self, target: SidebarTarget) -> None:
        """点击侧边栏入口并进入指定页面。

        Args:
            target: 目标页面；建造和强化需要额外点击二级菜单，好友直接进入。

        Raises:
            NavigationError: 点击后未在限定重试次数内到达目标页面。
            TypeError: 目标不是 ``SidebarTarget``。
        """
        if not isinstance(target, SidebarTarget):
            _log.error(
                '[UI] 侧边栏 → 拒绝：期望类型=SidebarTarget，实际类型={!r}，'
                '结果=拒绝，下一步=抛出异常',
                type(target).__name__,
            )
            raise TypeError(f'侧边栏目标必须为 SidebarTarget，收到: {target!r}')

        # 子页面返回导航会反向引用 SidebarPage，局部导入避免页面包初始化循环。
        from autowsgr.application.ui.controller.sidebar.build_page import BuildPage
        from autowsgr.application.ui.controller.sidebar.friend_page import FriendPage
        from autowsgr.application.ui.controller.sidebar.intensify_page import IntensifyPage

        target_checker = {
            SidebarTarget.BUILD: BuildPage.check_current_page,
            SidebarTarget.INTENSIFY: IntensifyPage.check_current_page,
            SidebarTarget.FRIEND: FriendPage.check_current_page,
        }
        _log.info('[UI] 侧边栏 → 开始进入：目标={}', target.value)
        try:
            if target in _SUBMENU_TARGETS:
                # 二级菜单需要先等待菜单出现，再选择目标页面并确认终态。
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
        except NavigationError as exc:
            _log.opt(exception=True).error(
                '[UI] 侧边栏 → 失败：动作=进入页面，目标={!r}，'
                '错误类型={!r}，错误={!r}，结果=失败，下一步=抛出异常',
                target.value,
                type(exc).__name__,
                str(exc),
            )
            raise
        _log.info('[UI] 侧边栏 → 进入：目标={}，结果=成功', target.value)

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """检查截图是否属于侧边栏页面。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            侧边栏页面匹配结果。
        """
        return recognition.recognize_sidebar_page(screen)

    # ── 页面返回 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮并确认回到母港主页面。

        Raises:
            NavigationError: 点击后未在限定时间内回到母港主页面。
        """
        # 母港主页面会反向引用侧边栏，局部导入避免页面包初始化循环。
        from autowsgr.application.ui.controller.home.main_page import HomePage

        _log.info('[UI] 侧边栏 → 开始返回：目标={}', PageName.HOME.value)
        try:
            click_and_wait_for_page(
                self._ctrl,
                click_coord=constants.CLICK_CLOSE,
                checker=HomePage.check_current_page,
                source=PageName.SIDEBAR,
                target=PageName.HOME,
            )
        except NavigationError as exc:
            _log.opt(exception=True).error(
                '[UI] 侧边栏 → 失败：动作=返回主页，目标={!r}，'
                '错误类型={!r}，错误={!r}，结果=失败，下一步=抛出异常',
                PageName.HOME.value,
                type(exc).__name__,
                str(exc),
            )
            raise
        _log.info(
            '[UI] 侧边栏 → 返回：目标={}，结果=成功',
            PageName.HOME.value,
        )

    # ── 二级菜单导航 ──────────────────────────────────────────────────────────

    def _navigate_with_submenu(
        self,
        target: SidebarTarget,
        checker: Callable[[numpy.ndarray], bool],
    ) -> None:
        """通过二级菜单进入目标页面并确认终态。

        Args:
            target: 需要二级菜单的侧边栏目标。
            checker: 目标页面检查器。

        Raises:
            NavigationError: 有限重试后仍未到达目标页面。
        """
        config = DEFAULT_NAV_CONFIG
        last_err: NavigationError | None = None

        for attempt in range(1, config.max_retries + 1):
            if attempt > 1:
                time.sleep(config.retry_delay)

            # 1. 打开二级菜单，避免目标选项尚未渲染就点击。
            operations.click_sidebar_entry(self._ctrl, _NAV_COORDINATES[target])
            time.sleep(_SUBMENU_DELAY_SECONDS)

            # 2. 选择目标页面并确认页面终态。
            operations.click_submenu_entry(self._ctrl, _SUBMENU_COORDINATES[target])

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
                if attempt < config.max_retries:
                    _log.warning(
                        '[UI] 侧边栏 → 重试：目标={!r}，尝试次数={}，最大尝试次数={}，'
                        '原因=未到达目标页面，错误={!r}，下一步=重试',
                        target.value,
                        attempt,
                        config.max_retries,
                        str(exc),
                    )
            else:
                return

        raise NavigationError(
            f'导航失败 (已重试 {config.max_retries} 次): 侧边栏 → {target.value}',
            screen=self._ctrl.screenshot(),
        ) from last_err
