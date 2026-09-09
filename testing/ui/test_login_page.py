"""登录前启动画面控制器的无设备单元测试。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from autowsgr.application.ui.controller.login import LoginPage, constants
from autowsgr.application.ui.controller.login import page as login_page


def test_check_current_page_wraps_pixel_signature_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """页面检查使用登录模块自己的签名并返回统一匹配结果。"""
    result = SimpleNamespace(matched=True, ratio=1.0)
    check_signature = MagicMock(return_value=result)
    monkeypatch.setattr(login_page.PixelChecker, 'check_signature', check_signature)
    screen = object()

    match = LoginPage.check_current_page(screen)

    check_signature.assert_called_once_with(screen, constants.PAGE_SIGNATURE)
    assert match.name == '启动画面'
    assert match.matched
    assert match.score == 1.0


def test_click_enter_uses_login_coordinate(monkeypatch: pytest.MonkeyPatch) -> None:
    """进入动作点击登录坐标并等待页面稳定。"""
    ctrl = MagicMock()
    sleep = MagicMock()
    monkeypatch.setattr(login_page.time, 'sleep', sleep)

    LoginPage(ctrl).click_enter()

    ctrl.click.assert_called_once_with(*constants.CLICK_ENTER)
    sleep.assert_called_once_with(2.0)
