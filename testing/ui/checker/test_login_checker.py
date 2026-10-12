"""模块功能：验证登录 checker 的入口编排与识别参数透传。

直接调用方：项目测试运行器。

直接依赖：pytest、login 的 checker 与 recognition。

边界：用替身接管识别函数，不连接设备、不识别画面。
"""

from __future__ import annotations

from typing import Any

import pytest

from autowsgr.application.ui.navigation.checker.login import checker, recognition


# 导航确认入口有自己的默认节奏（等弹层动画），其余入口保持单帧。
_NAV_CONFIRM_ENTRIES = {'check_login_page', 'check_server_select'}

_SCREEN_ENTRIES = [
    ('check_black_screen', 'read_black_screen'),
    ('check_update_prompt', 'read_update_prompt'),
    ('check_loading', 'read_loading'),
    ('check_login_page', 'read_login_page'),
    ('check_server_select', 'read_server_select'),
]


@pytest.mark.parametrize(('entry', 'target'), _SCREEN_ENTRIES)
def test_check_entry_passes_recognition_options(
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    target: str,
) -> None:
    """五个画面入口把识别模式与节奏原样传给识别层。"""
    captured: dict[str, Any] = {}

    def fake(_ctx: object, **options: object) -> bool:
        captured.update(options)
        return True

    monkeypatch.setattr(recognition, target, fake)

    result = getattr(checker, entry)(
        object(),
        absent=True,
        attempts=120,
        interval_seconds=1.0,
    )

    assert result is True
    assert captured == {'absent': True, 'attempts': 120, 'interval_seconds': 1.0}


@pytest.mark.parametrize(('entry', 'target'), _SCREEN_ENTRIES)
def test_check_entry_defaults_to_single_frame(
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    target: str,
) -> None:
    """不传参数时按各入口自己的默认节奏做前识别。"""
    captured: dict[str, Any] = {}

    def fake(_ctx: object, **options: object) -> bool:
        captured.update(options)
        return True

    monkeypatch.setattr(recognition, target, fake)

    assert getattr(checker, entry)(object()) is True
    expected_attempts = 10 if entry in _NAV_CONFIRM_ENTRIES else 1
    assert captured == {
        'absent': False,
        'attempts': expected_attempts,
        'interval_seconds': 0.5,
    }


def test_position_and_center_entries_stay_single_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """区服定位与按钮中心读取不接收识别节奏参数。"""
    monkeypatch.setattr(recognition, 'find_server_position', lambda _ctx, _name: 2)

    assert checker.find_server_position(object(), '昆西') == 2
