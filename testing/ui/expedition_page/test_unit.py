"""模块功能：验证远征页面识别、收取流程和页面边界。

上层调用：
- pytest：执行本模块的远征页面治理回归。

下层依赖：
- application.ui.controller.operations.sortie_page.expedition_page：提供页面、识别和操作实现。
- common.device.interaction：提供远征流程使用的导航异常类型。

本模块只使用设备和视觉替身验证页面边界，不连接真实设备或改写业务配置。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import (
    ExpeditionPage,
    constants,
)
from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import (
    page as page_module,
)
from autowsgr.application.ui.controller.operations.sortie_page.expedition_page import (
    recognition as recognition_module,
)
from autowsgr.common.device.interaction import NavigationError


class _Pixel:
    def __init__(self, ready: bool, rgb: tuple[int, int, int]) -> None:
        self._ready = ready
        self._rgb = rgb

    def near(self, _expected: object, _tolerance: float) -> bool:
        return self._ready

    def as_rgb_tuple(self) -> tuple[int, int, int]:
        return self._rgb


def test_recognition_returns_first_ready_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    pixels = iter(
        [
            _Pixel(False, (0, 0, 0)),
            _Pixel(True, constants.READY_COLOR),
        ]
    )
    monkeypatch.setattr(
        recognition_module.PixelChecker,
        'get_pixel',
        lambda *_args: next(pixels),
    )

    assert recognition_module.read_ready_expedition_slot(object()) == 1


def test_page_collects_slot_and_returns_to_map(monkeypatch: pytest.MonkeyPatch) -> None:
    ctrl = MagicMock()
    page = ExpeditionPage(SimpleNamespace(ctrl=ctrl, ocr=None))
    ready_slots = iter([2, None])
    actions: list[tuple[str, object]] = []

    monkeypatch.setattr(
        page_module.recognition,
        'read_ready_expedition_slot',
        lambda _screen: next(ready_slots),
    )
    monkeypatch.setattr(
        page_module.SortiePage,
        'check_expedition_notification',
        staticmethod(lambda _screen: False),
    )
    monkeypatch.setattr(page_module.ImageChecker, 'template_exists', lambda *_args: True)
    monkeypatch.setattr(page_module.time, 'sleep', lambda _seconds: None)
    monkeypatch.setattr(page_module.time, 'monotonic', lambda: 0.0)
    monkeypatch.setattr(
        page_module.operations,
        'click_expedition_slot',
        lambda _ctrl, coordinate: actions.append(('slot', coordinate)),
    )
    monkeypatch.setattr(
        page_module.operations,
        'click_expedition_skip',
        lambda _ctrl: actions.append(('skip', None)),
    )
    monkeypatch.setattr(page_module, 'confirm_operation', lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        page_module,
        'wait_for_page',
        lambda _ctrl, **_kwargs: actions.append(('map', None)),
    )

    assert page.collect_expedition() == 1
    assert actions == [
        ('slot', constants.SLOT_PROBES[2]),
        ('skip', None),
        ('map', None),
    ]


def test_page_stops_when_result_page_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    ctrl = MagicMock()
    page = ExpeditionPage(SimpleNamespace(ctrl=ctrl, ocr=None))
    ctrl.screenshot.return_value = np.zeros((10, 10, 3), dtype=np.uint8)
    actions: list[str] = []
    monotonic_values = iter([0.0, 10.0])

    monkeypatch.setattr(
        page_module.recognition,
        'read_ready_expedition_slot',
        lambda _screen: 0,
    )
    monkeypatch.setattr(page_module.ImageChecker, 'template_exists', lambda *_args: False)
    monkeypatch.setattr(
        page_module,
        'time',
        SimpleNamespace(monotonic=lambda: next(monotonic_values), sleep=lambda _seconds: None),
    )
    monkeypatch.setattr(
        page_module.operations,
        'click_expedition_slot',
        lambda *_args: actions.append('slot'),
    )
    monkeypatch.setattr(
        page_module.operations,
        'click_expedition_skip',
        lambda *_args: actions.append('skip'),
    )

    with pytest.raises(NavigationError, match='远征结算页未出现'):
        page.collect_expedition()

    assert actions == ['slot']


def test_page_fails_when_notification_slot_never_refreshes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl = MagicMock()
    page = ExpeditionPage(SimpleNamespace(ctrl=ctrl, ocr=None))
    ctrl.screenshot.return_value = np.zeros((10, 10, 3), dtype=np.uint8)
    monotonic_values = iter([0.0, 10.0])

    monkeypatch.setattr(
        page_module.recognition,
        'read_ready_expedition_slot',
        lambda _screen: None,
    )
    monkeypatch.setattr(
        page_module.SortiePage,
        'check_expedition_notification',
        staticmethod(lambda _screen: True),
    )
    monkeypatch.setattr(
        page_module,
        'time',
        SimpleNamespace(monotonic=lambda: next(monotonic_values), sleep=lambda _seconds: None),
    )

    with pytest.raises(NavigationError, match='未检测到就绪槽位'):
        page.collect_expedition()

    ctrl.click.assert_not_called()
