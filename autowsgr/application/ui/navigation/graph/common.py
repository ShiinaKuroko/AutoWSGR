"""公共页面之间的导航边。"""

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


# ── 公共页面动作 ─────────────────────────────────────────────


def _main_to_backyard(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.HOME)


def _main_to_event(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.EVENT)


def _main_to_map(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.SORTIE)


def _main_to_mission(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.TASK)


def _main_to_sidebar(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.main_page import MainPage

    MainPage(ctx).navigate_to(MainPage.Target.SIDEBAR)


COMMON_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MAIN, PageName.MAP, _main_to_map, '主页面 → 地图'),
    NavEdge(PageName.MAIN, PageName.MISSION, _main_to_mission, '主页面 → 任务'),
    NavEdge(PageName.MAIN, PageName.BACKYARD, _main_to_backyard, '主页面 → 后院'),
    NavEdge(PageName.MAIN, PageName.SIDEBAR, _main_to_sidebar, '主页面 → 侧边栏'),
    NavEdge(PageName.MAIN, PageName.EVENT_MAP, _main_to_event, '主页面 → 活动'),
)


__all__ = ['COMMON_EDGES', 'NavEdge']
