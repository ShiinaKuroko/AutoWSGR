"""决战业务入口回归。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import autowsgr.business.combat.decisive.executor as executor_module
from autowsgr.business.combat.decisive import DecisiveExecutor, DecisiveResult
from autowsgr.business.combat.decisive.executor import DecisiveController
from autowsgr.business.combat.decisive.state import DecisiveState
from autowsgr.common.types import DecisivePhase
from autowsgr.dispatch.registry import build_executor


def test_decisive_is_registered_in_business_registry() -> None:
    """Processor registry resolves the business decisive executor."""
    executor = build_executor('decisive', SimpleNamespace(), {'chapter': 6})

    assert isinstance(executor, DecisiveExecutor)


def test_decisive_executor_delegates_one_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """The new entry delegates one task item to the migrated state machine."""

    class Controller:
        def __init__(self, _ctx: object, _config: object) -> None:
            pass

        def run(self, *, full_recovery_check: bool = False) -> DecisiveResult:
            del full_recovery_check
            return DecisiveResult.CHAPTER_CLEAR

    monkeypatch.setattr(executor_module, 'DecisiveController', Controller)
    executor = DecisiveExecutor(SimpleNamespace(), {'chapter': 6})

    assert executor.run() is DecisiveResult.CHAPTER_CLEAR


def test_decisive_executor_recovers_transient_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    modes: list[bool] = []
    recoveries: list[int] = []

    class Controller:
        def __init__(self, _ctx: object, _config: object) -> None:
            pass

        def run(self, *, full_recovery_check: bool = False) -> DecisiveResult:
            nonlocal calls
            calls += 1
            modes.append(full_recovery_check)
            return DecisiveResult.ERROR if calls < 3 else DecisiveResult.CHAPTER_CLEAR

    monkeypatch.setattr(executor_module, 'DecisiveController', Controller)
    monkeypatch.setattr(
        executor_module,
        '_recover_decisive_after_error',
        lambda _ctx, attempt: recoveries.append(attempt),
    )
    executor = DecisiveExecutor(SimpleNamespace(), {'chapter': 6})

    assert executor.run() is DecisiveResult.CHAPTER_CLEAR
    assert calls == 3
    assert modes == [False, True, True]
    assert recoveries == [1, 2]


def test_decisive_executor_stops_after_recovery_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    recoveries: list[int] = []

    class Controller:
        def __init__(self, _ctx: object, _config: object) -> None:
            pass

        def run(self, *, full_recovery_check: bool = False) -> DecisiveResult:
            del full_recovery_check
            nonlocal calls
            calls += 1
            return DecisiveResult.ERROR

    monkeypatch.setattr(executor_module, 'DecisiveController', Controller)
    monkeypatch.setattr(
        executor_module,
        '_recover_decisive_after_error',
        lambda _ctx, attempt: recoveries.append(attempt),
    )
    executor = DecisiveExecutor(SimpleNamespace(), {'chapter': 6})

    assert executor.run() is DecisiveResult.ERROR
    assert calls == 3
    assert recoveries == [1, 2]


def test_decisive_controller_reports_entry_failure_for_executor_recovery() -> None:
    controller = object.__new__(DecisiveController)
    controller._config = SimpleNamespace(chapter=6)
    controller._state = SimpleNamespace(
        reset=MagicMock(),
        phase=DecisivePhase.INIT,
    )
    controller._prepare_entry_state = MagicMock(side_effect=RuntimeError('entry unavailable'))

    assert controller.run() is DecisiveResult.ERROR
    assert controller._state.phase is DecisivePhase.FINISHED


def test_decisive_retreat_resets_controller_flags() -> None:
    controller = object.__new__(DecisiveController)
    controller._state = DecisiveState(
        chapter=6,
        stage=1,
        node='B',
        phase=DecisivePhase.RETREAT,
    )
    controller._has_chosen_fleet = True
    controller._resume_mode = False
    controller._use_last_fleet_attempts = 2
    controller._skip_advance_choice = True
    controller._fleet_overlay_enabled = False
    controller._force_fleet_scan = True
    controller._full_recovery_check = True
    controller._wait_deadline = 100.0
    controller._advance_source_node = 'B'
    controller._execute_retreat = MagicMock()
    controller._handle_enter_map = lambda: setattr(
        controller._state,
        'phase',
        DecisivePhase.FINISHED,
    )

    controller._main_loop()

    assert controller._state.stage == 0
    assert controller._state.node == 'U'
    assert controller._has_chosen_fleet is False
    assert controller._resume_mode is True
    assert controller._use_last_fleet_attempts == 0
    assert controller._skip_advance_choice is False
    assert controller._fleet_overlay_enabled is True
    assert controller._force_fleet_scan is False
    assert controller._full_recovery_check is False
    assert controller._wait_deadline == 0.0
    assert controller._advance_source_node is None
