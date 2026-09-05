"""战役页面操作和战前准备。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from autowsgr.application.ui.controller.battle_preparation import (
    BattlePreparationPage,
    RepairStrategy,
)
from autowsgr.application.ui.controller.map import MapPage, MapPanel
from autowsgr.business.combat.fleet import exact_fleet_rules
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import RepairMode, ShipDamageState
from autowsgr.common.ui.interaction import NavigationError


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.application.runtime import RuntimeContext as GameContext

    from .spec import CampaignSpec


_log = get_logger('business.combat.campaign')


class CampaignOperations:
    """执行战役用例所需的页面组合操作。"""

    def __init__(
        self,
        ctx: GameContext,
        *,
        wait: Callable[[float], None],
        report: Callable[..., None],
        save_progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.ctx = ctx
        self._wait = wait
        self._report = report
        self._save_progress = save_progress or (lambda _data: None)

    def enter_campaign(self, spec: CampaignSpec) -> None:
        """从地图页进入指定战役的出征准备页。"""
        page = MapPage(self.ctx)
        page.ensure_panel(MapPanel.BATTLE)
        self._report('panel_ready', campaign=spec.campaign_name)
        self._wait(0)
        page.enter_campaign(
            map_index=spec.map_index,
            difficulty=spec.difficulty,
            campaign_name=spec.campaign_name,
        )

    def prepare_battle(
        self,
        spec: CampaignSpec,
        *,
        reset_fleet: bool = True,
    ) -> tuple[BattlePreparationPage, list[ShipDamageState], list[Any]]:
        """完成编队、修理和战前血量识别。"""
        self._wait(0.25)
        page = BattlePreparationPage(self.ctx)

        selection = spec.fleet_selection
        self._report('formation_entered')
        self._wait(0)
        slot_rules = selection.slot_rules
        if slot_rules is None and selection.plain_fleet is not None:
            slot_rules = exact_fleet_rules(selection.plain_fleet)
        if slot_rules is not None:
            _log.info('[Campaign] 战役队伍加载：编队配置加载成功')
            if not page.change_fleet(
                None,
                slot_rules,
                task_type='campaign',
                reset_fleet=reset_fleet,
                recognize_ship_types=not spec.skip_ship_type_validation,
                on_event=self._on_fleet_event,
            ):
                raise RuntimeError('战役编队未满足任务规则')
            self._report('fleet_ready', members=page.last_changed_fleet)
        elif spec.required_ship_types is not None:
            if not page.validate_campaign_fleet(
                spec.required_ship_types,
                validate_types=not spec.skip_ship_type_validation,
            ):
                raise RuntimeError('当前舰队不满足困难战役舰种和数量限制')
            _log.info('[Campaign] 战役队伍加载：未配置编队，沿用当前队伍')
            self._report('fleet_ready')
        else:
            _log.info('[Campaign] 战役队伍加载：未配置编队，沿用当前队伍')
            self._report('fleet_ready')

        strategy = _repair_strategy(spec.plan.repair_mode)
        if strategy is not None:
            page.apply_repair(strategy)

        info = page.detect_fleet_info()
        ship_stats = [info.ship_damage.get(index, ShipDamageState.NORMAL) for index in range(6)]
        ships = info.to_ships(page.last_changed_fleet or selection.primary_names)
        return page, ship_stats, ships

    def _on_fleet_event(self, event: str, **data: Any) -> None:
        """保存战役编队断点。"""
        if event in {'ship_selected', 'ship_removed'}:
            return
        self._report(event, **data)
        if event not in {'fleet_checkpoint', 'fleet_result'}:
            return
        self._save_progress(
            {
                'stage': data.get('stage', 'complete'),
                'slot': data.get('slot'),
                'members': list(data.get('members', [])),
            },
        )
        if event == 'fleet_checkpoint':
            self._wait(0)

    def start_battle(self, page: BattlePreparationPage) -> bool:
        """点击出征并探测是否离开准备页。"""
        for attempt in range(2):
            if page.try_start_battle(target='campaign combat'):
                _log.info('[Campaign] 战役战斗开始')
                self._report('battle_started')
                return True
            if attempt == 0:
                _log.warning('[Campaign] 出征后仍在准备页，重试一次')

        _log.info('[Campaign] 两次出征均未离开准备页，判定战役次数已用完')
        try:
            page.go_back()
        except NavigationError as error:
            _log.warning('[Campaign] 战役次数耗尽后回退地图失败: {}', error)
        return False


def _repair_strategy(repair_mode: list[RepairMode]) -> RepairStrategy | None:
    value = min(mode.value for mode in repair_mode)
    if value <= RepairMode.moderate_damage.value:
        return RepairStrategy.MODERATE
    if value <= RepairMode.severe_damage.value:
        return RepairStrategy.SEVERE
    return None
