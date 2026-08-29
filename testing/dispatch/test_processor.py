"""Processor contract checks for the first YAML-driven vertical slice."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import autowsgr.dispatch.processor as processor_module
from autowsgr.dispatch import (
    MAX_PRIORITY,
    TASK_PRIORITIES,
    Processor,
    Request,
    TaskPaused,
    TaskStopped,
    priority_for,
)


if TYPE_CHECKING:
    from pathlib import Path


class _Executor:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    def run(self) -> Any:
        if self.error is not None:
            raise self.error
        return self.result


def test_priority_policy_is_bounded_and_ordered() -> None:
    values = [priority_for(name) for name in TASK_PRIORITIES]

    assert max(values) <= MAX_PRIORITY
    assert priority_for('expedition_check') > priority_for('reward_check')
    assert priority_for('reward_check') > priority_for('campaign')
    assert priority_for('campaign') > priority_for('exercise')
    assert priority_for('exercise') > priority_for('decisive')
    assert priority_for('decisive') > priority_for('normal_fight')
    assert priority_for('normal_fight') == priority_for('event_fight')
    assert priority_for('unknown') == 0


@pytest.mark.parametrize(
    'kwargs',
    [
        {'task_type': 1},
        {'task_type': 'exercise', 'count': True},
        {'task_type': 'exercise', 'count': 0},
        {'task_type': 'exercise', 'priority': MAX_PRIORITY + 1},
        {'task_type': 'exercise', 'extre': 1},
    ],
)
def test_request_rejects_invalid_admission_values(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r'.+'):
        Request(**kwargs)


def test_request_rejects_non_mapping_params() -> None:
    with pytest.raises(ValueError, match='params'):
        Request(task_type='exercise', params=[('fleet_id', 2)])  # type: ignore[arg-type]


def test_request_from_yaml_drops_only_legacy_single_times(tmp_path: Path) -> None:
    path = tmp_path / 'exercise.yaml'
    path.write_text('task_type: exercise\nfleet_id: 2\ntimes: 1\n', encoding='utf-8')

    request = Request.from_yaml(path, source='gui', count=3)

    assert request.task_type == 'exercise'
    assert request.count == 3
    assert request.params == {'fleet_id': 2}
    with pytest.raises(TypeError):
        request.params['fleet_id'] = 1  # type: ignore[index]

    path.write_text('task_type: exercise\nfleet_id: 2\ntimes: 2\n', encoding='utf-8')
    with pytest.raises(ValueError, match='times'):
        Request.from_yaml(path)


def test_request_from_yaml_reports_syntax_errors(tmp_path: Path) -> None:
    path = tmp_path / 'broken.yaml'
    path.write_text('task_type: [', encoding='utf-8')

    with pytest.raises(ValueError, match='解析失败'):
        Request.from_yaml(path)


def test_processor_orders_requests_and_expands_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def build(task_type: str, *_args: Any, **_kwargs: Any) -> _Executor:
        calls.append(task_type)
        return _Executor(result=task_type)

    monkeypatch.setattr(processor_module, 'build_executor', build)
    processor = Processor(SimpleNamespace())
    repeated = Request(task_type='normal_fight', count=2)
    processor.submit(repeated)
    processor.submit(Request(task_type='exercise'))
    processor.submit(Request(task_type='reward_check'))

    outcomes = processor.run_pending()

    assert [request.task_type for _status, request, _result in outcomes] == [
        'reward_check',
        'exercise',
        'normal_fight',
        'normal_fight',
    ]
    assert [status for status, _request, _result in outcomes] == ['done'] * 4
    assert calls == ['reward_check', 'exercise', 'normal_fight', 'normal_fight']
    assert repeated.progress['_completed'] == 2


def test_interrupt_requeues_paused_request_before_continuing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fired = False
    calls: list[str] = []
    processor: Processor

    def on_event(event: str, **_data: Any) -> None:
        nonlocal fired
        if event == 'checkpoint' and not fired:
            fired = True
            processor.interrupt(Request(task_type='expedition_check'))

    def build(task_type: str, _ctx: Any, _params: Any, **kwargs: Any) -> _Executor:
        calls.append(task_type)
        if task_type == 'exercise' and calls.count('exercise') == 1:
            kwargs['on_event']('checkpoint')
            return _Executor(error=TaskPaused())
        return _Executor(result=task_type)

    monkeypatch.setattr(processor_module, 'build_executor', build)
    processor = Processor(SimpleNamespace(), on_event=on_event)
    request = Request(task_type='exercise')
    processor.submit(request)

    outcomes = processor.run_pending()

    assert [(status, item.task_type) for status, item, _result in outcomes] == [
        ('paused', 'exercise'),
        ('done', 'expedition_check'),
        ('done', 'exercise'),
    ]


def test_interrupt_at_max_priority_keeps_insertion_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    processor: Processor

    def build(task_type: str, *_args: Any, **_kwargs: Any) -> _Executor:
        calls.append(task_type)
        if task_type == 'normal_fight' and calls.count(task_type) == 1:
            processor.interrupt(Request(task_type='expedition_check', priority=MAX_PRIORITY))
            return _Executor(error=TaskPaused())
        return _Executor(result=task_type)

    monkeypatch.setattr(processor_module, 'build_executor', build)
    processor = Processor(SimpleNamespace())
    request = Request(task_type='normal_fight', priority=MAX_PRIORITY)
    processor.submit(request)

    outcomes = processor.run_pending()

    assert [item.task_type for _status, item, _result in outcomes] == [
        'normal_fight',
        'expedition_check',
        'normal_fight',
    ]
    assert all(item.priority <= MAX_PRIORITY for _status, item, _result in outcomes)


def test_processor_retries_soft_then_hard_and_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    recoveries: list[str] = []
    events: list[tuple[str, dict[str, Any]]] = []

    def build(*_args: Any, **_kwargs: Any) -> _Executor:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return _Executor(error=RuntimeError(f'failure-{attempts}'))
        return _Executor(result='ok')

    monkeypatch.setattr(processor_module, 'build_executor', build)
    processor = Processor(
        SimpleNamespace(),
        on_event=lambda event, **data: events.append((event, data)),
        recover=lambda: recoveries.append('recovered'),
        soft_retries=1,
        hard_retries=1,
    )
    processor.submit(Request(task_type='exercise'))

    outcomes = processor.run_pending()

    assert outcomes[0][0] == 'done'
    assert attempts == 3
    assert recoveries == ['recovered']
    assert [(data['mode'], data['attempt']) for event, data in events if event == 'retry'] == [
        ('soft', 1),
        ('hard', 1),
    ]


def test_processor_stop_does_not_construct_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stop = threading.Event()
    stop.set()
    build = MagicMock()
    monkeypatch.setattr(processor_module, 'build_executor', build)
    processor = Processor(SimpleNamespace(), stop=stop)
    request = Request(task_type='exercise')
    processor.submit(request)

    outcomes = processor.run_pending()

    assert [(status, item) for status, item, _result in outcomes] == [('stopped', request)]
    build.assert_not_called()


def test_task_stopped_exception_is_a_terminal_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        processor_module,
        'build_executor',
        lambda *_args, **_kwargs: _Executor(error=TaskStopped()),
    )
    processor = Processor(SimpleNamespace())
    request = Request(task_type='exercise')
    processor.submit(request)

    outcomes = processor.run_pending()

    assert outcomes[0][0] == 'stopped'
