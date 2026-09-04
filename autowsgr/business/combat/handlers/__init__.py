"""战斗业务处理器组合入口。"""

from autowsgr.application.combat.engine.phase_handlers import CombatPhaseHandlersMixin
from autowsgr.business.combat.handlers.decision import CombatDecisionMixin
from autowsgr.business.combat.handlers.settlement import CombatSettlementMixin


class PhaseHandlersMixin(
    CombatDecisionMixin,
    CombatSettlementMixin,
    CombatPhaseHandlersMixin,
):
    """组合业务决策、业务结算和通用阶段处理。"""


__all__ = [
    'CombatDecisionMixin',
    'CombatSettlementMixin',
    'PhaseHandlersMixin',
]
