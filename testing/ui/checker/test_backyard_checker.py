"""模块功能：验证后院检查器的识别判定契约。

直接调用方：项目测试运行器。

直接依赖：pytest、NumPy、common.vision 结果类型和 checker.backyard。

边界：用替身接管识别入口，不加载模板图片、不访问设备。
"""

from __future__ import annotations

import numpy as np
import pytest

from autowsgr.application.ui.navigation.checker import backyard, calibration
from autowsgr.application.ui.navigation.checker.backyard import (
    academy,
    bath,
    canteen,
    rank_room,
)
from autowsgr.application.ui.navigation.checker.backyard import (
    recognition as backyard_recognition,
)
from autowsgr.application.ui.navigation.checker.backyard import constants, recognition
from autowsgr.common.vision import RecognitionResult


class _Match:
    """模板匹配结果替身。"""

    def __init__(self, matched: bool) -> None:
        self.matched = matched


_SCREEN = np.zeros((4, 4, 3), dtype=np.uint8)


def _install(monkeypatch: pytest.MonkeyPatch, hit_rois: tuple[object, ...]) -> None:
    """让列出的识别区域命中，其余不命中。"""
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())

    def expect_template(_ctx: object, **options: object) -> RecognitionResult[list[object]]:
        roi = options['roi']
        regions = roi if isinstance(roi, tuple) else (roi,)
        flags = [region in hit_rois for region in regions]
        # 与真实入口一致：命中数达到 min_matches 即满足，absent 时断言相反。
        required = options.get('min_matches', 1)
        matched = sum(flags) >= required
        satisfied = (not matched) if options.get('absent') else matched
        return RecognitionResult(satisfied, [_Match(f) for f in flags], _SCREEN)

    # 后院主页与四个二级页各有自己的识别模块，替身要一起接管。
    for module in (
        backyard_recognition,
        canteen.recognition,
        academy.recognition,
        rank_room.recognition,
        bath.recognition,
    ):
        monkeypatch.setattr(module, 'expect_template', expect_template)


def test_backyard_reached_by_entry_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """入口模板命中即算到达后院主页（身份就是其中一个入口）。"""
    _install(monkeypatch, (constants.BATH_ENTRY_ROI,))

    assert backyard.check_backyard_page(object()) is True


def test_backyard_absent_when_entry_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """入口模板不在时不算在后院主页。"""
    _install(monkeypatch, ())

    assert backyard.check_backyard_page(object()) is False


def test_backyard_absent_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """后识别：入口模板不在，期待离开成立（进二级页后整页被换掉）。"""
    _install(monkeypatch, ())

    assert backyard.check_backyard_page(object(), absent=True) is True


def test_each_sub_page_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """四个二级页各自被自己的模板确认。"""
    cases = [
        (backyard.check_canteen_page, canteen.constants.PAGE_ROI),
        (backyard.check_academy_page, academy.constants.PAGE_ROI),
        (backyard.check_rank_room_page, rank_room.constants.PAGE_ROI),
        (backyard.check_bath_page, bath.constants.PAGE_ROI),
    ]
    for checker, roi in cases:
        _install(monkeypatch, (roi,))
        assert checker(object()) is True, roi
        assert checker(object(), absent=True) is False, roi


def test_sub_page_rejects_other_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """站在餐厅时，学院入口返回假。"""
    _install(monkeypatch, (canteen.constants.PAGE_ROI,))

    assert backyard.check_academy_page(object()) is False

def test_entry_center_reads_matching_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """入口模板命中时给出它的归一化中心。"""
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())
    monkeypatch.setattr(
        recognition, 'expect_template_center', lambda _ctx, **_: (0.5, 0.5)
    )

    assert backyard.read_canteen_entry_center(object()) == (0.5, 0.5)


def test_entry_center_returns_none_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """入口模板未命中时返回 None，由控制器用静态坐标兜底。"""
    monkeypatch.setattr(calibration, 'load_module_template', lambda *args, **kwargs: object())
    monkeypatch.setattr(recognition, 'expect_template_center', lambda _ctx, **_: None)

    assert backyard.read_bath_entry_center(object()) is None

