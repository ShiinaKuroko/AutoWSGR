"""验证导航器的最短路径、单帧识别和 HOME/MAP 双向链路。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import numpy as np

from autowsgr.application.ui import navigation
from autowsgr.application.ui.controller.home.main_page import constants as home_constants
from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
    constants as sortie_constants,
)
from autowsgr.application.ui.navigation import service
from autowsgr.application.ui.navigation.page_checker import registry as page_checker_registry
from autowsgr.application.ui.navigation.page_checker.registry import PageCheckerRegistry
from autowsgr.application.ui.navigation.route_calculator import calculate_route
from autowsgr.application.ui.navigation.route_registry import (
    create_default_registry as create_route_registry,
)
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.recognition_flow import RecognitionResult
from autowsgr.dispatch.context import ContextTemplate, context


if TYPE_CHECKING:
    import pytest


def _bind_context(task_id: str) -> Any:
    return context.bind(task_id, template=ContextTemplate.for_task('navigation'))


def _stub_recognition(
    monkeypatch: pytest.MonkeyPatch,
    pages: tuple[PageName, ...],
) -> list[tuple[object, object, int, float]]:
    calls: list[tuple[object, object, int, float]] = []
    page_iter = iter(pages)
    frame = np.zeros((1, 1, 3), dtype=np.uint8)

    def recognize(
        ctrl: object,
        _recognizer: object,
        *,
        record_screenshot: object,
        attempts: int,
        interval_seconds: float,
    ) -> RecognitionResult[PageName]:
        calls.append((ctrl, record_screenshot, attempts, interval_seconds))
        return RecognitionResult(True, True, next(page_iter), frame, len(calls))

    monkeypatch.setattr(service.recognition_flow, 'recognize_with_retry', recognize)
    return calls


def test_default_registry_contains_only_home_map_round_trip() -> None:
    registry = create_route_registry()
    routes = tuple(route for page in PageName for route in registry.outgoing(page))

    assert [(route.source, route.target) for route in routes] == [
        (PageName.HOME, PageName.MAP),
        (PageName.MAP, PageName.HOME),
    ]
    assert calculate_route(PageName.HOME, PageName.MAP, registry) == registry.outgoing(
        PageName.HOME,
    )
    assert calculate_route(PageName.MAP, PageName.HOME, registry) == registry.outgoing(
        PageName.MAP,
    )


def test_default_page_checker_registry_contains_only_home_and_map() -> None:
    registry = page_checker_registry.create_default_registry()

    assert set(registry._checkers) == {PageName.HOME, PageName.MAP}


def test_page_checker_registry_passes_one_frame_to_the_checker() -> None:
    received: list[object] = []
    registry = PageCheckerRegistry(
        {PageName.HOME: lambda screen: received.append(screen) or True},
    )
    screen = object()

    assert registry.identify(screen) is PageName.HOME
    assert received == [screen]


def test_goto_page_skips_route_when_current_page_is_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = SimpleNamespace(ctrl=SimpleNamespace(), record_screenshot=MagicMock())
    calls = _stub_recognition(monkeypatch, (PageName.HOME,))

    with _bind_context('navigation-same-page-test'):
        result = navigation.goto_page(ctx, PageName.HOME)

    assert result.skipped is True
    assert result.route == ()
    assert len(calls) == 1


def test_goto_home_to_map_is_one_click_and_one_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl = SimpleNamespace(click=MagicMock())
    ctx = SimpleNamespace(ctrl=ctrl, record_screenshot=MagicMock())
    calls = _stub_recognition(monkeypatch, (PageName.HOME, PageName.MAP))

    with _bind_context('navigation-home-map-test'):
        result = navigation.goto_page(ctx, PageName.MAP, attempts=4, interval_seconds=0.2)

    ctrl.click.assert_called_once_with(*home_constants.NAV_POSITIONS['sortie'])
    assert result.route == (PageName.MAP,)
    assert result.confirmed is True
    assert len(calls) == 2
    assert all(call[2:] == (4, 0.2) for call in calls)


def test_goto_map_to_home_is_one_click_and_one_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl = SimpleNamespace(click=MagicMock())
    ctx = SimpleNamespace(ctrl=ctrl, record_screenshot=MagicMock())
    calls = _stub_recognition(monkeypatch, (PageName.MAP, PageName.HOME))

    with _bind_context('navigation-map-home-test'):
        result = navigation.goto_page(ctx, PageName.HOME, attempts=5, interval_seconds=0.25)

    ctrl.click.assert_called_once_with(*sortie_constants.CLICK_BACK)
    assert result.route == (PageName.HOME,)
    assert result.confirmed is True
    assert len(calls) == 2
    assert all(call[2:] == (5, 0.25) for call in calls)
