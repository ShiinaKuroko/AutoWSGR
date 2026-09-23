"""验证主页 checker 的单帧识别契约。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import numpy as np

from autowsgr.application.ui.navigation.page_checker import home


if TYPE_CHECKING:
    import pytest


def test_home_checker_matches_the_given_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """checker 只使用调用方传入的截图执行一次模板匹配。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)
    loaded: list[str] = []
    matched: list[object] = []

    def load_image(path: str) -> np.ndarray:
        loaded.append(path)
        return screen[:10, :10]

    def match_template(*args: object, **_kwargs: object) -> SimpleNamespace:
        matched.append(args[0])
        return SimpleNamespace(matched=True)

    monkeypatch.setattr(home.vision.opencv, 'load_image', load_image)
    monkeypatch.setattr(home.vision, 'match_template', match_template)

    assert home.check_home_page(screen) is True
    assert loaded == ['application/ui/navigation/page_checker/HOME/HOME_MAIN_720P.png']
    assert matched == [screen]


def test_home_checker_returns_false_for_an_unmatched_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """模板未命中时 checker 直接返回 False。"""
    screen = np.zeros((720, 1280, 3), dtype=np.uint8)

    monkeypatch.setattr(home.vision.opencv, 'load_image', lambda _path: screen[:10, :10])
    monkeypatch.setattr(
        home.vision,
        'match_template',
        lambda *_args, **_kwargs: SimpleNamespace(matched=False),
    )

    assert home.check_home_page(screen) is False
