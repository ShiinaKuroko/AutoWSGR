"""业务实现 · 战斗领域 — 与战斗相关的业务定义。

当前成员:
    exercise/      演习链路 (统一 Runner 骨架的第一块试金石)

规划中 (按迁移顺序):
    campaign.py    战役链路 (选难度 → 选战役 → 准备 → 出征)
    normal.py      普通出征 + 活动战 (多节点地图)
    decisive/      决战 (独立子包: 专属页面体系 + 阶段状态机)
"""

from autowsgr.application.combat import CombatPhase
from autowsgr.business.combat.engine import CombatEngine, run_combat
from autowsgr.business.combat.history import (
    CombatEvent,
    CombatHistory,
    CombatResult,
    EventType,
    FightResult,
    grade_condition_met,
)
from autowsgr.business.combat.plan import CombatMode, CombatPlan, GradeCondition, NodeDecision
from autowsgr.business.combat.rules import RuleEngine, RuleResult


__all__ = [
    'CombatEngine',
    'CombatEvent',
    'CombatHistory',
    'CombatMode',
    'CombatPhase',
    'CombatPlan',
    'CombatResult',
    'EventType',
    'FightResult',
    'GradeCondition',
    'NodeDecision',
    'RuleEngine',
    'RuleResult',
    'grade_condition_met',
    'run_combat',
]
