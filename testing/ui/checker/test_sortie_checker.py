"""模块功能：验证出征页检查器的标签激活判定契约。

直接调用方：项目测试运行器。

直接依赖：pytest、NumPy、common.vision 结果类型和 checker.sortie。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.application.ui.navigation.checker import calibration, sortie
from autowsgr.application.ui.navigation.checker.sortie import constants, recognition
from autowsgr.common.vision import RecognitionResult


class _Match:
    """模板匹配结果替身。"""

    def __init__(self, matched: bool) -> None:
        self.matched = matched


def _install_recognition(monkeypatch: pytest.MonkeyPatch, *, active_roi: object = None) -> None:
    """用替身接管识别入口：只有指定识别区域算命中。"""
    screen = np.zeros((4, 4, 3), dtype=np.uint8)
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        matched = options['roi'] is active_roi
        return RecognitionResult(matched, [_Match(matched)], screen)

    monkeypatch.setattr(recognition, 'expect_template', expect_template)


_ENTRIES = (
    (constants.SORTIE_TAB_ROI, sortie.check_sortie_page),
    (constants.EXERCISE_TAB_ROI, sortie.check_exercise_page),
    (constants.EXPEDITION_TAB_ROI, sortie.check_expedition_page),
    (constants.CAMPAIGN_TAB_ROI, sortie.check_campaign_page),
    (constants.DECISIVE_TAB_ROI, sortie.check_decisive_page),
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
