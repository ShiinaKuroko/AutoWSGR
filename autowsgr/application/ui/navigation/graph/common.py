"""维护从主页进入一级页面的公共导航。

`autowsgr.application.ui.navigation.graph.__init__.py` 读取 `COMMON_EDGES`，
`autowsgr.application.ui.navigation.service.py` 执行其中的动作。动作交给
`autowsgr.application.ui.pages.main_page`，点击和到达检查再由页面控制器调用
`autowsgr.common.ui.interaction.py` 等底层能力完成。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.application.ui.context import UIContext as GameContext


@dataclass(frozen=True)
class NavEdge:
    """导航图中的一条有向边。"""

    source: PageName
    target: PageName
    action: Callable[[GameContext], None] = field(repr=False)
    description: str = ''


# ── 公共页面动作 ─────────────────────────────────────────────────


def _main_to_backyard(ctx: GameContext) -> None:
    """点击主页的后院入口并等待后院页面。"""
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.HOME)


def _main_to_event(ctx: GameContext) -> None:
    """点击主页的活动入口并等待活动页面。"""
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.EVENT)


def _main_to_map(ctx: GameContext) -> None:
    """点击主页的出征入口并等待地图页面。"""
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.SORTIE)


def _main_to_mission(ctx: GameContext) -> None:
    """点击主页的任务入口并等待任务页面。"""
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.TASK)


def _main_to_sidebar(ctx: GameContext) -> None:
    """点击主页的侧边栏入口并等待侧边栏。"""
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.SIDEBAR)


# ── 公共导航图 ─────────────────────────────────────────────────

# 边表描述页面入口和回退关系，具体点击由上面的页面动作完成。
COMMON_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MAIN, PageName.MAP, _main_to_map, '主页面 → 地图'),
    NavEdge(PageName.MAIN, PageName.MISSION, _main_to_mission, '主页面 → 任务'),
    NavEdge(PageName.MAIN, PageName.BACKYARD, _main_to_backyard, '主页面 → 后院'),
    NavEdge(PageName.MAIN, PageName.SIDEBAR, _main_to_sidebar, '主页面 → 侧边栏'),
    NavEdge(PageName.MAIN, PageName.EVENT_MAP, _main_to_event, '主页面 → 活动'),
)


__all__ = ['COMMON_EDGES', 'NavEdge']
