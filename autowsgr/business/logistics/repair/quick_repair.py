"""快速修理 — 出征准备页内的修理策略执行。

性质:
    战斗链路的内部步骤 (面板切换, 不跨页面), 不满足打断点契约,
    不进调度视野 — 放在本域仅为与浴场修理同地管理。

职责边界:
    本模块持有「策略」(何时修、修到什么程度、手动修理门禁、重试编排);
    页面持有「操作能力」(select_panel 面板切换、detect_ship_damage 血条探测)。
    与 overlays 的拆法一致: 业务决策在 business, UI 操作在页面/infra。

调用方式:
    BattlePreparationPage.apply_repair / check_repair / repair_slots
    委托到本模块函数 (见 ui/battle/repair.py 的薄壳),
    战斗链路调用方 (normal_fight / campaign / decisive) 无感。
"""

from __future__ import annotations

import time

from autowsgr.infra import ActionFailedError
from autowsgr.infra.logger import get_logger
from autowsgr.types import ShipDamageState
from autowsgr.ui.battle.base import BaseBattlePreparation, Panel, RepairStrategy
from autowsgr.ui.battle.constants import BLOOD_BAR_PROBE


_log = get_logger('business.logistics.repair')


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


def apply_quick_repair(
    page: BaseBattlePreparation,
    strategy: RepairStrategy | None = None,
    *,
    repair_manually: bool = False,
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
        调用方要求手动修理 (如决战关闭快修时), 与全局配置取或。
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

    repair_pos = []
    positions = check_repair(page, strategy)
    for i in range(retry_count):
        # 没有需要修理的舰船，直接返回
        if not positions:
            return []
        # 需要手动修理，退出程序
        if page._ctx.config.repair_manually or repair_manually:
            raise ActionFailedError('需要进行手动修理')
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
