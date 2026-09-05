"""定义任务、后院、侧边栏及后勤子页面之间的导航边。

`navigation.service.goto_page` 通过 `graph` 汇总这里的边；动作由对应页面控制器执行。
本文件依赖 `PageName`、公共 `NavEdge` 模型和后勤页面控制器，不处理后勤业务规则。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.common import NavEdge
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


# -- 后勤页面动作 ------------


def _backyard_to_bath(ctx: GameContext) -> None:
    """从后院进入浴室。"""
    from autowsgr.application.ui.pages.backyard_page import BackyardPage, BackyardTarget

    BackyardPage(ctx).navigate_to(BackyardTarget.BATH)


def _backyard_to_canteen(ctx: GameContext) -> None:
    """从后院进入食堂。"""
    from autowsgr.application.ui.pages.backyard_page import BackyardPage, BackyardTarget

    BackyardPage(ctx).navigate_to(BackyardTarget.CANTEEN)


def _backyard_to_main(ctx: GameContext) -> None:
    """从后院返回主页。"""
    from autowsgr.application.ui.pages.backyard_page import BackyardPage

    BackyardPage(ctx).go_back()


def _bath_to_backyard(ctx: GameContext) -> None:
    """从浴室返回后院。"""
    from autowsgr.application.ui.pages.bath_page import BathPage

    BathPage(ctx).go_back()


def _build_to_sidebar(ctx: GameContext) -> None:
    """从建造页返回侧边栏。"""
    from autowsgr.application.ui.pages.build_page import BuildPage

    BuildPage(ctx).go_back()


def _canteen_to_backyard(ctx: GameContext) -> None:
    """从食堂返回后院。"""
    from autowsgr.application.ui.pages.canteen_page import CanteenPage

    CanteenPage(ctx).go_back()


def _friend_to_sidebar(ctx: GameContext) -> None:
    """从好友页返回侧边栏。"""
    from autowsgr.application.ui.pages.friend_page import FriendPage

    FriendPage(ctx).go_back()


def _intensify_to_sidebar(ctx: GameContext) -> None:
    """从强化页返回侧边栏。"""
    from autowsgr.application.ui.pages.intensify_page import IntensifyPage

    IntensifyPage(ctx).go_back()


def _mission_to_main(ctx: GameContext) -> None:
    """从任务页返回主页。"""
    from autowsgr.application.ui.pages.mission_page import MissionPage

    MissionPage(ctx).go_back()


def _sidebar_to_build(ctx: GameContext) -> None:
    """从侧边栏进入建造页。"""
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.BUILD)


def _sidebar_to_friend(ctx: GameContext) -> None:
    """从侧边栏进入好友页。"""
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.FRIEND)


def _sidebar_to_intensify(ctx: GameContext) -> None:
    """从侧边栏进入强化页。"""
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage, SidebarTarget

    SidebarPage(ctx).navigate_to(SidebarTarget.INTENSIFY)


def _sidebar_to_main(ctx: GameContext) -> None:
    """关闭侧边栏并回到主页。"""
    from autowsgr.application.ui.pages.sidebar_page import SidebarPage

    SidebarPage(ctx).close()


# -- 后勤导航图 ------------

# 回调必须先定义，模块加载时才能绑定为可执行的页面动作。
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
