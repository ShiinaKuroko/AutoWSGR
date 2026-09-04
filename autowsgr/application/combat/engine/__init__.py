"""战斗驱动子系统：状态机、计划和阶段转移。"""

from autowsgr.application.combat.engine.engine import CombatEngine
from autowsgr.application.combat.engine.phase_handlers import CombatPhaseHandlersMixin
from autowsgr.application.combat.engine.state import (
    CombatPhase,
    ModeCategory,
    PhaseBranch,
    build_transitions,
    resolve_successors,
)


__all__ = [
    'CombatEngine',
    'CombatPhase',
    'CombatPhaseHandlersMixin',
    'ModeCategory',
    'PhaseBranch',
    'build_transitions',
    'resolve_successors',
]
