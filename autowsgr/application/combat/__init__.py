"""Reusable combat application capabilities.

Business runners choose the plan and interpret results; this package performs
the common combat loop and device/vision actions.
"""

from autowsgr.application.combat.engine import (
    CombatEngine,
    CombatMode,
    CombatPhase,
    CombatPlan,
    GradeCondition,
    NodeDecision,
    run_combat,
)
from autowsgr.application.combat.history import (
    CombatEvent,
    CombatHistory,
    CombatResult,
    FightResult,
    grade_condition_met,
)
from autowsgr.application.combat.node_tracker import MapNodeData, NodeTracker
from autowsgr.application.combat.recognition import (
    SHIP_DROP_PAGE_SIGNATURE,
    ShipDropResult,
    recognize_enemy_formation,
    recognize_ship_drop,
)
from autowsgr.application.combat.rules import RuleEngine, RuleResult
__all__ = [
    'SHIP_DROP_PAGE_SIGNATURE',
    'CombatEngine',
    'CombatEvent',
    'CombatHistory',
    'CombatMode',
    'CombatPhase',
    'CombatPlan',
    'CombatResult',
    'FightResult',
    'GradeCondition',
    'MapNodeData',
    'NodeDecision',
    'NodeTracker',
    'RuleEngine',
    'RuleResult',
    'ShipDropResult',
    'grade_condition_met',
    'recognize_enemy_formation',
    'recognize_ship_drop',
    'run_combat',
]
