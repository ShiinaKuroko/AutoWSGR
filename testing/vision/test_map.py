"""Tests for map-counter OCR at the common vision boundary."""

from __future__ import annotations

import numpy as np

from autowsgr.common.vision import OCRResult
from autowsgr.common.vision.map import recognize_loot_count


class _UnparseableOCR:
    """Return a denominator-only OCR result."""

    def recognize_single(self, image: np.ndarray, *, allowlist: str) -> OCRResult:
        return OCRResult(text='50', confidence=1.0)


def test_unparseable_loot_count_returns_none() -> None:
    """无法解析分子时返回 None，而不是比较 None 与数字。"""
    screen = np.zeros((100, 100, 3), dtype=np.uint8)

    assert recognize_loot_count(screen, _UnparseableOCR()) is None
