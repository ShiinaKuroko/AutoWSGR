"""模块功能：验证出征页域探针的判层契约。

直接调用方：项目测试运行器。

直接依赖：pytest、checker.sortie 与 vision 识别入口。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from autowsgr.application.ui.navigation.checker.sortie import checker as sortie_checker
from autowsgr.application.ui.navigation.checker.sortie import read_sortie_tab_layer


if TYPE_CHECKING:
    from autowsgr.application.ui.navigation.types import PageName


_LAYERS = sortie_checker._TAB_LAYERS
_PAGES = tuple(page for page, _, _ in _LAYERS)


def _install_recognition(monkeypatch: pytest.MonkeyPatch, *, active_index: int | None) -> list:
    """用替身接管识别入口：只有指定位置的模板算命中，并记录调用参数。"""
    calls: list[dict[str, object]] = []

    def expect_template(_ctx: object, **options: object) -> SimpleNamespace:
        calls.append(options)
        templates = options['template']
        observation = [
            SimpleNamespace(matched=(index == active_index)) for index in range(len(templates))
        ]
        return SimpleNamespace(satisfied=active_index is not None, observation=observation)

    monkeypatch.setattr(sortie_checker, 'expect_template', expect_template)
    return calls


@pytest.mark.parametrize(('active_index', 'expected'), tuple(enumerate(_PAGES)))
def test_report_active_tab(
    monkeypatch: pytest.MonkeyPatch,
    active_index: int,
    expected: PageName,
) -> None:
    """激活哪个标签就返回哪个页面。"""
    _install_recognition(monkeypatch, active_index=active_index)

    assert read_sortie_tab_layer(object()) is expected


def test_report_no_tab(monkeypatch: pytest.MonkeyPatch) -> None:
    """没有任何标签激活时返回 None。"""
    _install_recognition(monkeypatch, active_index=None)

    assert read_sortie_tab_layer(object()) is None


def test_read_all_tabs_in_one_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """五个标签共用一次截图：一次调用传齐模板与区域。"""
    calls = _install_recognition(monkeypatch, active_index=0)

    read_sortie_tab_layer(object())

    assert len(calls) == 1
    assert len(calls[0]['template']) == len(_LAYERS)
    assert len(calls[0]['roi']) == len(_LAYERS)
