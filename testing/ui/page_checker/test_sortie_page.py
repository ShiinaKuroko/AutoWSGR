"""验证出征页面 checker 的单帧识别契约。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np

from autowsgr.application.ui.navigation.page_checker import sortie
from autowsgr.dispatch.context import ContextManager, ContextTemplate


if TYPE_CHECKING:
    import pytest


def test_sortie_checker_saves_screenshot_before_template_matching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """截图先写入 Context，再逐个匹配出征页标签模板。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    manager = ContextManager()
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=screen))
    loaded: list[str] = []
    matched: list[object] = []
    events: list[str] = []
    rois: list[object] = []
    match_results = iter((True, True, True, False, False))

    def load_image(path: str) -> np.ndarray:
        loaded.append(path)
        return screen[:10, :10]

    def match_template(*args: object, **kwargs: object) -> SimpleNamespace:
        events.append('match')
        matched.append(args[0])
        rois.append(kwargs['roi'])
        return SimpleNamespace(matched=next(match_results))

    monkeypatch.setattr(sortie.vision.opencv, 'load_image', load_image)
    monkeypatch.setattr(sortie.vision, 'match_template', match_template)

    with manager.bind('sortie-checker-success', template=ContextTemplate.for_task('navigation')):
        ctx = manager.request()

        def record_screenshot(frame: np.ndarray) -> None:
            events.append('record')
            ctx.record_screenshot(frame)

        assert sortie.check_sortie_page(ctrl, record_screenshot=record_screenshot) is True
        assert events == ['record'] + ['match'] * 5
        assert np.array_equal(ctx.read_latest_screenshot(), screen)
        assert ctx.read_current_page() is None

    assert ctrl.screenshot.call_count == 1
    assert len(loaded) == 5
    assert len(matched) == 5
    assert matched == [screen] * 5
    assert all(path.startswith('application/ui/navigation/page_checker/SORTIE/') for path in loaded)
    assert [roi.to_absolute(1280, 720) for roi in rois] == [
        (197, 12, 276, 53),
        (358, 11, 441, 55),
        (522, 10, 607, 56),
        (687, 10, 770, 56),
        (852, 12, 940, 55),
    ]


def test_sortie_checker_retries_unmatched_frames_then_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """出征页模板未命中时使用共享识别流程重试并返回 False。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    manager = ContextManager()
    ctrl = SimpleNamespace(screenshot=MagicMock(return_value=screen))
    matches = iter((True, True, False, False, False) * 3)
    matched_frames: list[object] = []

    monkeypatch.setattr(sortie.vision.opencv, 'load_image', lambda _path: screen[:10, :10])
    monkeypatch.setattr(sortie.recognition_flow.time, 'sleep', lambda _seconds: None)

    def match_template(*args: object, **_kwargs: object) -> SimpleNamespace:
        matched_frames.append(args[0])
        return SimpleNamespace(matched=next(matches))

    monkeypatch.setattr(sortie.vision, 'match_template', match_template)

    with manager.bind('sortie-checker-failure', template=ContextTemplate.for_task('navigation')):
        ctx = manager.request()
        assert (
            sortie.check_sortie_page(
                ctrl,
                record_screenshot=ctx.record_screenshot,
            )
            is False
        )
        assert np.array_equal(ctx.read_latest_screenshot(), screen)
        assert ctx.read_current_page() is None

    assert ctrl.screenshot.call_count == 3
    assert matched_frames == [screen] * 15
