"""演习执行器主链路的无设备静态回归。"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar
from unittest.mock import MagicMock

import pytest

import autowsgr.business.base as base_module
import autowsgr.business.combat.exercise.executor as executor_module
import autowsgr.business.system.initialize.initialize as initialize_module
from autowsgr.combat import CombatResult
from autowsgr.dispatch import TaskPaused
from autowsgr.types import ConditionFlag, ShipDamageState


if TYPE_CHECKING:
    from collections.abc import Callable


class _Rivals:
    def __init__(self, values: list[bool]) -> None:
        self.rivals = values


class _MapPage:
    statuses: ClassVar[list[list[bool]]] = []
    selected: ClassVar[list[int]] = []

    def __init__(self, _ctx: object) -> None:
        pass

    def switch_panel(self, _panel: object) -> None:
        return None

    def get_exercise_rival_status(self) -> _Rivals:
        values = self.statuses.pop(0) if self.statuses else [False] * 5
        return _Rivals(values)

    def select_exercise_rival(self, rival: int) -> None:
        self.selected.append(rival)

    def enter_exercise_battle(self) -> None:
        return None


class _PreparationPage:
    instances: ClassVar[list[_PreparationPage]] = []
    on_preparation_page: ClassVar[bool] = False

    def __init__(self, _ctx: object) -> None:
        self.instances.append(self)
        self.rules = None
        self.events: list[str] = []

    @staticmethod
    def is_current_page(_screen: object) -> bool:
        return _PreparationPage.on_preparation_page

    def select_fleet(self, fleet_id: int) -> None:
        self.events.append(f'fleet:{fleet_id}')

    def change_fleet(
        self,
        fleet_id: int,
        rules: object,
        *,
        on_event: Callable[..., None] | None = None,
    ) -> bool:
        self.events.append(f'change:{fleet_id}')
        self.rules = rules
        if on_event is not None:
            on_event('fleet_validation', passed=True, members=['A'])
            on_event('ship_selected', slot=1, option=rules[0].primary, selected='A')
            on_event('fleet_result', members=['A', None], passed=True)
        return True

    def apply_repair(self, _strategy: object) -> None:
        self.events.append('repair')

    def apply_supply(self) -> None:
        self.events.append('supply')

    @staticmethod
    def detect_ship_damage(_screen: object) -> dict[int, ShipDamageState]:
        return dict.fromkeys(range(6), ShipDamageState.NORMAL)

    def start_battle(self) -> None:
        self.events.append('start')

    def go_back(self) -> None:
        self.events.append('back')


def _ctx() -> SimpleNamespace:
    def screenshot() -> object:
        return object()

    return SimpleNamespace(
        ctrl=SimpleNamespace(screenshot=screenshot),
        config=SimpleNamespace(account=SimpleNamespace(game_app='pkg')),
    )


@pytest.fixture(autouse=True)
def _patch_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    _MapPage.statuses = [[True, False, False, False, False], [False] * 5]
    _MapPage.selected = []
    _PreparationPage.instances = []
    _PreparationPage.on_preparation_page = False
    monkeypatch.setattr(executor_module, 'MapPage', _MapPage)
    monkeypatch.setattr(executor_module, 'BattlePreparationPage', _PreparationPage)
    monkeypatch.setattr(initialize_module, 'initialize', lambda _ctx: None)
    monkeypatch.setattr(executor_module, 'goto_page', lambda *_args: None)
    monkeypatch.setattr(base_module, 'goto_page', lambda *_args: None)
    monkeypatch.setattr(
        executor_module,
        'run_combat',
        lambda *_args, **_kwargs: CombatResult(flag=ConditionFlag.OPERATION_SUCCESS),
    )
    monkeypatch.setattr(executor_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(base_module.time, 'sleep', lambda _seconds: None)


def test_executor_uses_yaml_fleet_and_exercise_combat_plan() -> None:
    events: list[tuple[str, dict]] = []
    request_params = {
        'fleet_id': 2,
        'fleet_presets': [
            {
                'ships': [
                    {'name': 'U-177', 'ship_type': ['ss'], 'min_level': 69},
                ],
            },
        ],
    }
    executor = executor_module.ExerciseExecutor(
        _ctx(),
        request_params,
        on_event=lambda event, **data: events.append((event, data)),
    )

    result = executor.run()

    assert len(result) == 1
    assert _MapPage.selected == [1]
    page = _PreparationPage.instances[0]
    assert page.rules is not None
    assert page.rules[0].primary.name == 'U-177'
    assert page.events[-1] == 'start'
    assert executor.plan.default_node.night is True
    assert [event for event, _data in events] == [
        'panel_ready',
        'rival_confirmed',
        'formation_entered',
        'fleet_validation',
        'ship_selected',
        'fleet_result',
        'fleet_ready',
        'before_start',
        'battle_started',
        'rival_done',
        'panel_ready',
    ]


def test_legacy_entries_are_kept_out_of_executor_module() -> None:
    from autowsgr.business.combat.exercise.compat import ExerciseRunner

    assert ExerciseRunner.__module__.endswith('.compat')
    assert not hasattr(executor_module, 'ExerciseRunner')


def test_ship_selection_checkpoint_honors_pause_and_returns_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pause = threading.Event()
    pause.set()
    page_back = MagicMock()
    monkeypatch.setattr(_PreparationPage, 'go_back', page_back)
    executor = executor_module.ExerciseExecutor(
        _ctx(),
        {'fleet_id': 2, 'fleet_presets': [{'ships': [{'name': 'U-177'}]}]},
        pause=pause,
    )
    executor._prep_active = True

    with pytest.raises(TaskPaused):
        executor._on_fleet_event(
            'ship_selected',
            slot=1,
            option=executor.fleet_selection.slot_rules[0].primary,
            selected='U-177',
        )

    page_back.assert_called_once()
    assert executor._prep_active is False


def test_failure_cleanup_leaves_preparation_page_before_home_navigation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _PreparationPage.on_preparation_page = True
    executor = executor_module.ExerciseExecutor(_ctx(), {'fleet_id': 2})
    home = MagicMock()
    monkeypatch.setattr(executor_module, 'goto_page', home)

    executor._return_home()

    assert _PreparationPage.instances
    page = _PreparationPage.instances[-1]
    assert page.events == ['back']
    home.assert_called_once()


def test_failure_cleanup_uses_known_preparation_state_without_reidentifying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = executor_module.ExerciseExecutor(_ctx(), {'fleet_id': 2})
    executor._prep_active = True
    home = MagicMock()
    monkeypatch.setattr(executor_module, 'goto_page', home)
    page_check = MagicMock(side_effect=AssertionError('不要依赖准备页识别'))
    monkeypatch.setattr(_PreparationPage, 'is_current_page', page_check)

    executor._return_home()

    assert _PreparationPage.instances[-1].events == ['back']
    page_check.assert_not_called()
    home.assert_called_once()
