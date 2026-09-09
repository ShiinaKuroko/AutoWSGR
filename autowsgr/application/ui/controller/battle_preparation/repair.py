"""模块功能：向出征准备页面公开快速修理操作入口。

上层调用：
- business.combat：按出征模式和配置触发准备页修理。
- application.ui.controller.battle_preparation.preparation：组合修理 Mixin。

下层依赖：
- application.ui.controller.battle_preparation.base：提供页面上下文和面板操作。
- application.ui.controller.battle_preparation.repair_action：执行修理策略和结果复查。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.battle_preparation.base import (
    BaseBattlePreparation,
    RepairStrategy,
)
from autowsgr.application.ui.controller.battle_preparation.repair_action import (
    apply_quick_repair,
    check_repair,
    repair_slots,
)


if TYPE_CHECKING:
    from collections.abc import Callable


class RepairMixin(BaseBattlePreparation):
    """Expose repair actions through the preparation page."""

    def check_repair(self, strategy: RepairStrategy) -> list[int]:
        """根据策略执行快速修理检查（不实际修理）。"""
        return check_repair(self, strategy)

    def repair_slots(self, positions: list[int]) -> None:
        """切换到快速修理面板并修理指定位置的舰船。"""
        repair_slots(self, positions)

    def apply_repair(
        self,
        strategy: RepairStrategy | None = None,
        *,
        repair_manually: bool | None = None,
        manual_repair_action: Callable[[list[int]], None] | None = None,
        retry_count: int = 3,
    ) -> list[int]:
        """根据策略执行快速修理，显式维修方式优先于全局配置。"""
        return apply_quick_repair(
            self,
            strategy,
            repair_manually=repair_manually,
            manual_repair_action=manual_repair_action,
            retry_count=retry_count,
        )
