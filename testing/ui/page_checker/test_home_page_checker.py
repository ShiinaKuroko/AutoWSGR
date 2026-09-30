"""验证主页 checker 的截图、浮窗和模板识别顺序。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import numpy as np

from autowsgr.application.ui.navigation.page_checker import home
from autowsgr.dispatch.context import (
    ContextHandle,
    ContextManager,
    ContextTemplate,
    RuntimeBindings,
)


if TYPE_CHECKING:
    import pytest


def test_home_checker_captures_cleans_and_retries_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """先记录截图并处理浮窗，再通过公共重试流程识别主页模板。"""
    initial = np.zeros((720, 1280, 3), dtype=np.uint8)
    unmatched = np.ones((720, 1280, 3), dtype=np.uint8)
    matched = np.full((720, 1280, 3), 2, dtype=np.uint8)
    template_image = np.zeros((10, 10, 3), dtype=np.uint8)
    labels = {id(initial): 'initial', id(unmatched): 'unmatched', id(matched): 'matched'}
    frames = iter((initial, unmatched, matched))
    events: list[str] = []

    def screenshot() -> np.ndarray:
        frame = next(frames)
        events.append(f'screenshot:{labels[id(frame)]}')
        return frame

    class StubHomePage:
        def __init__(self, _ctx: object) -> None:
            pass

        def dismiss_current_overlay(self, *, navigation_context: ContextHandle) -> None:
            assert isinstance(navigation_context, ContextHandle)
            events.append('dismiss_overlay')

    def load_image(path: str) -> np.ndarray:
        events.append('load_template')
        assert path == 'application/ui/navigation/page_checker/HOME/HOME_MAIN_720P.png'
        return template_image

    def match_template(
        screen: np.ndarray,
        _template: object,
        *,
        roi: object,
        confidence: float,
    ) -> SimpleNamespace:
        assert roi == home._HOME_PAGE_ROI
        assert confidence == home._HOME_PAGE_CONFIDENCE
        events.append(f'match:{labels[id(screen)]}')
        return SimpleNamespace(matched=screen is matched)

    def sleep(seconds: float) -> None:
        events.append(f'sleep:{seconds}')

    monkeypatch.setattr(home, 'HomePage', StubHomePage)
    monkeypatch.setattr(home.vision.opencv, 'load_image', load_image)
    monkeypatch.setattr(home.vision, 'match_template', match_template)
    monkeypatch.setattr(home.recognition_flow.time, 'sleep', sleep)
    manager = ContextManager()
    runtime = RuntimeBindings(
        ctrl=SimpleNamespace(screenshot=screenshot),
        config=None,
        ocr=None,
        ship_ocr=None,
    )

    with manager.bind(
        'home-checker-test',
        template=ContextTemplate.for_task('navigation'),
        runtime=runtime,
    ):
        dispatch_context = manager.request()
        assert home.check_home_page(dispatch_context) is True
        assert np.array_equal(dispatch_context.read_latest_screenshot(), matched)
        assert dispatch_context.read_current_page() is None

    assert events == [
        'screenshot:initial',
        'dismiss_overlay',
        'load_template',
        'screenshot:unmatched',
        'match:unmatched',
        'sleep:0.5',
        'screenshot:matched',
        'match:matched',
    ]
