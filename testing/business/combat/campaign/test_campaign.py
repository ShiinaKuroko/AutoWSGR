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
from autowsgr.business.combat import CombatResult
from autowsgr.business.combat.campaign.spec import CampaignSpec, parse_campaign_name
from autowsgr.dispatch import TaskPaused
from autowsgr.types import ConditionFlag, RepairMode, ShipDamageState


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


def test_campaign_spec_accepts_fleet_rules() -> None:
    spec = CampaignSpec.from_params(
        {
            'campaign_name': '困难航母',
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
