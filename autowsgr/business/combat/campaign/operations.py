"""战役页面操作和战前准备。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from autowsgr.application.ui.navigation import goto_page
from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage, RepairStrategy
from autowsgr.application.ui.pages.map import MapPage
from autowsgr.business.combat.fleet import exact_fleet_rules
from autowsgr.common.system.logger import get_logger
from autowsgr.common.ui.interaction import NavigationError, wait_leave_page
from autowsgr.types import PageName, RepairMode, ShipDamageState


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
    ) -> None:
        self.ctx = ctx
        self._wait = wait
        self._report = report

    def enter_campaign(self, spec: CampaignSpec) -> None:
        """从当前页面进入指定战役的出征准备页。"""
        goto_page(self.ctx, PageName.MAP)
        MapPage(self.ctx).enter_campaign(
            map_index=spec.map_index,
            difficulty=spec.difficulty,
            campaign_name=spec.campaign_name,
        )
        self._report('panel_ready', campaign=spec.campaign_name)

    def prepare_battle(
        self,
        spec: CampaignSpec,
    ) -> tuple[BattlePreparationPage, list[ShipDamageState], list[Any]]:
        """完成支援、编队、修理和战前血量识别。"""
        self._wait(0.25)
        page = BattlePreparationPage(self.ctx)

        support = spec.auto_support
        if support is None:
            daily = getattr(getattr(self.ctx, 'config', None), 'daily_automation', None)
            support = bool(getattr(daily, 'auto_set_support', False))
        if support:
            ensure_battle_support(self.ctx, enabled=True)

        selection = spec.fleet_selection
        self._report('formation_entered', fleet_id=selection.fleet_id)
        slot_rules = selection.slot_rules
        if slot_rules is None and selection.plain_fleet is not None:
            slot_rules = exact_fleet_rules(selection.plain_fleet)
        if slot_rules is not None:
            _log.info('[Campaign] 开始编成战役舰队')
            if not page.change_fleet(None, slot_rules, task_type='campaign'):
                raise RuntimeError('战役编队未满足任务规则')
            self._report('fleet_ready', members=page.last_changed_fleet)
        elif spec.required_ship_types is not None and not page.validate_campaign_fleet(
            spec.required_ship_types,
        ):
            raise RuntimeError('当前舰队不满足困难战役舰种和数量限制')
        else:
            self._report('fleet_ready')

        strategy = _repair_strategy(spec.plan.repair_mode)
        if strategy is not None:
            page.apply_repair(strategy)

        info = page.detect_fleet_info()
        ship_stats = [info.ship_damage.get(index, ShipDamageState.NORMAL) for index in range(6)]
        ships = info.to_ships(selection.primary_names)
        return page, ship_stats, ships

    def start_battle(self, page: BattlePreparationPage) -> bool:
        """点击出征并探测是否离开准备页。"""
        for attempt in range(2):
            page.start_battle()
            screen = wait_leave_page(
                self.ctx.ctrl,
                checker=BattlePreparationPage.is_current_page,
                timeout=1.5,
                source=PageName.BATTLE_PREP,
                target='campaign combat',
                probe=True,
            )
            if screen is not None:
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

    def return_home(self) -> None:
        """从任意战役页面回到首页。"""
        goto_page(self.ctx, PageName.MAIN)


def ensure_battle_support(ctx: GameContext, *, enabled: bool = True) -> None:
    """确保军阶战役支援开关处于目标状态。"""
    page = BattlePreparationPage(ctx)
    screen = ctx.ctrl.screenshot()
    if page.is_support_enabled(screen) == enabled:
        _log.debug('[Campaign] 战役支援已为目标状态 {}', enabled)
        return
    _log.info('[Campaign] 战役支援状态不符，切换 → {}', enabled)
    page.toggle_battle_support()
    time.sleep(0.5)


def _repair_strategy(repair_mode: list[RepairMode]) -> RepairStrategy | None:
    value = min(mode.value for mode in repair_mode)
    if value <= RepairMode.moderate_damage.value:
        return RepairStrategy.MODERATE
    if value <= RepairMode.severe_damage.value:
        return RepairStrategy.SEVERE
    return None
