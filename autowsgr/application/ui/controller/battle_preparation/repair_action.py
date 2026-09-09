"""模块功能：执行出征准备页面的快速修理策略、点击和有限复查。

上层调用：
- application.ui.controller.battle_preparation.repair：公开修理 Mixin 的薄委托。
- business.combat：在普通、战役和决战出征前触发修理。

下层依赖：
- application.ui.controller.battle_preparation.base：提供面板和页面控制器能力。
- application.ui.controller.battle_preparation.constants：提供血条操作坐标。
- common.system：提供动作失败和手动修理终止异常。

本模块只编排准备页内的修理策略；页面操作由传入的 Controller 执行，跨页面澡堂
导航由调用方回调负责。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.battle_preparation.base import (
    BaseBattlePreparation,
    Panel,
    RepairStrategy,
)
from autowsgr.application.ui.controller.battle_preparation.constants import BLOOD_BAR_PROBE
from autowsgr.common.system import ActionFailedError, ManualRepairRequiredError
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import ShipDamageState


if TYPE_CHECKING:
    from collections.abc import Callable


_log = get_logger('business.logistics.repair')


def check_repair(page: BaseBattlePreparation, strategy: RepairStrategy) -> list[int]:
    """根据策略检查需要修理的槽位 (不实际修理)。

    Parameters
    ----------
    page:
        出征准备页控制器 (提供截图与血条探测能力)。
    strategy:
        修理策略。

    Returns
    -------
    list[int]
        需要修理的槽位列表。
    """
    screen = page._ctrl.screenshot()
    damage = page.detect_ship_damage(screen)

    positions: list[int] = []
    for slot, dmg in damage.items():
        if dmg in {ShipDamageState.NO_SHIP, ShipDamageState.NORMAL}:
            continue
        if (
            (strategy is RepairStrategy.ALWAYS and dmg >= ShipDamageState.MODERATE)
            or (strategy is RepairStrategy.MODERATE and dmg >= ShipDamageState.MODERATE)
            or (strategy is RepairStrategy.SEVERE and dmg >= ShipDamageState.SEVERE)
        ):
            positions.append(slot)
    return positions


def repair_slots(page: BaseBattlePreparation, positions: list[int]) -> None:
    """切换到快速修理面板并修理指定位置的舰船。

    Parameters
    ----------
    page:
        出征准备页控制器 (提供 ``_ctrl`` 与 ``select_panel`` 能力)。
    positions:
        需要修理的槽位号列表。
    """
    if not positions:
        return
    page.select_panel(Panel.QUICK_REPAIR)
    time.sleep(0.8)
    for pos in positions:
        if pos not in BLOOD_BAR_PROBE:
            _log.warning('[QuickRepair] 无效修理位置: {}', pos)
            continue
        page._ctrl.click(*BLOOD_BAR_PROBE[pos])
        time.sleep(1.5)
        _log.info('[QuickRepair] 出征准备 → 修理位置 {}', pos)


def apply_quick_repair(
    page: BaseBattlePreparation,
    strategy: RepairStrategy | None = None,
    *,
    repair_manually: bool | None = None,
    manual_repair_action: Callable[[list[int]], None] | None = None,
    retry_count: int = 3,
) -> list[int]:
    """根据策略执行快速修理 (检查 → 修理 → 复查 → 有限重试)。

    Parameters
    ----------
    page:
        出征准备页控制器。
    strategy:
        修理策略, 默认 ``RepairStrategy.SEVERE``。
    repair_manually:
        显式传入时覆盖全局配置；``None`` 表示沿用全局 ``repair_manually``。
    manual_repair_action:
        Callback receives the detected repair slot indexes.
        手动修理触发前执行的导航动作。
    retry_count:
        修理失败复查的最大重试次数。

    Returns
    -------
    list[int]
        实际修理的槽位列表。

    Raises
    ------
    ActionFailedError
        需要手动修理, 或重试后仍有舰船未修复。
    """
    if strategy is None:
        strategy = RepairStrategy.SEVERE

    if strategy is RepairStrategy.NEVER:
        return []

    manual_repair_enabled = (
        page._ctx.config.repair_manually if repair_manually is None else repair_manually
    )
    repair_pos = []
    positions = check_repair(page, strategy)
    for i in range(retry_count):
        # 没有需要修理的舰船，直接返回
        if not positions:
            return []
        # 需要手动修理，退出程序
        if manual_repair_enabled:
            if manual_repair_action is not None:
                try:
                    manual_repair_action(positions)
                except ManualRepairRequiredError:
                    raise
                except Exception as exc:
                    raise ManualRepairRequiredError('手动维修处理失败') from exc
            raise ManualRepairRequiredError('需要进行手动修理')
        repair_slots(page, positions)
        repair_pos.extend(positions)
        # 修理完成再检查一遍
        positions = check_repair(page, strategy)
        if not positions:
            _log.info('[QuickRepair] 修理位置: {} (策略: {})', repair_pos, strategy.value)
            return repair_pos
        _log.info(f'[QuickRepair] 有舰船修理失败: {positions}, 重试第 {i} 次')
    # 经过重试仍修理失败
    _log.error('[QuickRepair] 舰船修理异常(策略: {})', strategy.value)
    raise ActionFailedError('舰船修理异常')
