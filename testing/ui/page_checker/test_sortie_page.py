"""验证出征页面 checker 的单帧识别契约。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import numpy as np

from autowsgr.application.ui.navigation.page_checker import sortie


if TYPE_CHECKING:
    import pytest


def test_sortie_checker_requires_active_and_inactive_tabs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """出征页必须同时命中出征 active tab 和其余四个 inactive tab。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    loaded: list[str] = []
    matched: list[object] = []
    rois = []

    def load_image(path: str) -> np.ndarray:
        loaded.append(path)
        return screen[:10, :10]

    def match_template(*args: object, **kwargs: object) -> SimpleNamespace:
        matched.append(args[0])
        rois.append(kwargs['roi'])
        return SimpleNamespace(matched=True)

    monkeypatch.setattr(sortie.vision.opencv, 'load_image', load_image)
    monkeypatch.setattr(sortie.vision, 'match_template', match_template)

    assert sortie.check_sortie_page(screen) is True

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


def test_sortie_checker_stops_on_unmatched_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    """任一 tab 模板未命中时返回 False。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    results = iter((True, False))

    monkeypatch.setattr(sortie.vision.opencv, 'load_image', lambda _path: screen[:10, :10])
    monkeypatch.setattr(
        sortie.vision,
        'match_template',
        lambda *_args, **_kwargs: SimpleNamespace(matched=next(results)),
    )

    assert sortie.check_sortie_page(screen) is False
