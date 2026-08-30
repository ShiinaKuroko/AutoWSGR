"""Compatibility exports for the migrated combat engine."""

import importlib
import sys

from autowsgr.application.combat.engine.state import CombatPhase
from autowsgr.business.combat.engine import CombatEngine, run_combat
from autowsgr.business.combat.plan import CombatMode, CombatPlan, GradeCondition, NodeDecision


__all__ = [
    'CombatEngine',
    'CombatMode',
    'CombatPhase',
    'CombatPlan',
    'GradeCondition',
    'NodeDecision',
    'run_combat',
]


sys.modules[f'{__name__}.engine'] = importlib.import_module('autowsgr.business.combat.engine')
sys.modules[f'{__name__}.plan'] = importlib.import_module('autowsgr.business.combat.plan')
sys.modules[f'{__name__}.state'] = importlib.import_module('autowsgr.application.combat.engine.state')
