"""后勤页面之间的导航边。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.common import NavEdge
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


# ── 后勤页面动作 ─────────────────────────────────────────────


def _backyard_to_bath(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.backyard_page import BackyardPage, BackyardTarget

    BackyardPage(ctx).navigate_to(BackyardTarget.BATH)


def _backyard_to_canteen(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.backyard_page import BackyardPage, BackyardTarget

    BackyardPage(ctx).navigate_to(BackyardTarget.CANTEEN)


def _backyard_to_main(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.backyard_page import BackyardPage

    BackyardPage(ctx).go_back()


def _bath_to_backyard(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.bath_page import BathPage

    BathPage(ctx).go_back()


def _build_to_sidebar(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.build_page import BuildPage

    BuildPage(ctx).go_back()


def _canteen_to_backyard(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.canteen_page import CanteenPage

    CanteenPage(ctx).go_back()


def _friend_to_sidebar(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.friend_page import FriendPage

    FriendPage(ctx).go_back()


def _intensify_to_sidebar(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.intensify_page import IntensifyPage

    IntensifyPage(ctx).go_back()


def _mission_to_main(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.mission_page import MissionPage

    MissionPage(ctx).go_back()


def _sidebar_to_build(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.BUILD)


def _sidebar_to_friend(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.FRIEND)


def _sidebar_to_intensify(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.INTENSIFY)


def _sidebar_to_main(ctx: GameContext) -> None:
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage

    SidebarPage(ctx).close()


LOGISTICS_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MISSION, PageName.MAIN, _mission_to_main, '任务 → 主页面'),
    NavEdge(PageName.BACKYARD, PageName.MAIN, _backyard_to_main, '后院 → 主页面'),
    NavEdge(PageName.SIDEBAR, PageName.MAIN, _sidebar_to_main, '侧边栏 → 主页面'),
    NavEdge(PageName.BACKYARD, PageName.BATH, _backyard_to_bath, '后院 → 浴室'),
    NavEdge(PageName.BACKYARD, PageName.CANTEEN, _backyard_to_canteen, '后院 → 食堂'),
    NavEdge(PageName.BATH, PageName.BACKYARD, _bath_to_backyard, '浴室 → 后院'),
    NavEdge(PageName.CANTEEN, PageName.BACKYARD, _canteen_to_backyard, '食堂 → 后院'),
    NavEdge(PageName.SIDEBAR, PageName.BUILD, _sidebar_to_build, '侧边栏 → 建造'),
    NavEdge(PageName.SIDEBAR, PageName.INTENSIFY, _sidebar_to_intensify, '侧边栏 → 强化'),
    NavEdge(PageName.SIDEBAR, PageName.FRIEND, _sidebar_to_friend, '侧边栏 → 好友'),
    NavEdge(PageName.BUILD, PageName.SIDEBAR, _build_to_sidebar, '建造 → 侧边栏'),
    NavEdge(PageName.INTENSIFY, PageName.SIDEBAR, _intensify_to_sidebar, '强化 → 侧边栏'),
    NavEdge(PageName.FRIEND, PageName.SIDEBAR, _friend_to_sidebar, '好友 → 侧边栏'),
)


__all__ = ['LOGISTICS_EDGES']
