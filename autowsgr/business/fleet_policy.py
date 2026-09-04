"""编队策略查表 — 五模式编队规则 (用户梳理的游戏机制)。

规则表:
    普通出征/演习: 选队 1-4, 1 号位必须非空
    远征:          选队 5-8, 1 号位必须非空
    战役:          固定槽位逐框填船, 1 号位必须非空
    决战:          逐框填船, 1 号位必须非空

左对齐机制: 普通/活动/演习等通用换船流程在移除成员后按游戏规则维护槽位；
战役是固定物理槽位例外, 不左移、不拖拽。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FleetPolicy:
    """一个战斗模式的编队规则。"""

    select: bool = True
    """True=选队式 (点击队伍号); False=填船式 (逐框添加)。"""

    fleets: tuple[int, ...] = (1, 2, 3, 4)
    """选队式可用的队伍号。远征为 (5, 6, 7, 8)。"""

    require_slot1: bool = True
    """填船式: 1 号位是否必须非空。"""


# 模式 → 编队策略的权威查表
FLEET_POLICIES: dict[str, FleetPolicy] = {
    'normal': FleetPolicy(select=True, fleets=(1, 2, 3, 4)),
    'exercise': FleetPolicy(select=True, fleets=(1, 2, 3, 4)),
    'expedition': FleetPolicy(select=True, fleets=(5, 6, 7, 8)),
    'campaign': FleetPolicy(select=False, require_slot1=True),
    'decisive': FleetPolicy(select=False, require_slot1=True),
}
