"""Static homepage popup recognition smoke tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from autowsgr.application.ui.controller.home.main_page import recognition


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
    """Static debug samples must identify the expected homepage overlay."""
    result = recognition.read_overlay(_load_sample(name))

    assert result is expected
