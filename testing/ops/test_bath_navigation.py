"""普通出征和决战进入澡堂的模式专用导航测试。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.battle_preparation import (
    BattlePreparationPage,
    RepairStrategy,
    repair_action,
)
from autowsgr.application.ui.navigation import service
from autowsgr.business.logistics.repair import bath_repair
from autowsgr.common.system import ManualRepairRequiredError
from autowsgr.common.types import PageName, ShipDamageState


def test_normal_sortie_returns_to_map_before_bath(monkeypatch: pytest.MonkeyPatch) -> None:
    """普通出征准备页先回普通地图，再进入澡堂。"""
    page = MagicMock()
    monkeypatch.setattr(
        'autowsgr.application.ui.controller.battle_preparation.BattlePreparationPage',
        lambda _ctx: page,
    )
    goto_page = MagicMock()
    monkeypatch.setattr(service, 'goto_page', goto_page)
    ctx = object()

    service.goto_bath_from_normal_sortie(ctx)

    page.go_back.assert_called_once_with()
    goto_page.assert_called_once_with(ctx, PageName.BATH)


def test_event_sortie_returns_to_event_map_before_bath(monkeypatch: pytest.MonkeyPatch) -> None:
    """活动出征准备页先回活动地图，再进入澡堂。"""
    click_and_wait = MagicMock()
    monkeypatch.setattr('autowsgr.common.ui.interaction.click_and_wait_for_page', click_and_wait)
    goto_page = MagicMock()
    monkeypatch.setattr(service, 'goto_page', goto_page)
    ctx = SimpleNamespace(ctrl=object())

    service.goto_bath_from_event_sortie(ctx)

    click_and_wait.assert_called_once()
    assert click_and_wait.call_args.args[0] is ctx.ctrl
    assert click_and_wait.call_args.kwargs['source'] is PageName.BATTLE_PREP
    assert click_and_wait.call_args.kwargs['target'] is PageName.EVENT_MAP
    goto_page.assert_called_once_with(ctx, PageName.BATH)


def test_campaign_sortie_returns_via_campaign_selection_before_bath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparation = MagicMock()
    campaign_selection = MagicMock()
    monkeypatch.setattr(
        'autowsgr.application.ui.controller.battle_preparation.BattlePreparationPage',
        lambda _ctx: preparation,
    )
    monkeypatch.setattr(
        'autowsgr.application.ui.controller.operations.sortie_page.battle_page.MapPage',
        lambda _ctx: campaign_selection,
    )
    goto_page = MagicMock()
    monkeypatch.setattr(service, 'goto_page', goto_page)
    ctx = object()

    service.goto_bath_from_campaign_sortie(ctx)

    preparation.go_back.assert_called_once_with()
    campaign_selection.go_back.assert_called_once_with()
    goto_page.assert_called_once_with(ctx, PageName.BATH)


def test_decisive_sortie_leaves_saved_map_before_bath(monkeypatch: pytest.MonkeyPatch) -> None:
    """决战出征准备页使用暂离保存进度，回到总览后再进入澡堂。"""
    controller = MagicMock()
    decisive_config = object()
    ctx = SimpleNamespace(
        config=SimpleNamespace(decisive_battle=decisive_config),
        ctrl=object(),
    )
    monkeypatch.setattr(
        'autowsgr.application.ui.controller.operations.sortie_page.decisive_page.DecisiveMapController',
        lambda _ctx, _config: controller,
    )
    goto_page = MagicMock()
    monkeypatch.setattr(service, 'goto_page', goto_page)
    wait_for_page = MagicMock()
    monkeypatch.setattr('autowsgr.common.ui.interaction.wait_for_page', wait_for_page)

    service.goto_bath_from_decisive_sortie(ctx)

    controller.go_to_map_page.assert_called_once_with()
    controller.open_retreat_dialog.assert_called_once_with()
    controller.confirm_leave.assert_called_once_with()
    controller.confirm_retreat.assert_not_called()
    wait_for_page.assert_called_once()
    assert wait_for_page.call_args.args[0] is ctx.ctrl
    assert wait_for_page.call_args.kwargs['target'] is PageName.DECISIVE_BATTLE
    goto_page.assert_called_once_with(ctx, PageName.BATH)


def test_manual_repair_action_runs_before_manual_repair_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = SimpleNamespace(
        ctrl=MagicMock(),
        config=SimpleNamespace(repair_manually=True),
        ocr=MagicMock(),
    )
    page = BattlePreparationPage(ctx)
    monkeypatch.setattr(repair_action, 'check_repair', lambda _page, _strategy: [0])
    manual_repair_action = MagicMock()

    with pytest.raises(ManualRepairRequiredError, match='需要进行手动修理'):
        page.apply_repair(
            RepairStrategy.MODERATE,
            manual_repair_action=manual_repair_action,
        )

    manual_repair_action.assert_called_once_with([0])


def test_manual_bath_repair_dispatches_targets_and_returns_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = MagicMock()
    page.repair_ship.side_effect = [120, -1]
    ship = MagicMock()
    ctx = SimpleNamespace(
        bathroom=MagicMock(),
        config=SimpleNamespace(bathroom_count=2),
        get_ship=lambda _name: ship,
        update_ship_damage=MagicMock(),
    )
    goto_page = MagicMock()
    monkeypatch.setattr(bath_repair, 'BathPage', lambda _ctx: page)
    monkeypatch.setattr(bath_repair, 'goto_page', goto_page)

    bath_repair.repair_manual_targets_in_bath(ctx, ['ship-1', 'ship-2'])

    assert page.open_choose_repair_overlay.call_count == 2
    page.repair_ship.assert_any_call('ship-1')
    page.repair_ship.assert_any_call('ship-2')
    ship.set_repair.assert_called_once_with(120)
    ctx.update_ship_damage.assert_called_once_with('ship-1', ShipDamageState.NORMAL)
    ctx.bathroom.occupy.assert_called_once_with(120)
    goto_page.assert_called_once_with(ctx, PageName.HOME)
