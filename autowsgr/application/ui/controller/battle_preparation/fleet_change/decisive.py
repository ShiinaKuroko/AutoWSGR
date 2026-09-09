"""模块功能：执行决战出征准备页的无搜索框舰队编成流程。

上层调用：
- application.ui.controller.battle_preparation.fleet_change：公开决战编队分支。
- application.ui.controller.operations.sortie_page.decisive_page.preparation_page：在决战准备页触发换船。

下层依赖：
- application.ui.controller.battle_preparation.fleet_change._change：提供页面选船和排序。
- common.system.logger：记录编队阶段和失败原因。

决战选船不使用搜索框；页面差异保留在本模块，不改变通用选船算法。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from autowsgr.application.ui.controller.battle_preparation.fleet_change._change import (
        FleetChangeMixin,
    )


_log = get_logger('ui.preparation')
_MAX_SET_RETRIES = 2


def change_decisive_fleet(  # noqa: PLR0912
    page: FleetChangeMixin,
    ship_names: Sequence[str | None],
    *,
    on_event: Callable[..., None] | None = None,
) -> bool:
    """使用决战的无搜索框 OCR 流程完成编队。"""
    names = [
        name.strip() if isinstance(name, str) and name.strip() else None
        for name in list(ship_names)[:6]
    ]
    names += [None] * (6 - len(names))
    if names[0] is None:
        raise ValueError('决战编队一号位不能为空')

    page._use_search = False
    page._last_changed_fleet = None
    page._on_fleet_event = on_event
    selectors = [None] * 6
    _log.info('[Fleet] 决战目标编队：{}', names)

    for attempt in range(_MAX_SET_RETRIES + 1):
        current = page.detect_fleet()
        if page._validate_with_selector(current, names, selectors):
            page._last_changed_fleet = list(current)
            return True

        matched, matched_slots = page._match_existing_members(current, names, selectors)
        for target_slot, name in enumerate(names):
            if name is None or target_slot in matched_slots:
                continue

            slot = next((index for index in range(6) if not matched[index]), None)
            if slot is None:
                _log.warning('[Fleet] 决战没有可用槽位：{}', name)
                continue

            selected = page._change_single_ship(
                slot,
                name,
                selector=None,
                slot_occupied=current[slot] is not None,
            )
            current[slot] = selected if selected is not None else name
            matched[slot] = True
            matched_slots.add(target_slot)
            if on_event is not None:
                on_event('fleet_checkpoint', stage='selected', slot=slot + 1, members=list(current))
            time.sleep(0.3)

        for slot in range(5, -1, -1):
            if not matched[slot] and current[slot] is not None:
                page._change_single_ship(slot, None, selector=None, slot_occupied=True)
                current[slot] = None
                if on_event is not None:
                    on_event(
                        'fleet_checkpoint', stage='cleared', slot=slot + 1, members=list(current)
                    )
                time.sleep(0.3)

        current = page.detect_fleet()
        page._reorder(current, names)
        current = page.detect_fleet()
        if page._validate_with_selector(current, names, selectors):
            page._last_changed_fleet = list(current)
            _log.info('[Fleet] 决战编队完成：{}', current)
            if on_event is not None:
                on_event('fleet_result', stage='complete', members=list(current))
            return True

        if attempt < _MAX_SET_RETRIES:
            _log.warning(
                '[Fleet] 决战编队第 {}/{} 次验证失败，重试', attempt + 1, _MAX_SET_RETRIES + 1
            )
            time.sleep(0.5)

    _log.error('[Fleet] 决战编队重试后仍未满足目标')
    return False
