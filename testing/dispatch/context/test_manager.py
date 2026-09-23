"""Contract tests for the dispatch-owned task context."""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.dispatch.context import (
    ContextClosedError,
    ContextManager,
    ContextNotBoundError,
    ContextTemplate,
)


def test_context_is_lazy_and_keeps_navigation_facts() -> None:
    manager = ContextManager()
    template = ContextTemplate.for_task('navigation_checker')
    screen = np.zeros((2, 3, 3), dtype=np.uint8)

    with manager.bind('task-1', template=template):
        first = manager.request()
        second = manager.request()

        assert first.task_id == second.task_id == 'task-1'
        assert first.task_type == 'navigation_checker'

        first.record_screenshot(screen)
        first.set_current_page('首页')
        first.set_target_page('首页')
        first.record_route_step(0)

        assert np.array_equal(second.read_latest_screenshot(), screen)
        assert second.read_current_page() == '首页'
        assert second.read_target_page() == '首页'

        result = object()
        first.record_result(result)
        assert second.read_result() is result

        manager.close()
        with pytest.raises(ContextClosedError):
            first.read_current_page()


def test_context_requires_a_bound_scope() -> None:
    with pytest.raises(ContextNotBoundError):
        ContextManager().request()


def test_context_state_does_not_cross_task_scopes() -> None:
    manager = ContextManager()
    template = ContextTemplate.for_task('navigation_checker')

    with manager.bind('task-a', template=template):
        manager.request().set_current_page('首页')

    with manager.bind('task-b', template=template):
        assert manager.request().read_current_page() is None
