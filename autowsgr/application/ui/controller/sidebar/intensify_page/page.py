"""模块功能：提供强化页面检查和返回侧边栏的导航能力。

上层调用：
- application.ui.navigation.graph.logistics：执行强化页面返回侧边栏的页面边动作。
- application.ui.navigation.registry：注册强化页面检查器。

下层依赖：
- application.ui.controller.sidebar.intensify_page.constants：提供返回坐标。
- application.ui.controller.sidebar.main_page：提供侧边栏页面检查器。
- application.ui.controller.operations.sortie_page.main_page：提供强化页面组检查。
- common.device.interaction：等待侧边栏页面到达。
- common.types：提供页面名称。

边界：
强化业务仍处于 TODO 阶段；本模块只提供页面检查和返回导航，不提供强化业务流程。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    TabbedPageType,
    check_tabbed_page,
)
from autowsgr.application.ui.controller.sidebar.intensify_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.interaction import NavigationError, click_and_wait_for_page


if TYPE_CHECKING:
    import numpy

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.navigation.types import PageMatch


_log = get_logger('ui.sidebar.intensify_page')


class IntensifyTab(enum.Enum):
    """改造页面标签组。"""

    INTENSIFY = '强化'
    REMOLD = '改造'
    SKILL = '技能'


class IntensifyPage:
    """强化页面的导航控制器。"""

    def __init__(self, ctx: UIContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: numpy.ndarray) -> PageMatch:
        """检查截图是否属于强化页面组。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            强化页面组匹配结果。
        """
        return check_tabbed_page(screen, TabbedPageType.INTENSIFY)

    # TODO(intensify_page): 确认强化业务契约后，再补充强化业务流程入口与测试。

    # ── 标签切换 ──────────────────────────────────────────────────────────

    def go_to_tab(self, tab: IntensifyTab) -> None:
        """点击顶部标签，切到对应内容。

        只负责点击；是否真的切过去了由导航器用标签的 checker 确认。

        Args:
            tab: 目标标签。

        Raises:
            ValueError: 标签没有配置落点。
        """
        position = constants.TAB_POSITIONS.get(tab.name.lower())
        if position is None:
            raise ValueError(f'改造页没有该标签的落点: {tab!r}')
        _log.info('[UI] 改造页面 → 切换标签：tab={!r}，position={!r}', tab.value, position)
        self._ctrl.click(*position)

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮并确认回到侧边栏。

        Raises:
            NavigationError: 点击后未在限定时间内回到侧边栏。
        """
        # 侧边栏页面会反向加载强化页面检查器，延迟导入避免循环初始化。
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        _log.info(
            '[UI] 强化页面 → 开始返回：目标={}',
            PageName.SIDEBAR.value,
        )
        try:
            click_and_wait_for_page(
                self._ctrl,
                click_coord=constants.CLICK_BACK,
                checker=SidebarPage.check_current_page,
                source=PageName.INTENSIFY,
                target=PageName.SIDEBAR,
            )
        except NavigationError as exc:
            _log.opt(exception=True).error(
                '[UI] 强化页面 → 失败：动作=返回侧边栏，目标={!r}，'
                '错误类型={!r}，错误={!r}，结果=失败，下一步=抛出异常',
                PageName.SIDEBAR.value,
                type(exc).__name__,
                str(exc),
            )
            raise
        _log.info(
            '[UI] 强化页面 → 返回：目标={}，结果=成功',
            PageName.SIDEBAR.value,
        )
