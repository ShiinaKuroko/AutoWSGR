"""Battle preparation repair actions."""

from __future__ import annotations

from autowsgr.application.ui.pages.battle_preparation.base import (
    BaseBattlePreparation,
    RepairStrategy,
)
from autowsgr.application.ui.pages.battle_preparation.repair_action import (
    apply_quick_repair,
    check_repair,
    repair_slots,
)


class RepairMixin(BaseBattlePreparation):
    """Expose repair actions through the preparation page."""

    def repair_slots(self, positions: list[int]) -> None:
        """切换到快速修理面板并修理指定位置的舰船。"""
        repair_slots(self, positions)

    def check_repair(self, strategy: RepairStrategy) -> list[int]:
        """根据策略执行快速修理检查（不实际修理）。"""
        return check_repair(self, strategy)

    def apply_repair(
        self,
        strategy: RepairStrategy | None = None,
        *,
        repair_manually: bool = False,
        retry_count: int = 3,
    ) -> list[int]:
        """根据策略执行快速修理。"""
        return apply_quick_repair(
            self,
            strategy,
            repair_manually=repair_manually,
            retry_count=retry_count,
        )
