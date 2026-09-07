"""模块功能：负责强化页面检查、标签读取、标签选择和页面返回。

上层调用：
- application.ui.navigation.graph.logistics：执行强化页面返回侧边栏的页面边动作。
- application.ui.navigation.registry：注册强化页面检查器。
- testing.ui：执行强化页面导航和标签验证。

下层依赖：
- application.ui.controller.sidebar.intensify_page.constants：提供返回和标签点击坐标。
- application.ui.controller.sidebar.main_page：提供侧边栏页面检查器。
- application.ui.controller.shared.tabbed_page：识别标签页和生成标签检查器。
- common.ui.interaction：等待标签或侧边栏页面到达。
- common.types：提供页面名称。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.shared.tabbed_page import (
    TabbedPageType,
    check_tabbed_page,
    get_active_tab_index,
    make_tab_checker,
)
from autowsgr.application.ui.controller.sidebar.intensify_page import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import click_and_wait_for_page


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.common.vision import PageMatch


_log = get_logger('ui')

# ── 页面标签 ─────────────────────────────────────────────────────────────────


class IntensifyTab(enum.Enum):
    """强化页面中的标签。"""

    INTENSIFY = '强化'
    REMAKE = '改修'
    SKILL = '技能'


_TAB_ORDER: tuple[IntensifyTab, ...] = tuple(IntensifyTab)
_TAB_TO_INDEX: dict[IntensifyTab, int] = {tab: index for index, tab in enumerate(_TAB_ORDER)}
_TAB_COORDINATES: dict[IntensifyTab, tuple[float, float]] = {
    IntensifyTab.INTENSIFY: constants.CLICK_INTENSIFY_TAB,
    IntensifyTab.REMAKE: constants.CLICK_REMAKE_TAB,
    IntensifyTab.SKILL: constants.CLICK_SKILL_TAB,
}


class IntensifyPage:
    """强化页面内的 UI 操作控制器。"""

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl

    # ── 页面检查 ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """检查截图是否属于强化页面组。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            强化页面组匹配结果。
        """
        return check_tabbed_page(screen, TabbedPageType.INTENSIFY)

    @staticmethod
    def read_active_tab(screen: np.ndarray) -> IntensifyTab | None:
        """读取强化页面当前激活的标签。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            当前标签；无法识别或索引越界时返回 ``None``。
        """
        index = get_active_tab_index(screen)
        if index is None or index >= len(_TAB_ORDER):
            return None
        return _TAB_ORDER[index]

    # ── 标签选择 ──────────────────────────────────────────────────────────────

    def select_tab(self, tab: IntensifyTab) -> None:
        """切换到指定标签并确认目标标签到达。

        Args:
            tab: 目标标签。

        Raises:
            NavigationError: 点击后未在限定时间内到达目标标签。
        """
        current = self.read_active_tab(self._ctrl.screenshot())
        _log.info(
            '[UI] 强化页面: {} → {}',
            current.value if current else '未知',
            tab.value,
        )
        click_and_wait_for_page(
            self._ctrl,
            click_coord=_TAB_COORDINATES[tab],
            checker=make_tab_checker(TabbedPageType.INTENSIFY, _TAB_TO_INDEX[tab]),
            source=f'强化-{current.value if current else "?"}',
            target=f'强化-{tab.value}',
        )

    # ── 回退 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击返回按钮并确认回到侧边栏。

        Raises:
            NavigationError: 点击后未在限定时间内回到侧边栏。
        """
        from autowsgr.application.ui.controller.sidebar.main_page import SidebarPage

        _log.info('[UI] 强化页面 → 返回侧边栏')
        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=SidebarPage.check_current_page,
            source=PageName.INTENSIFY,
            target=PageName.SIDEBAR,
        )
