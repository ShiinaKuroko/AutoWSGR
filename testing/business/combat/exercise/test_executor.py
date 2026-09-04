"""演习执行器主链路的无设备静态回归。"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar
from unittest.mock import MagicMock

import pytest

import autowsgr.application.runtime.executor as base_module
import autowsgr.application.runtime.initialize.initialize as initialize_module
import autowsgr.business.combat.exercise.executor as executor_module
import autowsgr.business.combat.exercise.operations as operations_module
from autowsgr.business.combat import CombatResult
from autowsgr.common.types import ConditionFlag, PageName, ShipDamageState
from autowsgr.dispatch import TaskPaused


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
        self.task_type = None
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
        task_type: str = 'normal',
        on_event: Callable[..., None] | None = None,
    ) -> bool:
        self.events.append(f'change:{fleet_id}')
        self.task_type = task_type
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

    def try_start_battle(self, *, target: str) -> bool:
        self.events.append(f'start:{target}')
        return True

    def go_back(self) -> None:
        self.events.append('back')


def _ctx() -> SimpleNamespace:
    def screenshot() -> object:
        return object()

    return SimpleNamespace(
        ctrl=SimpleNamespace(screenshot=screenshot),
        ocr=None,
        config=SimpleNamespace(account=SimpleNamespace(game_app='pkg')),
    )


@pytest.fixture(autouse=True)
def _patch_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    _MapPage.statuses = [[True, False, False, False, False], [False] * 5]
    _MapPage.selected = []
    _PreparationPage.instances = []
    _PreparationPage.on_preparation_page = False
    monkeypatch.setattr(operations_module, 'MapPage', _MapPage)
    monkeypatch.setattr(operations_module, 'BattlePreparationPage', _PreparationPage)
    monkeypatch.setattr(executor_module, 'goto_page', MagicMock())
    monkeypatch.setattr(initialize_module, 'initialize', lambda _ctx: None)
    monkeypatch.setattr(base_module, 'goto_page', MagicMock())
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
    assert page.task_type == 'exercise'
    assert page.rules is not None
    assert page.rules[0].primary.name == 'U-177'
    assert page.events[-1] == 'start:exercise combat'
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


def test_ship_selection_checkpoint_honors_pause_and_returns_home() -> None:
    pause = threading.Event()
    pause.set()
    executor = executor_module.ExerciseExecutor(
        _ctx(),
        {'fleet_id': 2, 'fleet_presets': [{'ships': [{'name': 'U-177'}]}]},
        pause=pause,
    )

    with pytest.raises(TaskPaused):
        executor._operations._on_fleet_event(
            'ship_selected',
            slot=1,
            option=executor.fleet_selection.slot_rules[0].primary,
            selected='U-177',
        )

    base_module.goto_page.assert_called_once()


def test_failure_cleanup_uses_shared_navigation_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = executor_module.ExerciseExecutor(_ctx(), {'fleet_id': 2})
    home = MagicMock()

    def fail(_ctx: object) -> None:
        raise RuntimeError('boom')

    monkeypatch.setattr(executor_module, 'goto_page', home)
    monkeypatch.setattr(initialize_module, 'initialize', fail)

    with pytest.raises(RuntimeError, match='boom'):
        executor.run()

    home.assert_called_once_with(executor.ctx, PageName.MAIN)


def test_pause_after_battle_keeps_completed_result() -> None:
    progress: dict[str, object] = {}
    pause = threading.Event()

    def pause_after_result(event: str, **_data: object) -> None:
        if event == 'rival_done':
            pause.set()

    _MapPage.statuses = [[True, False, False, False, False]]
    first = executor_module.ExerciseExecutor(
        _ctx(),
        {'fleet_id': 2, 'rivals_limit': 1},
        pause=pause,
        progress=progress,
        on_event=pause_after_result,
    )
    with pytest.raises(TaskPaused):
        first.run()

    pause.clear()
    _MapPage.statuses = [[False] * 5]
    resumed = executor_module.ExerciseExecutor(
        _ctx(),
        {'fleet_id': 2, 'rivals_limit': 1},
        pause=pause,
        progress=progress,
    )

    assert len(resumed.run()) == 1
    assert '_results' not in progress
