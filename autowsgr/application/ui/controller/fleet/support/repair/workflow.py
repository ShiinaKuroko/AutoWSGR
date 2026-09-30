"""模块功能：编排损伤检查、快速维修、复查和手动维修中断。

上层调用：
- main_page.page：在准备页主流程中执行维修。
- business.combat：提供维修策略并处理手动维修异常。

下层依赖：
- main_page.page：提供快速维修面板选择。
- repair.recognition：读取损伤状态。
- repair.constants：提供维修等待和重试参数。
- application.errors：提供明确的维修失败异常。
"""

from __future__ import annotations

import enum
import time
from typing import TYPE_CHECKING

from autowsgr.application.errors import ActionFailedError, ManualRepairRequiredError
from autowsgr.application.ui.controller.fleet.main_page.constants import BLOOD_BAR_PROBE
from autowsgr.application.ui.controller.fleet.support.repair import constants, recognition
from autowsgr.business.logistics.types import ShipDamageState
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.controller.context import UIContext
    from autowsgr.application.ui.controller.fleet.main_page import BattlePreparationPage


_log = get_logger('ui.fleet.support.repair')


class RepairStrategy(enum.Enum):
    """准备页快速维修策略。"""

    MODERATE = 'moderate'
    SEVERE = 'severe'
    ALWAYS = 'always'
    NEVER = 'never'


def apply_repair(
    ctx: UIContext,
    page: BattlePreparationPage,
    strategy: RepairStrategy | None = None,
    *,
    repair_manually: bool | None = None,
    retry_count: int = constants.REPAIR_RETRY_COUNT,
) -> list[int]:
    """执行损伤检测、快速维修、复查和有限重试。"""
    if strategy is None:
        strategy = RepairStrategy.SEVERE
    if strategy is RepairStrategy.NEVER:
        return []

    manual_enabled = ctx.config.repair_manually if repair_manually is None else repair_manually
    repaired_positions: list[int] = []
    positions = check_repair(ctx, strategy)
    for attempt in range(retry_count):
        if not positions:
            return repaired_positions
        if manual_enabled:
            raise ManualRepairRequiredError(f'需要手动修理槽位: {positions}')

        repair_slots(ctx, page, positions)
        repaired_positions.extend(positions)
        positions = check_repair(ctx, strategy)
        if not positions:
            _log.info(
                '[QuickRepair] 修理位置: {} (策略: {})',
                repaired_positions,
                strategy.value,
            )
            return repaired_positions
        _log.info(
            '[QuickRepair] 有舰船修理失败: {}, 重试第 {} 次',
            positions,
            attempt + 1,
        )

    _log.error('[QuickRepair] 舰船修理异常(策略: {})', strategy.value)
    raise ActionFailedError('舰船修理异常')


def check_repair(
    ctx: UIContext,
    strategy: RepairStrategy,
) -> list[int]:
    """根据维修策略计算需要快速维修的物理槽位。"""
    damage = recognition.detect_ship_damage(ctx.ctrl.screenshot())
    positions: list[int] = []
    for slot, state in damage.items():
        if state in {ShipDamageState.NO_SHIP, ShipDamageState.NORMAL}:
            continue
        if (
            strategy in {RepairStrategy.ALWAYS, RepairStrategy.MODERATE}
            and state >= ShipDamageState.MODERATE
        ) or (strategy is RepairStrategy.SEVERE and state >= ShipDamageState.SEVERE):
            positions.append(slot)
    return positions


def open_quick_repair(page: BattlePreparationPage) -> None:
    """打开准备页快速维修面板。"""
    from autowsgr.application.ui.controller.fleet.main_page import Panel

    page.select_panel(Panel.QUICK_REPAIR)


def repair_slots(
    ctx: UIContext,
    page: BattlePreparationPage,
    positions: Sequence[int],
) -> None:
    """打开快速维修面板并点击指定物理槽位。"""
    if not positions:
        return
    open_quick_repair(page)
    time.sleep(constants.REPAIR_PANEL_WAIT)
    for position in positions:
        if position not in BLOOD_BAR_PROBE:
            _log.warning('[QuickRepair] 无效修理位置: {}', position)
            continue
        ctx.ctrl.click(*BLOOD_BAR_PROBE[position])
        time.sleep(constants.REPAIR_SLOT_WAIT)
        _log.info('[QuickRepair] 出征准备 -> 修理位置 {}', position)


__all__ = [
    'RepairStrategy',
    'apply_repair',
    'check_repair',
    'open_quick_repair',
    'repair_slots',
]
