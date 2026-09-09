"""模块功能：在战役出征准备页按固定物理槽位执行舰队编成。

上层调用：
- application.ui.controller.battle_preparation.preparation：组合战役编队入口。
- business.combat.campaign：传入战役舰种或舰名规则。

下层依赖：
- application.ui.controller.battle_preparation.fleet_change._change：提供通用换船能力。
- application.ui.controller.battle_preparation.detection：提供舰队快照和状态校验。

战役页面不使用拖动和槽位左移；固定槽位约束属于页面行为，不能下沉到 common。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.battle_preparation.fleet_change import _change
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from autowsgr.application.ui.fleet import FleetSlotRule, ShipSelector
    from autowsgr.common.types import ShipType

_log = get_logger('ui.preparation')


class CampaignFleetChangeMixin(_change.FleetChangeMixin):
    """战役编队：固定物理槽位，只能点对点更换，禁止拖动和左移。"""

    def change_fleet(
        self,
        fleet_id: int | None,
        ship_names: Sequence[FleetSlotRule | str | None],
        *,
        task_type: str = 'normal',
        reset_fleet: bool = True,
        on_event: Callable[..., None] | None = None,
        recognize_ship_types: bool = True,
    ) -> bool:
        if task_type != 'campaign':
            return super().change_fleet(
                fleet_id,
                ship_names,
                task_type=task_type,
                on_event=on_event,
            )
        if len(ship_names) > 6:
            raise ValueError('战役编队最多包含 6 个槽位')
        if fleet_id is not None and self.read_selected_fleet(self._ctrl.screenshot()) != fleet_id:
            self.select_fleet(fleet_id)
            time.sleep(0.5)
        return self._change_campaign_fleet(
            ship_names,
            recognize_ship_types=recognize_ship_types,
            reset_fleet=reset_fleet,
            on_event=on_event,
        )

    def validate_campaign_fleet(
        self,
        required_types: Sequence[ShipType],
        *,
        validate_types: bool = True,
    ) -> bool:
        """校验未配置具体舰名的困难战役当前队伍。"""
        if not 1 <= len(required_types) <= 6:
            raise ValueError('战役舰种规则必须包含 1-6 个槽位')
        if self._preferred_ocr is None:
            raise RuntimeError('战役编队校验需要 OCR 引擎')

        snapshot = self.detect_fleet_snapshot(recognize_ship_details=validate_types)
        ship_types = snapshot.ship_types or []
        passed = all(
            snapshot.occupied[slot] and (not validate_types or ship_types[slot] is expected)
            for slot, expected in enumerate(required_types)
        ) and all(not occupied for occupied in snapshot.occupied[len(required_types) :])
        _log.info(
            '[Fleet] 战役舰种校验: 目标={} 当前={} 结果={}',
            [item.value for item in required_types],
            [item.value if item is not None else None for item in ship_types],
            '通过' if passed else '不通过',
        )
        return passed

    def _change_campaign_fleet(
        self,
        ship_names: Sequence[FleetSlotRule],
        *,
        recognize_ship_types: bool,
        reset_fleet: bool,
        on_event: Callable[..., None] | None,
    ) -> bool:
        self._last_changed_fleet = None
        self._on_fleet_event = on_event
        selectors = list(ship_names[:6])
        selectors += [None] * (6 - len(selectors))
        if selectors[0] is None:
            raise ValueError('战役编队一号位不能为空')

        assigned = self._plan_target_options(selectors)
        if assigned is None or assigned[0] is None:
            _log.error('[Fleet] 战役编队规则无法分配一号位')
            return False

        expected_pool = self._ocr_target_pool(selectors)
        if recognize_ship_types:
            snapshot = self._detect_initial_snapshot(expected_pool, selectors)
        else:
            snapshot = self._detect_initial_snapshot(
                expected_pool,
                selectors,
                recognize_ship_types=False,
            )
        current = list(snapshot.names)
        occupied = list(snapshot.occupied)
        verified_slots: set[int] = set()
        self._initial_snapshot = snapshot
        self._mark_snapshot_verified_slots(snapshot, assigned, verified_slots)
        self._emit_fleet_event(
            'fleet_validation',
            passed=self._validate_assignment(current, occupied, assigned, verified_slots),
            members=list(current),
        )
        if reset_fleet:
            self._clear_campaign_fleet(current, occupied)
            verified_slots.clear()

        for attempt in range(_change._MAX_SET_RETRIES + 1):
            names = self._target_names(assigned)
            if self._validate_assignment(current, occupied, assigned, verified_slots):
                return self._finish_campaign_fleet(current, occupied, assigned, verified_slots)

            self._replace_campaign_slots(
                current,
                occupied,
                assigned,
                selectors,
                verified_slots,
            )
            names = self._target_names(assigned)
            current, occupied = self._detect_position_snapshot(
                current,
                names,
                stage='战役最终位置',
                round_number=attempt + 1,
            )
            if self._validate_assignment(current, occupied, assigned, verified_slots):
                return self._finish_campaign_fleet(current, occupied, assigned, verified_slots)
            if attempt < _change._MAX_SET_RETRIES:
                time.sleep(0.5)

        self._log_final_result(
            current,
            occupied,
            assigned,
            verified_slots,
            passed=False,
        )
        return False

    def _clear_campaign_fleet(
        self,
        current: list[str | None],
        occupied: list[bool],
    ) -> None:
        """清空当前六个物理槽位，不压缩剩余成员。"""
        for slot in range(5, -1, -1):
            if occupied[slot] or current[slot] is not None:
                self._clear_campaign_slot(slot, current, occupied)

    def _replace_campaign_slots(
        self,
        current: list[str | None],
        occupied: list[bool],
        assigned: list[ShipSelector | None],
        selectors: list[FleetSlotRule | None],
        verified_slots: set[int],
    ) -> None:
        """先释放跨槽位重复目标，再逐物理槽位替换或清空。"""
        for target_slot, option in enumerate(assigned):
            if option is None:
                continue
            source_slot = next(
                (
                    slot
                    for slot, name in enumerate(current)
                    if slot != target_slot
                    and occupied[slot]
                    and self._option_matches_name(name, option)
                ),
                None,
            )
            if source_slot is not None:
                self._clear_campaign_slot(source_slot, current, occupied)

        for slot, option in enumerate(assigned):
            if option is None:
                if occupied[slot] or current[slot] is not None:
                    self._clear_campaign_slot(slot, current, occupied)
                continue
            if self._campaign_slot_satisfied(slot, current, occupied, option, verified_slots):
                continue
            self._select_campaign_slot(
                slot,
                option,
                selectors[slot],
                current,
                occupied,
                assigned,
                verified_slots,
            )

    def _select_campaign_slot(
        self,
        slot: int,
        option: ShipSelector,
        selector: FleetSlotRule | None,
        current: list[str | None],
        occupied: list[bool],
        assigned: list[ShipSelector | None],
        verified_slots: set[int],
    ) -> None:
        if selector is None:
            raise RuntimeError(f'战役槽位 {slot + 1} 缺少选船规则')
        options = (option, *[candidate for candidate in selector.options if candidate != option])
        previous = current[slot]
        selected = self._change_single_ship(
            slot,
            option.name,
            selector=options,
            slot_occupied=occupied[slot],
        )
        selected_option = next(
            (candidate for candidate in options if self._option_matches_name(selected, candidate)),
            None,
        )
        if selected is None or selected_option is None:
            raise RuntimeError(f'战役槽位 {slot + 1} 未选到目标舰船: {option.name}')
        current[slot] = selected
        occupied[slot] = True
        assigned[slot] = selected_option
        verified_slots.discard(slot)
        if self._requires_selection_validation(selected_option):
            verified_slots.add(slot)
        _log.info('[Fleet] 战役点对点换船: 槽位{} {} -> {}', slot + 1, previous or '空槽', selected)
        self._emit_fleet_event(
            'fleet_checkpoint',
            stage='selected',
            slot=slot + 1,
            members=list(current),
        )
        time.sleep(0.3)

    def _clear_campaign_slot(
        self,
        slot: int,
        current: list[str | None],
        occupied: list[bool],
    ) -> None:
        previous = current[slot]
        self._change_single_ship(slot, None, slot_occupied=occupied[slot])
        current[slot] = None
        occupied[slot] = False
        _log.info('[Fleet] 战役点对点清空: 槽位{} {} -> 空槽', slot + 1, previous or '未知舰船')
        self._emit_fleet_event(
            'fleet_checkpoint',
            stage='cleared',
            slot=slot + 1,
            members=list(current),
        )
        time.sleep(0.3)

    @classmethod
    def _campaign_slot_satisfied(
        cls,
        slot: int,
        current: Sequence[str | None],
        occupied: Sequence[bool],
        option: ShipSelector,
        verified_slots: set[int],
    ) -> bool:
        return (
            occupied[slot]
            and cls._option_matches_name(current[slot], option)
            and (not cls._requires_selection_validation(option) or slot in verified_slots)
        )

    def _finish_campaign_fleet(
        self,
        current: list[str | None],
        occupied: list[bool],
        assigned: list[ShipSelector | None],
        verified_slots: set[int],
    ) -> bool:
        self._log_final_result(
            current,
            occupied,
            assigned,
            verified_slots,
            passed=True,
        )
        self._last_changed_fleet = list(current)
        return True
