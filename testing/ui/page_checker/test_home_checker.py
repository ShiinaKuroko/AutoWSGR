"""模块功能：验证主页检查器的识别判定契约。

直接调用方：项目测试运行器。

直接依赖：pytest、NumPy、common.vision 结果类型和 page_checker.home_checker。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.application.ui.navigation.page_checker import calibration, home_checker
from autowsgr.application.ui.navigation.page_checker.home_checker import constants, recognition
from autowsgr.common.vision import RecognitionResult


class _Match:
    """模板匹配结果替身。"""

    def __init__(self, matched: bool) -> None:
        self.matched = matched


def _install_recognition(
    monkeypatch: pytest.MonkeyPatch,
    *,
    home_visible: bool = False,
    news_matches: tuple[bool, bool, bool] = (False, False, False),
    reward_matches: tuple[bool, bool] = (False, False),
    confirm_visible: bool = False,
) -> None:
    """用替身接管识别入口，按识别区域返回预设事实。"""
    screen = np.zeros((4, 4, 3), dtype=np.uint8)
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        roi = options['roi']
        if roi is constants.HOME_MAIN_ROI:
            return RecognitionResult(home_visible, [_Match(home_visible)], screen)
        if roi is constants.REWARD_CONFIRM_BUTTON_ROI:
            return RecognitionResult(confirm_visible, [_Match(confirm_visible)], screen)
        if isinstance(roi, tuple):
            flags = news_matches if len(roi) == 3 else reward_matches
            matches = [_Match(flag) for flag in flags]
            return RecognitionResult(any(flags), matches, screen)
        raise AssertionError(f'未预期的模板识别区域: {roi!r}')

    monkeypatch.setattr(recognition, 'expect_template', expect_template)


def test_home_page_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """主页模板命中时确认在主页。"""
    _install_recognition(monkeypatch, home_visible=True)

    assert home_checker.check_home_page(object()) is True


def test_home_page_hidden_by_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    """主页模板未命中时不算在主页。"""
    _install_recognition(monkeypatch)

    assert home_checker.check_home_page(object()) is False


def test_news_overlay_reads_checked_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """公告浮窗一次识别同时给出浮窗状态和已勾选状态。"""
    _install_recognition(monkeypatch, news_matches=(True, True, False))

    state = home_checker.check_home_news_overlay(object())

    assert state.matched is True
    assert state.checked is True


def test_news_overlay_reads_unchecked_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """勾选框未勾选时给出未勾选事实。"""
    _install_recognition(monkeypatch, news_matches=(True, False, True))

    state = home_checker.check_home_news_overlay(object())

    assert state.matched is True
    assert state.checked is False


def test_news_overlay_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """三个模板都没命中时公告浮窗不存在。"""
    _install_recognition(monkeypatch)

    state = home_checker.check_home_news_overlay(object())

    assert state.matched is False
    assert state.checked is None


def test_reward_overlay_matches_text_or_button(monkeypatch: pytest.MonkeyPatch) -> None:
    """奖励文字命中即算奖励浮窗存在。"""
    _install_recognition(monkeypatch, reward_matches=(True, False))

    assert home_checker.check_home_reward_overlay(object()) is True


def test_reward_overlay_absent_and_confirm_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """奖励浮窗不存在、确认浮窗存在时各自如实返回。"""
    _install_recognition(monkeypatch, confirm_visible=True)

    assert home_checker.check_home_reward_overlay(object()) is False
    assert home_checker.check_home_reward_confirm(object()) is True
