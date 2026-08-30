"""战斗领域基建的公开入口。

业务执行器只依赖本模块导出的计划、引擎和结果；动作、识别器、处理器与
记录器属于战斗基建内部实现，不作为跨业务调用入口。
"""

from autowsgr.infra.combat.engine import (
    CombatEngine,
    CombatMode,
    CombatPhase,
    CombatPlan,
    GradeCondition,
    NodeDecision,
    run_combat,
)
from autowsgr.infra.combat.history import (
    CombatEvent,
    CombatHistory,
    CombatResult,
    FightResult,
    grade_condition_met,
)
from autowsgr.infra.combat.node_tracker import MapNodeData, NodeTracker
from autowsgr.infra.combat.recognition import (
    SHIP_DROP_PAGE_SIGNATURE,
    ShipDropResult,
    recognize_enemy_formation,
    recognize_ship_drop,
)
from autowsgr.infra.combat.rules import RuleEngine, RuleResult
from autowsgr.infra.fleet import (
    ALLOWED_SHIP_TYPE_CODES,
    FleetPreset,
    FleetSelectionSource,
    FleetSlotRule,
    ResolvedFleetSelection,
    ShipSelector,
    exact_fleet_rules,
    fleet_slot_from_api,
    resolve_fleet_selection,
)


__all__ = [
    'ALLOWED_SHIP_TYPE_CODES',
    'SHIP_DROP_PAGE_SIGNATURE',
    'CombatEngine',
    'CombatEvent',
    'CombatHistory',
    'CombatMode',
    'CombatPhase',
    'CombatPlan',
    'CombatResult',
    'FightResult',
    'FleetPreset',
    'FleetSelectionSource',
    'FleetSlotRule',
    'GradeCondition',
    'MapNodeData',
    'NodeDecision',
    'NodeTracker',
    'ResolvedFleetSelection',
    'RuleEngine',
    'RuleResult',
    'ShipDropResult',
    'ShipSelector',
    'exact_fleet_rules',
    'fleet_slot_from_api',
    'grade_condition_met',
    'recognize_enemy_formation',
    'recognize_ship_drop',
    'resolve_fleet_selection',
    'run_combat',
]
