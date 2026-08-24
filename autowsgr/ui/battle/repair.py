"""兼容 shim — 修理策略实现已迁移至 :mod:`autowsgr.business.logistics.repair.quick_repair`。

本模块保留 :class:`RepairMixin` 类壳 (维持 BattlePreparationPage 的
继承聚合结构与 ``page.apply_repair`` 调用习惯), 方法体薄委托到
business 层的函数实现 — 页面提供操作能力, 业务持有修理策略。
"""

from __future__ import annotations

from autowsgr.business.logistics.repair.quick_repair import (
    apply_quick_repair,
    check_repair,
    repair_slots,
)
from autowsgr.ui.battle.base import BaseBattlePreparation, RepairStrategy


class RepairMixin(BaseBattlePreparation):
    """修理操作 Mixin — 薄委托壳, 实现在 business/logistics/repair/quick_repair.py。"""

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
