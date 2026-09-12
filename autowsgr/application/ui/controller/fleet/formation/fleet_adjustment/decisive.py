"""模块功能：执行决战准备页的无搜索框编队调整。

上层调用：
- formation.fleet_adjustment.workflow：按 task_type 分派决战编队流程。
- business.combat.decisive：传入决战目标舰队规则。

下层依赖：
- fleet_adjustment.workflow：提供快照、成员匹配、单舰操作和排序入口。
- common.fleet：提供规范化舰船选择规则。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.fleet.formation.fleet_adjustment import constants
from autowsgr.common.fleet import FleetSlotRule, ShipSelector
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from autowsgr.application.ui.controller.fleet.formation.fleet_adjustment import (
        FleetAdjustment,
    )
    from autowsgr.application.ui.controller.fleet.formation.fleet_recognition import (
        FleetSnapshot,
    )


_log = get_logger('ui.fleet.formation.fleet_adjustment')


def adjust_decisive_fleet(
    adjustment: FleetAdjustment,
    ship_names: Sequence[str | None],
    *,
    on_event: Callable[..., None] | None = None,
) -> FleetSnapshot:
    """使用决战无搜索框流程完成六个物理槽位的编队调整。"""
    adjustment._use_search = False
    adjustment._alignment._use_search = False
    _set_event_handler(adjustment, on_event)

    names = [
        name.strip() if isinstance(name, str) and name.strip() else None
        for name in list(ship_names)[:6]
    ]
    names += [None] * (6 - len(names))
    if names[0] is None:
        raise ValueError('决战编队一号位不能为空')

    selectors = [
        FleetSlotRule(primary=ShipSelector(name=name)) if name is not None else None
        for name in names
    ]
    assigned = adjustment._plan_target_options(selectors)
    if assigned is None or assigned[0] is None:
        raise RuntimeError('决战编队规则无法分配一号位')

    snapshot = adjustment._read_fleet_snapshot()
    adjustment._initial_snapshot = snapshot
    current = list(snapshot.names)
    occupied = list(snapshot.occupied)
    for attempt in range(constants.MAX_SET_RETRIES + 1):
        if adjustment._validate_assignment(current, occupied, assigned):
            return _finish_decisive_fleet(adjustment, current, occupied, assigned)

        matched, matched_slots = adjustment._match_existing_members(
            current,
            names,
            selectors,
        )
        for target_slot, name in enumerate(names):
            if name is None or target_slot in matched_slots:
                continue
            slot = next((index for index in range(6) if not matched[index]), None)
            if slot is None:
                raise RuntimeError(f'决战没有可用槽位: {name}')
            selected = adjustment._change_single_ship(
                slot,
                name,
                slot_occupied=occupied[slot],
            )
            current[slot] = selected or name
            occupied[slot] = True
            matched[slot] = True
            matched_slots.add(target_slot)
            adjustment._emit_fleet_event(
                'fleet_checkpoint',
                stage='selected',
                slot=slot + 1,
                members=list(current),
            )
            time.sleep(constants.ACTION_WAIT)

        for slot in range(5, -1, -1):
            if matched[slot] or not occupied[slot]:
                continue
            adjustment._change_single_ship(slot, None, slot_occupied=True)
            current[slot] = None
            occupied[slot] = False
            adjustment._emit_fleet_event(
                'fleet_checkpoint',
                stage='cleared',
                slot=slot + 1,
                members=list(current),
            )
            time.sleep(constants.ACTION_WAIT)

        adjustment._reorder(current, names)
        final_snapshot = adjustment._read_fleet_snapshot(expected_names=names)
        current, occupied = adjustment._merge_position_snapshot(current, final_snapshot)
        if adjustment._validate_assignment(current, occupied, assigned):
            return _finish_decisive_fleet(adjustment, current, occupied, assigned)
        if attempt < constants.MAX_SET_RETRIES:
            _log.warning(
                '[Fleet] 决战编队第 {}/{} 次验证失败，重试',
                attempt + 1,
                constants.MAX_SET_RETRIES + 1,
            )
            time.sleep(constants.RETRY_WAIT)

    raise RuntimeError('决战编队重试后仍未满足目标规则')


def _finish_decisive_fleet(
    adjustment: FleetAdjustment,
    current: list[str | None],
    occupied: list[bool],
    assigned: list[ShipSelector | None],
) -> FleetSnapshot:
    """记录决战编队成功并返回当前事实。"""
    verified_slots: set[int] = set()
    adjustment._log_final_result(
        current,
        occupied,
        assigned,
        verified_slots,
        passed=True,
    )
    snapshot = adjustment._initial_snapshot
    return type(snapshot)(
        names=list(current),
        occupied=list(occupied),
        ship_types=snapshot.ship_types if snapshot is not None else None,
        ship_levels=snapshot.ship_levels if snapshot is not None else None,
    )


def _set_event_handler(
    adjustment: FleetAdjustment,
    on_event: Callable[..., None] | None,
) -> None:
    """设置本次决战流程的事件出口。"""
    adjustment._on_fleet_event = on_event
    adjustment._alignment._on_fleet_event = on_event


__all__ = ['adjust_decisive_fleet']
