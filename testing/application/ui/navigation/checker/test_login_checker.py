"""模块功能：验证登录 checker 的画面判断与参数传递。

直接调用方：项目测试运行器。

直接依赖：pytest、login 的 checker 与 vision 识别入口。

边界：用替身接管识别函数，不连接设备、不识别画面。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autowsgr.application.ui.navigation.checker.login import checker


# 导航确认入口有自己的默认节奏（等弹层动画），其余入口保持单帧。
_NAV_CONFIRM_ENTRIES = {'check_login_page', 'check_server_select'}

_SCREEN_ENTRIES = [
    ('check_black_screen', 'expect_template'),
    ('check_update_prompt', 'expect_ocr'),
    ('check_loading', 'expect_ocr'),
    ('check_login_page', 'expect_template'),
    ('check_server_select', 'expect_template'),
]


def _capture(monkeypatch: pytest.MonkeyPatch, attr: str) -> dict[str, Any]:
    """用替身接管识别入口并记录调用参数。"""
    captured: dict[str, Any] = {}

    def fake(_ctx: object, *args: object, **options: object) -> SimpleNamespace:
        captured['args'] = args
        captured['options'] = options
        return SimpleNamespace(satisfied=True)

    monkeypatch.setattr(checker, attr, fake)
    return captured


@pytest.mark.parametrize(('entry', 'target'), _SCREEN_ENTRIES)
def test_check_entry_passes_options_to_vision(
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    target: str,
) -> None:
    """五个画面入口把识别模式与节奏传给能力层。"""
    captured = _capture(monkeypatch, target)

    result = getattr(checker, entry)(
        object(),
        absent=True,
        attempts=120,
        interval_seconds=1.0,
    )

    assert result is True
    options = captured['options']
    assert options['absent'] is True
    assert options['attempts'] == 120
    assert options['interval_seconds'] == 1.0


@pytest.mark.parametrize(('entry', 'target'), _SCREEN_ENTRIES)
def test_check_entry_defaults(
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    target: str,
) -> None:
    """不传参数时按各入口自己的默认节奏做前识别。"""
    captured = _capture(monkeypatch, target)

    assert getattr(checker, entry)(object()) is True
    expected_attempts = 10 if entry in _NAV_CONFIRM_ENTRIES else 1
    options = captured['options']
    assert options['absent'] is False
    assert options['attempts'] == expected_attempts
    assert options['interval_seconds'] == 0.5


def test_read_server_position_scans_server_rois(monkeypatch: pytest.MonkeyPatch) -> None:
    """区服定位按列表顺序逐条比对，命中即返回下标。"""
    calls: list[object] = []

    def fake_expect_ocr(_ctx: object, **options: object) -> SimpleNamespace:
        roi = options.get('roi')
        calls.append(roi)
        return SimpleNamespace(satisfied=roi is checker.SERVER_NAME_ROIS[2])

    monkeypatch.setattr(checker, 'expect_ocr', fake_expect_ocr)

    assert checker.read_server_position(object(), '昆西') == 2
    assert calls == list(checker.SERVER_NAME_ROIS[:3])


def test_read_server_index_falls_back_to_static_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OCR 定位失败时退回静态映射，换区链路不因一次识别失败中断。"""
    monkeypatch.setattr(checker, 'read_server_position', lambda _ctx, _name: None)

    assert checker.read_server_index(object(), '昆西') == checker.get_server_index('昆西')
