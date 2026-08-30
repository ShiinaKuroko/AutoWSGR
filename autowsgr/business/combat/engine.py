"""Business-owned combat engine and result boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from autowsgr.application.combat import CombatEngine as ApplicationCombatEngine
from autowsgr.business.combat.handlers import PhaseHandlersMixin
from autowsgr.business.combat.history import CombatHistory, CombatResult
from autowsgr.business.combat.plan import MODE_CATEGORIES, CombatPlan


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.common.device import AndroidController
    from autowsgr.common.vision import OCREngine
    from autowsgr.types import ShipDamageState


class CombatEngine(PhaseHandlersMixin, ApplicationCombatEngine):
    """Run the generic application driver with business phase decisions."""

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

    def _get_current_decision(self) -> Any:
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
    engine = CombatEngine(device, ocr, stop_requested=stop_requested)
    return engine.fight(plan, initial_ship_stats=ship_stats)
