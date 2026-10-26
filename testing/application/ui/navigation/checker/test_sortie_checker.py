"""模块功能：验证出征页检查器的标签激活判定契约。

直接调用方：项目测试运行器。

直接依赖：pytest、checker.sortie 与 vision 识别入口。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from autowsgr.application.ui.navigation.checker import sortie
from autowsgr.application.ui.navigation.checker.sortie import checker as sortie_checker


def _install_recognition(monkeypatch: pytest.MonkeyPatch, *, active_roi: object = None) -> None:
    """用替身接管识别入口：只有指定识别区域算命中。"""

    def expect_template(_ctx: object, **options: object) -> SimpleNamespace:
        roi = options.get('roi')
        matched = roi is active_roi
        return SimpleNamespace(
            satisfied=(not matched) if options.get('absent') else matched,
        )

    monkeypatch.setattr(sortie_checker, 'expect_template', expect_template)


_ENTRIES = (
    (sortie_checker.SORTIE_TAB_ROI, sortie.check_sortie_page),
    (sortie_checker.EXERCISE_TAB_ROI, sortie.check_exercise_page),
    (sortie_checker.EXPEDITION_TAB_ROI, sortie.check_expedition_page),
    (sortie_checker.CAMPAIGN_TAB_ROI, sortie.check_campaign_page),
    (sortie_checker.DECISIVE_TAB_ROI, sortie.check_decisive_page),
)


@pytest.mark.parametrize(('active_roi', 'entry'), _ENTRIES)
def test_only_active_tab_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    active_roi: object,
    entry: object,
) -> None:
    """只有激活标签对应的入口返回真，其余入口返回假。"""
    _install_recognition(monkeypatch, active_roi=active_roi)

    assert entry(object()) is True
    for other_roi, other_entry in _ENTRIES:
        if other_roi is active_roi:
            continue
        assert other_entry(object()) is False


def test_no_tab_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """没有任何标签激活时五个入口都返回假。"""
    _install_recognition(monkeypatch)

    for _, entry in _ENTRIES:
        assert entry(object()) is False
