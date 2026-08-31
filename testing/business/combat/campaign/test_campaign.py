"""战役业务入口的无设备回归。"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import autowsgr.business.base as base_module
import autowsgr.business.combat.campaign.executor as executor_module
import autowsgr.business.combat.campaign.operations as operations_module
import autowsgr.business.system.initialize.initialize as initialize_module
from autowsgr.application.ui.pages.battle_preparation import BattlePreparationPage
from autowsgr.application.ui.pages.battle_preparation.fleet_change._detect import FleetSnapshot
from autowsgr.business.combat import CombatResult
from autowsgr.business.combat.campaign.spec import (
    CAMPAIGN_FLEET_TYPES,
    CampaignSpec,
    parse_campaign_name,
)
from autowsgr.business.combat.fleet import exact_fleet_rules
from autowsgr.dispatch import TaskPaused
from autowsgr.types import ConditionFlag, RepairMode, ShipDamageState, ShipType


def _ctx() -> SimpleNamespace:
    def screenshot() -> object:
        return object()

    return SimpleNamespace(
        ctrl=SimpleNamespace(screenshot=screenshot),
        config=SimpleNamespace(
            daily_automation=SimpleNamespace(auto_set_support=False),
        ),
        ocr=None,
    )


def test_campaign_spec_builds_single_point_plan() -> None:
    assert parse_campaign_name('困难航母') == (4, 'hard')

    spec = CampaignSpec.from_params(
        {
            'campaign_name': '困难航母',
            'formation': 1,
            'night': False,
            'repair_mode': 1,
        },
    )

    assert spec.map_index == 4
    assert spec.difficulty == 'hard'
    assert spec.plan.mode == 'battle'
    assert spec.plan.default_node.formation.value == 1
    assert spec.plan.default_node.night is False
    assert spec.plan.repair_mode == [RepairMode.moderate_damage] * 6
    assert spec.required_ship_types == CAMPAIGN_FLEET_TYPES[4]


def test_campaign_spec_accepts_fleet_rules() -> None:
    spec = CampaignSpec.from_params(
        {
            'campaign_name': '简单航母',
            'fleet_rules': [
                {
                    'name': 'U-177',
                    'ship_type': ['ss'],
                    'min_level': 69,
                },
            ],
        },
    )

    selection = spec.fleet_selection
    assert selection.slot_rules is not None
    assert selection.slot_rules[0].primary is not None
    assert selection.slot_rules[0].primary.name == 'U-177'
    assert selection.slot_rules[0].primary.min_level == 69


@pytest.mark.parametrize(
    ('campaign_name', 'expected_types'),
    [
        ('困难驱逐', CAMPAIGN_FLEET_TYPES[1]),
        ('困难巡洋', CAMPAIGN_FLEET_TYPES[2]),
        ('困难战列', CAMPAIGN_FLEET_TYPES[3]),
        ('困难航母', CAMPAIGN_FLEET_TYPES[4]),
        ('困难潜艇', CAMPAIGN_FLEET_TYPES[5]),
    ],
)
def test_hard_campaign_applies_fixed_slot_types(
    campaign_name: str,
    expected_types: tuple[ShipType, ...],
) -> None:
    spec = CampaignSpec.from_params(
        {
            'campaign_name': campaign_name,
            'fleet': [f'ship-{index}' for index in range(len(expected_types))],
        },
    )

    assert spec.fleet_selection.slot_rules is not None
    assert [
        rule.primary.ship_types[0]
        for rule in spec.fleet_selection.slot_rules
        if rule.primary is not None
    ] == list(expected_types)


def test_hard_campaign_without_names_validates_the_current_fleet() -> None:
    spec = CampaignSpec.from_params({'campaign_name': '困难潜艇'})

    assert spec.required_ship_types == (ShipType.SS, ShipType.SS, ShipType.SS)
    assert spec.fleet_selection.slot_rules is None


def test_hard_campaign_rejects_wrong_fleet_size() -> None:
    with pytest.raises(ValueError, match='必须提供 6 个'):
        CampaignSpec.from_params(
            {
                'campaign_name': '困难驱逐',
                'fleet': ['ship-1'],
            },
        )


def test_campaign_type_validation_preserves_physical_empty_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ctx()
    ctx.ocr = object()
    page = BattlePreparationPage(ctx)
    monkeypatch.setattr(
        page,
        'detect_fleet_snapshot',
        lambda **_kwargs: FleetSnapshot(
            names=['A', None, 'C', None, None, None],
            occupied=[True, False, True, False, False, False],
            ship_types=[ShipType.SS, None, ShipType.SS, None, None, None],
        ),
    )
    assert not page.validate_campaign_fleet((ShipType.SS, ShipType.SS, ShipType.SS))


def test_campaign_fleet_changes_each_physical_slot_without_dragging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl = MagicMock()
    ctx = _ctx()
    ctx.ctrl = ctrl
    page = BattlePreparationPage(ctx)
    initial = FleetSnapshot(
        names=['B', 'A', 'X', None, None, None],
        occupied=[True, True, True, False, False, False],
    )
    changes: list[tuple[int, str | None]] = []

    monkeypatch.setattr(page, '_detect_initial_snapshot', lambda *_args: initial)
    monkeypatch.setattr(
        page,
        '_detect_position_snapshot',
        lambda current, _names, **_kwargs: (list(current), [name is not None for name in current]),
    )
    monkeypatch.setattr(
        page,
        '_change_single_ship',
        lambda slot, name, **_kwargs: changes.append((slot, name)) or name,
    )

    assert page.change_fleet(
        None,
        exact_fleet_rules(['A', 'B']),
        task_type='campaign',
    )
    assert changes == [(1, None), (0, None), (0, 'A'), (1, 'B'), (2, None)]
    ctrl.swipe.assert_not_called()


def test_campaign_fleet_rejects_more_than_six_slots() -> None:
    with pytest.raises(ValueError, match='最多包含 6 个'):
        BattlePreparationPage(_ctx()).change_fleet(
            None,
            exact_fleet_rules([f'ship-{index}' for index in range(7)]),
            task_type='campaign',
        )


@pytest.mark.parametrize(
    'params',
    [
        {
            'campaign_name': '困难航母',
            'fleet': ['U-177'],
            'fleet_rules': ['U-103'],
        },
        {
            'campaign_name': '困难航母',
            'fleet_rules': ['U-177'] * 7,
        },
    ],
)
def test_campaign_spec_rejects_ambiguous_or_oversized_fleet(params: dict[str, object]) -> None:
    with pytest.raises(ValueError, match='战役'):
        CampaignSpec.from_params(params)


@pytest.mark.parametrize(
    'params',
    [
        {},
        {'campaign_name': '不存在'},
        {'campaign_name': '困难航母', 'mode': 'normal'},
        {'campaign_name': '困难航母', 'night': 'yes'},
    ],
)
def test_campaign_spec_rejects_invalid_params(params: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        CampaignSpec.from_params(params)


def test_campaign_executor_runs_battle_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    page = MagicMock()
    events: list[str] = []
    monkeypatch.setattr(initialize_module, 'initialize', lambda _ctx: None)
    monkeypatch.setattr(base_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(operations_module.CampaignOperations, 'enter_campaign', lambda *_args: None)
    monkeypatch.setattr(
        operations_module.CampaignOperations,
        'prepare_battle',
        lambda *_args: (page, [ShipDamageState.NORMAL] * 6, []),
    )
    monkeypatch.setattr(operations_module.CampaignOperations, 'start_battle', lambda *_args: True)
    monkeypatch.setattr(operations_module.CampaignOperations, 'return_home', lambda *_args: None)
    monkeypatch.setattr(
        executor_module,
        'run_combat',
        lambda *_args, **_kwargs: CombatResult(flag=ConditionFlag.OPERATION_SUCCESS),
    )

    executor = executor_module.CampaignExecutor(
        _ctx(),
        {'campaign_name': '困难航母'},
        on_event=lambda event, **_data: events.append(event),
    )

    result = executor.run()

    assert result.flag is ConditionFlag.OPERATION_SUCCESS
    assert events == ['before_start', 'battle_done']


def test_campaign_operations_use_page_difficulty_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class MapPageStub:
        def __init__(self, _ctx: object) -> None:
            pass

        def enter_campaign(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(operations_module, 'MapPage', MapPageStub)
    monkeypatch.setattr(operations_module, 'goto_page', lambda *_args: None)

    operations = operations_module.CampaignOperations(
        _ctx(),
        wait=lambda _seconds: None,
        report=lambda *_args, **_kwargs: None,
    )
    operations.enter_campaign(CampaignSpec.from_params({'campaign_name': '困难航母'}))

    assert captured['difficulty'] == 'hard'


def test_campaign_operations_checks_unconfigured_hard_fleet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = MagicMock()
    page.validate_campaign_fleet.return_value = False
    monkeypatch.setattr(operations_module, 'BattlePreparationPage', lambda _ctx: page)

    spec = CampaignSpec.from_params({'campaign_name': '困难潜艇'})
    operations = operations_module.CampaignOperations(
        _ctx(),
        wait=lambda _seconds: None,
        report=lambda *_args, **_kwargs: None,
    )

    with pytest.raises(RuntimeError, match='困难战役'):
        operations.prepare_battle(spec)

    page.validate_campaign_fleet.assert_called_once_with(spec.required_ship_types)


def test_campaign_executor_keeps_result_across_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    pause = threading.Event()
    progress: dict[str, object] = {}
    result = CombatResult(flag=ConditionFlag.OPERATION_SUCCESS)
    monkeypatch.setattr(initialize_module, 'initialize', lambda _ctx: None)
    monkeypatch.setattr(base_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(base_module, 'goto_page', MagicMock())
    monkeypatch.setattr(operations_module.CampaignOperations, 'enter_campaign', lambda *_args: None)
    monkeypatch.setattr(
        operations_module.CampaignOperations,
        'prepare_battle',
        lambda *_args: (MagicMock(), [ShipDamageState.NORMAL] * 6, []),
    )
    monkeypatch.setattr(operations_module.CampaignOperations, 'start_battle', lambda *_args: True)
    monkeypatch.setattr(operations_module.CampaignOperations, 'return_home', lambda *_args: None)
    monkeypatch.setattr(executor_module, 'run_combat', lambda *_args, **_kwargs: result)

    def pause_after_battle(event: str, **_data: object) -> None:
        if event == 'battle_done':
            pause.set()

    first = executor_module.CampaignExecutor(
        _ctx(),
        {'campaign_name': '困难航母'},
        pause=pause,
        progress=progress,
        on_event=pause_after_battle,
    )
    with pytest.raises(TaskPaused):
        first.run()

    pause.clear()
    resumed = executor_module.CampaignExecutor(
        _ctx(),
        {'campaign_name': '困难航母'},
        pause=pause,
        progress=progress,
    )

    assert resumed.run() is result
    assert '_result' not in progress
