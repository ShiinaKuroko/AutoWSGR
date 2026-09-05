"""定义地图、出征准备、活动和决战页面的战斗导航边。

`navigation.service.goto_page` 通过 `graph` 汇总这里的边；动作由对应页面控制器执行。
本文件依赖 `PageName`、公共 `NavEdge` 模型和战斗页面控制器，不处理业务任务状态。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.common import NavEdge
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


# -- 战斗页面动作 ------------


def _battle_prep_to_map(ctx: GameContext) -> None:
    """从出征准备页返回地图。"""
    from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage

    BattlePreparationPage(ctx).go_back()


def _decisive_to_main(ctx: GameContext) -> None:
    """从决战页面返回主页。"""
    from autowsgr.application.ui.pages.decisive import DecisiveBattlePage

    DecisiveBattlePage(ctx).go_back()


def _event_to_main(ctx: GameContext) -> None:
    """从活动页面返回主页。"""
    from autowsgr.application.ui.pages.event.event_page import BaseEventPage

    BaseEventPage(ctx).go_back()


def _map_to_decisive(ctx: GameContext) -> None:
    """从地图进入决战页面。"""
    from autowsgr.application.ui.pages.map import MapPage

    MapPage(ctx).enter_decisive()


def _map_to_main(ctx: GameContext) -> None:
    """从地图返回主页。"""
    from autowsgr.application.ui.pages.map import MapPage

    MapPage(ctx).go_back()


# -- 战斗导航图 ------------

# 回调必须先定义，模块加载时才能绑定为可执行的页面动作。
COMBAT_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MAP, PageName.MAIN, _map_to_main, '地图 → 主页面'),
    NavEdge(PageName.BATTLE_PREP, PageName.MAP, _battle_prep_to_map, '出征准备 → 地图'),
    NavEdge(PageName.MAP, PageName.DECISIVE_BATTLE, _map_to_decisive, '地图 → 决战'),
    NavEdge(PageName.DECISIVE_BATTLE, PageName.MAIN, _decisive_to_main, '决战 → 主页面'),
    NavEdge(PageName.EVENT_MAP, PageName.MAIN, _event_to_main, '活动 → 主页面'),
)


__all__ = ['COMBAT_EDGES']
