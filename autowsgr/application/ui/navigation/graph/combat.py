"""维护战斗域页面之间的导航。

`autowsgr.application.ui.navigation.graph.__init__.py` 读取 `COMBAT_EDGES`，
`autowsgr.application.ui.navigation.service.py` 执行边动作。这里的动作调用
`autowsgr.application.ui.pages.map`、`battle_preparation`、`event.event_page` 和
`decisive`，页面内的点击、等待和到达检查由页面控制器及 `autowsgr.common` 完成。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.graph.common import NavEdge
from autowsgr.common.types import PageName


if TYPE_CHECKING:
    from autowsgr.application.ui.context import UIContext as GameContext


# ── 战斗页面动作 ─────────────────────────────────────────────────


def _battle_prep_to_map(ctx: GameContext) -> None:
    """从出征准备页返回地图，供暂停或取消时回到战斗入口。"""
    from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage

    BattlePreparationPage(ctx).go_back()


def _decisive_to_main(ctx: GameContext) -> None:
    """从决战页面返回主页，结束决战页面上下文。"""
    from autowsgr.application.ui.pages.decisive import DecisiveBattlePage

    DecisiveBattlePage(ctx).go_back()


def _event_to_main(ctx: GameContext) -> None:
    """从活动页面返回主页，结束活动页面上下文。"""
    from autowsgr.application.ui.pages.event.event_page import BaseEventPage

    BaseEventPage(ctx).go_back()


def _map_to_decisive(ctx: GameContext) -> None:
    """从地图切换到决战面板，并等待决战页面。"""
    from autowsgr.application.ui.pages.map import MapPage

    MapPage(ctx).enter_decisive()


def _map_to_main(ctx: GameContext) -> None:
    """从地图返回主页，结束当前出征入口。"""
    from autowsgr.application.ui.pages.map import MapPage

    MapPage(ctx).go_back()


# ── 战斗导航图 ─────────────────────────────────────────────────

# 边表描述战斗页面入口和回退关系，具体点击由上面的页面动作完成。
COMBAT_EDGES: tuple[NavEdge, ...] = (
    NavEdge(PageName.MAP, PageName.MAIN, _map_to_main, '地图 → 主页面'),
    NavEdge(PageName.BATTLE_PREP, PageName.MAP, _battle_prep_to_map, '出征准备 → 地图'),
    NavEdge(PageName.MAP, PageName.DECISIVE_BATTLE, _map_to_decisive, '地图 → 决战'),
    NavEdge(PageName.DECISIVE_BATTLE, PageName.MAIN, _decisive_to_main, '决战 → 主页面'),
    NavEdge(PageName.EVENT_MAP, PageName.MAIN, _event_to_main, '活动 → 主页面'),
)


__all__ = ['COMBAT_EDGES']
