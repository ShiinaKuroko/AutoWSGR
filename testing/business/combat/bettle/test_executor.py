"""普通出征和活动战统一入口回归。"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import TYPE_CHECKING

import autowsgr.business.combat.bettle.executor as executor_module
from autowsgr.business.combat.bettle import BettleExecutor
from autowsgr.dispatch.registry import build_executor


if TYPE_CHECKING:
    import pytest

    from autowsgr.application.combat.history import CombatResult


def test_bettle_task_types_share_one_executor() -> None:
    """普通出征和活动战由同一个业务入口承接。"""
    normal = build_executor('normal_fight', SimpleNamespace(), {'chapter': 1})
    event = build_executor(
        'event_fight',
        SimpleNamespace(),
        {'event': '20260730', 'chapter': 'H', 'map': '1a'},
    )

    assert isinstance(normal, BettleExecutor)
    assert isinstance(event, BettleExecutor)
    assert normal.task_type == 'normal_fight'
    assert event.task_type == 'event_fight'


def test_bettle_executor_passes_task_type_to_shared_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """执行器把任务类型传给共享 Runner，选择对应导航模式。"""
    initialized: list[object] = []
    navigated: list[object] = []
    runner_args: dict[str, object] = {}
    events: list[tuple[str, dict[str, object]]] = []
    initialize_module = importlib.import_module(
        'autowsgr.application.runtime.initialize.initialize',
    )

    class Runner:
        def __init__(self, _ctx: object, _plan: object, **kwargs: object) -> None:
            runner_args.update(kwargs)

        def run(self) -> CombatResult:
            from autowsgr.application.combat.history import CombatResult
            from autowsgr.common.types import ConditionFlag

            return CombatResult(flag=ConditionFlag.OPERATION_SUCCESS)

    monkeypatch.setattr(initialize_module, 'initialize', initialized.append)
    monkeypatch.setattr(executor_module, 'NormalFightRunner', Runner)
    monkeypatch.setattr(executor_module, 'goto_page', lambda _ctx, page: navigated.append(page))

    executor = BettleExecutor(
        SimpleNamespace(),
        {'chapter': 'H', 'map': '1a', 'event': '20260730'},
        task_type='event_fight',
        on_event=lambda event, **data: events.append((event, data)),
    )
    result = executor.run()

    assert result.flag.value == 'success'
    assert initialized == [executor.ctx]
    assert runner_args['task_type'] == 'event_fight'
    assert callable(runner_args['wait'])
    repair_status_callback = runner_args['repair_status_callback']
    assert callable(repair_status_callback)
    repair_status_callback(True)
    repair_status_callback(False)
    assert events[-2:] == [
        ('repairing', {'repairing': True}),
        ('repairing', {'repairing': False}),
    ]
    assert navigated
