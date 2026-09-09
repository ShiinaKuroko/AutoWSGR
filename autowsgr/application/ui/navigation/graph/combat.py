"""维护战斗域页面之间的导航。

`autowsgr.application.ui.navigation.graph.__init__.py` 读取 `COMBAT_EDGES`，
`autowsgr.application.ui.navigation.service.py` 执行边动作。这里的动作调用
`autowsgr.application.ui.controller.operations.sortie_page.battle_page`、`battle_preparation`、`home.event_page` 和
`operations.sortie_page.decisive_page`，页面内的点击、等待和到达检查由页面控制器及 `autowsgr.common` 完成。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.common import NavEdge
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


# ── 战斗页面动作 ─────────────────────────────────────────────────


def _decisive_to_home(ctx: GameContext) -> None:
    """从决战页面返回主页，结束决战页面上下文。"""
    from autowsgr.application.ui.controller.operations.sortie_page.decisive_page import (
        DecisiveBattlePage,
    )

    DecisiveBattlePage(ctx).go_back()


def _event_to_home(ctx: GameContext) -> None:
    """从活动页面返回主页，结束活动页面上下文。"""
    from autowsgr.application.ui.controller.home.event_page.page import BaseEventPage

    BaseEventPage(ctx).go_back()


def _map_to_decisive(ctx: GameContext) -> None:
    """从地图切换到决战面板，并等待决战页面。"""
    from autowsgr.application.ui.controller.operations.sortie_page.battle_page import MapPage

    MapPage(ctx).enter_decisive()


def _map_to_home(ctx: GameContext) -> None:
    """从地图返回主页，结束当前出征入口。"""
    from autowsgr.application.ui.controller.operations.sortie_page.battle_page import MapPage

    MapPage(ctx).go_back()


# ── 战斗导航图 ─────────────────────────────────────────────────

# 边表描述战斗页面入口和回退关系，具体点击由上面的页面动作完成。
# BATTLE_PREP 的父页面依赖普通/决战/活动模式，由 service.py 的显式路线处理；
# 活动出征通过 goto_bath_from_event_sortie 返回 EVENT_MAP 后再进入主页和后院。
COMBAT_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MAP, PageName.HOME, _map_to_home, '地图 → 主页面'),
    NavEdge(PageName.MAP, PageName.DECISIVE_BATTLE, _map_to_decisive, '地图 → 决战'),
    NavEdge(PageName.DECISIVE_BATTLE, PageName.HOME, _decisive_to_home, '决战 → 主页面'),
    NavEdge(PageName.EVENT_MAP, PageName.HOME, _event_to_home, '活动 → 主页面'),
)


__all__ = ['COMBAT_EDGES']
