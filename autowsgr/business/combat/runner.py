"""业务战斗运行入口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.combat import CombatEngine as ApplicationCombatEngine
from autowsgr.application.combat.history import CombatHistory, CombatResult
from autowsgr.business.combat.handlers import PhaseHandlersMixin
from autowsgr.business.combat.plan import MODE_CATEGORIES, CombatPlan, NodeDecision


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.common.device import AndroidController
    from autowsgr.common.types import ShipDamageState
    from autowsgr.common.vision import OCREngine


class CombatRunner(PhaseHandlersMixin, ApplicationCombatEngine):
    """组合业务决策和 application 战斗驱动。"""

    def __init__(
        self,
        device: AndroidController,
        ocr: OCREngine | None = None,
        *,
        stop_requested: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__(
            device,
            ocr,
            stop_requested=stop_requested,
            history_factory=CombatHistory,
            result_factory=lambda history: CombatResult(history=history),
            mode_categories=MODE_CATEGORIES,
        )

    def _get_current_decision(self) -> NodeDecision:
        """返回当前节点的业务决策。"""
        return self._plan.get_node_decision(self._node)


def run_combat(
    device: AndroidController,
    plan: CombatPlan,
    *,
    ship_stats: list[ShipDamageState],
    ocr: OCREngine | None = None,
    stop_requested: Callable[[], bool] | None = None,
) -> CombatResult:
    """Execute one business combat run."""
    runner = CombatRunner(device, ocr, stop_requested=stop_requested)
    return runner.fight(plan, initial_ship_stats=ship_stats)
