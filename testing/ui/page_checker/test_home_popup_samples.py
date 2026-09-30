"""Static homepage popup recognition smoke tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from autowsgr.application.ui.controller.home.main_page import constants
from autowsgr.application.ui.controller.home.main_page import recognition
from autowsgr.common import vision


_SAMPLE_ROOT = Path(__file__).parent / 'data' / 'home'


def _load_sample(name: str) -> np.ndarray:
    encoded = np.fromfile(str(_SAMPLE_ROOT / name), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise AssertionError(f'无法读取首页静态样本: {name}')
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('HOME_NEWS_SAMPLE_720P.png', recognition.OverlayKind.NEWS),
        ('HOME_REWARD_SAMPLE1_720P.png', recognition.OverlayKind.REWARD),
        ('HOME_REWARD_SAMPLE2_720P.png', recognition.OverlayKind.REWARD),
    ],
)
def test_home_popup_sample_recognition(name: str, expected: recognition.OverlayKind) -> None:
    """Static samples produce template results that identify the expected overlay."""
    screen = _load_sample(name)
    matches = [
        vision.match_template(
            screen,
            recognition.load_template(template),
            roi=roi,
        )
        for template, roi in (
            (recognition.NEWS_TEMPLATE, constants.NEWS_TEXT_ROI),
            (recognition.REWARD_TEMPLATE, constants.REWARD_TEXT_ROI),
            (recognition.CONFIRM_TEMPLATE, constants.REWARD_CONFIRM_BUTTON_ROI),
        )
    ]
    result = recognition.read_overlay(matches)

    assert result is expected
