"""验证登录前启动画面控制器的无设备单元测试。

上层调用：
- testing：执行登录启动画面控制器回归测试。

下层依赖：
- application.ui.controller.login：提供登录启动画面页面入口。

边界：
只验证页面识别和进入动作，不连接设备或执行登录后流程。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call

from autowsgr.application.ui.controller.login import LoginPage, constants, recognition
from autowsgr.application.ui.controller.login import page as login_page


if TYPE_CHECKING:
    import pytest


def test_check_current_page_wraps_pixel_signature_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """页面检查使用登录模块自己的签名并返回统一匹配结果。"""
    result = SimpleNamespace(matched=True, ratio=1.0)
    check_signature = MagicMock(return_value=result)
    monkeypatch.setattr(recognition.vision.PixelChecker, 'check_signature', check_signature)
    screen = object()

    match = LoginPage.check_current_page(screen)

    check_signature.assert_called_once_with(screen, constants.PAGE_SIGNATURE)
    assert match.name == '启动画面'
    assert match.matched
    assert match.score == 1.0


def test_enter_game_uses_login_coordinate(monkeypatch: pytest.MonkeyPatch) -> None:
    """进入动作点击登录坐标并等待页面稳定。"""
    ctrl = MagicMock()
    sleep = MagicMock()
    log = MagicMock()
    monkeypatch.setattr(login_page.time, 'sleep', sleep)
    monkeypatch.setattr(login_page._log, 'info', log)

    LoginPage(ctrl).enter_game()

    ctrl.click.assert_called_once_with(*constants.CLICK_ENTER)
    sleep.assert_called_once_with(2.0)
    assert log.call_args_list == [
        call('[UI] 登录画面 → 尝试进入'),
        call('[UI] 登录画面 → 进入游戏：结果=已提交'),
    ]
