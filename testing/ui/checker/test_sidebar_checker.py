"""模块功能：验证侧边栏检查器的识别判定契约。

直接调用方：项目测试运行器。

直接依赖：pytest、NumPy、common.vision 结果类型和 checker.sidebar。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.application.ui.navigation.checker import calibration, sidebar
from autowsgr.application.ui.navigation.checker.sidebar import constants, recognition
from autowsgr.application.ui.navigation.checker.sidebar.friend import check_friend_page
from autowsgr.application.ui.navigation.checker.sidebar.build import check_build_page, check_dismantle_tab
from autowsgr.application.ui.navigation.checker.sidebar.friend import constants as friend_constants
from autowsgr.application.ui.navigation.checker.sidebar.intensify import check_intensify_page, check_remold_tab, check_skill_tab
from autowsgr.application.ui.navigation.checker.sidebar.friend import recognition as friend_recognition
from autowsgr.common.vision import RecognitionResult


class _Match:
    """模板匹配结果替身。"""

    def __init__(self, matched: bool) -> None:
        self.matched = matched


_SCREEN = np.zeros((4, 4, 3), dtype=np.uint8)


def _install_sidebar_recognition(
    monkeypatch: pytest.MonkeyPatch,
    visible_roi: object | None = None,
) -> None:
    """用替身接管侧边栏识别，只让指定的识别区域命中。"""
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        matched = options['roi'] is visible_roi
        # 与真实入口一致：absent 为真时，模板没命中才算满足预期。
        satisfied = (not matched) if options.get('absent') else matched
        return RecognitionResult(satisfied, [_Match(matched)], _SCREEN)

    monkeypatch.setattr(recognition, 'expect_template', expect_template)


def test_sidebar_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """侧边栏模板命中时确认侧边栏展开。"""
    _install_sidebar_recognition(monkeypatch, constants.SIDEBAR_MAIN_ROI)

    assert sidebar.check_sidebar_page(object()) is True


def test_sidebar_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """侧边栏模板未命中时不算展开。"""
    _install_sidebar_recognition(monkeypatch, constants.BUILD_SUBMENU_ROI)

    assert sidebar.check_sidebar_page(object()) is False


def test_sidebar_absent_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """后识别：模板未命中时，期望收起为真。"""
    _install_sidebar_recognition(monkeypatch, constants.BUILD_SUBMENU_ROI)

    assert sidebar.check_sidebar_page(object(), absent=True) is True


def test_build_submenu_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """建造二级菜单模板命中时确认它弹出。"""
    _install_sidebar_recognition(monkeypatch, constants.BUILD_SUBMENU_ROI)

    assert sidebar.check_build_submenu(object()) is True


def test_build_submenu_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """建造二级菜单模板未命中时不算弹出。"""
    _install_sidebar_recognition(monkeypatch, constants.SIDEBAR_MAIN_ROI)

    assert sidebar.check_build_submenu(object()) is False


def test_intensify_submenu_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """强化二级菜单模板命中时确认它弹出。"""
    _install_sidebar_recognition(monkeypatch, constants.INTENSIFY_SUBMENU_ROI)

    assert sidebar.check_intensify_submenu(object()) is True


def test_intensify_submenu_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """强化二级菜单模板未命中时不算弹出。"""
    _install_sidebar_recognition(monkeypatch, constants.SIDEBAR_MAIN_ROI)

    assert sidebar.check_intensify_submenu(object()) is False


def _install_friend_recognition(
    monkeypatch: pytest.MonkeyPatch,
    *,
    visible: bool,
) -> None:
    """用替身接管好友页面识别。"""
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        assert options['roi'] is friend_constants.FRIEND_TAB_ROI
        satisfied = (not visible) if options.get('absent') else visible
        return RecognitionResult(satisfied, [_Match(visible)], _SCREEN)

    monkeypatch.setattr(friend_recognition, 'expect_template', expect_template)


def test_friend_page_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """好友页面模板命中时确认在前台。"""
    _install_friend_recognition(monkeypatch, visible=True)

    assert check_friend_page(object()) is True


def test_friend_page_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """好友页面模板未命中时不算在前台。"""
    _install_friend_recognition(monkeypatch, visible=False)

    assert check_friend_page(object()) is False

# ── 建造页与改造页的标签 ──────────────────────────────────────────────────────


def _install_tab_recognition(
    monkeypatch: pytest.MonkeyPatch,
    visible_roi: object,
) -> None:
    """让建造页与改造页的模板识别只在给定区域命中。"""
    from autowsgr.application.ui.navigation.checker.sidebar import build, intensify

    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        matched = options['roi'] is visible_roi
        satisfied = (not matched) if options.get('absent') else matched
        return RecognitionResult(satisfied, [_Match(matched)], _SCREEN)

    for module in (build.recognition, intensify.recognition):
        monkeypatch.setattr(module, 'expect_template', expect_template)


def test_build_page_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """建造页默认落在「建造」标签，模板命中即算到达。"""
    from autowsgr.application.ui.navigation.checker.sidebar.build import constants as build_constants

    _install_tab_recognition(monkeypatch, build_constants.BUILD_TAB_ROI)

    assert check_build_page(object()) is True


def test_build_page_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """未落在建造标签时不算到达。"""
    from autowsgr.application.ui.navigation.checker.sidebar.build import constants as build_constants

    _install_tab_recognition(monkeypatch, build_constants.DISMANTLE_TAB_ROI)

    assert check_build_page(object()) is False


def test_dismantle_tab_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """解体标签激活时确认切换成功。"""
    from autowsgr.application.ui.navigation.checker.sidebar.build import constants as build_constants

    _install_tab_recognition(monkeypatch, build_constants.DISMANTLE_TAB_ROI)

    assert check_dismantle_tab(object()) is True


def test_intensify_page_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """改造页默认落在「强化」标签，模板命中即算到达。"""
    from autowsgr.application.ui.navigation.checker.sidebar.intensify import constants as intensify_constants

    _install_tab_recognition(monkeypatch, intensify_constants.INTENSIFY_TAB_ROI)

    assert check_intensify_page(object()) is True


def test_intensify_page_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """未落在强化标签时不算到达。"""
    from autowsgr.application.ui.navigation.checker.sidebar.intensify import constants as intensify_constants

    _install_tab_recognition(monkeypatch, intensify_constants.SKILL_TAB_ROI)

    assert check_intensify_page(object()) is False


def test_remold_and_skill_tabs(monkeypatch: pytest.MonkeyPatch) -> None:
    """改造与技能标签各自能被确认。"""
    from autowsgr.application.ui.navigation.checker.sidebar.intensify import constants as intensify_constants

    _install_tab_recognition(monkeypatch, intensify_constants.REMOLD_TAB_ROI)
    assert check_remold_tab(object()) is True
    assert check_skill_tab(object()) is False

    _install_tab_recognition(monkeypatch, intensify_constants.SKILL_TAB_ROI)
    assert check_skill_tab(object()) is True
    assert check_remold_tab(object()) is False

